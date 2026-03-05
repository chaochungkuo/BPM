from __future__ import annotations

import os
import json
import typer

from bpm.core import agent_config
from bpm.core import agent_provider
from bpm.core import agent_recommend
from bpm.core import agent_session
from bpm.core import agent_template_index
from bpm.core.agent_config import AgentConfig

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help=(
        "Agent commands.\n\n"
        "Configure and run a BPM/BRS-scoped assistant for template discovery and guidance."
    ),
)


@app.command("history")
def history_cmd(
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of sessions to show"),
    kind: str = typer.Option("all", "--kind", help="Filter by session kind: all|start|doctor"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table|json"),
):
    """
    Show recent agent session transcripts.
    """
    kind_norm = (kind or "all").strip().lower()
    if kind_norm not in ("all", "start", "doctor"):
        typer.secho(f"Error: invalid kind '{kind}'. Use all|start|doctor.", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    prefix = None if kind_norm == "all" else kind_norm
    files = agent_session.list_session_files(prefix=prefix, limit=limit)
    rows = [agent_session.summarize_session(p) for p in files]

    if (format or "table").lower() == "json":
        typer.echo(json.dumps(rows, indent=2))
        return

    if not rows:
        typer.echo("No agent sessions found.")
        return

    typer.echo("Recent agent sessions:")
    for i, row in enumerate(rows, start=1):
        status = "ok" if row.get("ok") is True else ("fail" if row.get("ok") is False else "-")
        decision = row.get("decision") or "-"
        typer.echo(
            f"{i:>2}. kind={row.get('kind')} status={status} events={row.get('event_count')} "
            f"decision={decision} file={row.get('file')}"
        )


@app.command("config")
def config_cmd(
    non_interactive: bool = typer.Option(False, "--non-interactive", help="Fail instead of prompting for values"),
):
    """
    Configure BPM agent provider settings.
    """
    providers = ["openai", "anthropic", "azure_openai", "openai_compatible"]

    try:
        current = agent_config.load_config()
    except Exception:
        base, token_var, model = agent_config.defaults_for_provider("openai")
        current = AgentConfig(
            version=1,
            provider="openai",
            base_url=base,
            model=model,
            timeout_seconds=60,
            max_tokens=2000,
            temperature=0.1,
            token_source="env",
            token_env_var=token_var,
        )

    if non_interactive:
        agent_config.validate_config(current)
        p = agent_config.save_config(current)
        typer.secho(f"[ok] Config saved: {p}", fg=typer.colors.GREEN)
        return

    provider = typer.prompt("Provider", default=current.provider)
    if provider not in providers:
        typer.secho(f"Error: invalid provider '{provider}'", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    base_default, token_default, model_default = agent_config.defaults_for_provider(provider)

    base_url = typer.prompt("Base URL", default=current.base_url if current.provider == provider else base_default)
    model = typer.prompt("Model", default=current.model if current.provider == provider else model_default)
    token_source = typer.prompt(
        "Token source (env|keychain|none)",
        default=current.token_source if current.provider == provider else ("none" if provider == "openai_compatible" else "env"),
    )
    if token_source not in ("env", "keychain", "none"):
        typer.secho(f"Error: invalid token source '{token_source}'", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    token_env_var = current.token_env_var if current.provider == provider else token_default
    if token_source == "env":
        token_env_var = typer.prompt("Token environment variable", default=token_env_var or "OPENAI_API_KEY")
    if token_source == "none":
        token_env_var = ""

    timeout_seconds = typer.prompt("Timeout (seconds)", default=str(current.timeout_seconds))
    max_tokens = typer.prompt("Max tokens", default=str(current.max_tokens))
    temperature = typer.prompt("Temperature", default=str(current.temperature))

    cfg = AgentConfig(
        version=1,
        provider=provider,
        base_url=base_url,
        model=model,
        timeout_seconds=int(timeout_seconds),
        max_tokens=int(max_tokens),
        temperature=float(temperature),
        token_source=token_source,
        token_env_var=token_env_var,
    )

    try:
        agent_config.validate_config(cfg)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    path = agent_config.save_config(cfg)
    typer.secho(f"[ok] Config saved: {path}", fg=typer.colors.GREEN)


@app.command("doctor")
def doctor_cmd(verbose: bool = typer.Option(False, "--verbose", help="Show extra diagnostic detail")):
    """
    Validate agent readiness: config, token env, provider endpoint, and active BRS templates.
    """
    failed = False
    session_file = agent_session.new_session_file(prefix="doctor")
    agent_session.append_event(session_file, {"event": "doctor_start", "verbose": verbose})

    try:
        cfg = agent_config.load_config()
        typer.secho("[ok] Config loaded", fg=typer.colors.GREEN)
        agent_session.append_event(
            session_file,
            {
                "event": "doctor_config_loaded",
                "provider": cfg.provider,
                "base_url": cfg.base_url,
                "model": cfg.model,
            },
        )
    except Exception as e:
        typer.secho(f"[fail] Config: {e}", fg=typer.colors.RED)
        agent_session.append_event(session_file, {"event": "doctor_failed", "stage": "config", "error": str(e)})
        raise typer.Exit(code=1)

    if cfg.token_source == "env":
        token = os.environ.get(cfg.token_env_var)
        if token:
            typer.secho(f"[ok] Token env found: {cfg.token_env_var}", fg=typer.colors.GREEN)
        else:
            typer.secho(f"[fail] Missing token env: {cfg.token_env_var}", fg=typer.colors.RED)
            agent_session.append_event(
                session_file, {"event": "doctor_failed", "stage": "token_env", "name": cfg.token_env_var}
            )
            failed = True
    elif cfg.token_source == "none":
        typer.secho("[ok] Token not required (token_source=none)", fg=typer.colors.GREEN)
    else:
        typer.secho("[warn] keychain token source not implemented yet", fg=typer.colors.YELLOW)

    health = agent_provider.healthcheck(cfg)
    if health.ok:
        typer.secho(f"[ok] Provider endpoint: {health.message}", fg=typer.colors.GREEN)
        agent_session.append_event(session_file, {"event": "doctor_endpoint_ok", "message": health.message})
        model_check = agent_provider.check_model_available(cfg)
        if model_check.ok:
            typer.secho(f"[ok] Model check: {model_check.message}", fg=typer.colors.GREEN)
            agent_session.append_event(session_file, {"event": "doctor_model_ok", "message": model_check.message})
        else:
            typer.secho(f"[fail] Model check: {model_check.message}", fg=typer.colors.RED)
            agent_session.append_event(
                session_file, {"event": "doctor_failed", "stage": "model_check", "error": model_check.message}
            )
            failed = True
        if verbose and model_check.available_models:
            typer.echo("  models:")
            for m in model_check.available_models[:20]:
                typer.echo(f"  - {m}")
    else:
        typer.secho(f"[fail] Provider endpoint: {health.message}", fg=typer.colors.RED)
        agent_session.append_event(session_file, {"event": "doctor_failed", "stage": "endpoint", "error": health.message})
        failed = True

    try:
        templates = agent_template_index.list_templates()
        if templates:
            typer.secho(f"[ok] Active BRS templates discovered: {len(templates)}", fg=typer.colors.GREEN)
            agent_session.append_event(
                session_file, {"event": "doctor_templates_ok", "count": len(templates)}
            )
            if verbose:
                for t in templates[:10]:
                    typer.echo(f"  - {t.template_id} ({t.descriptor_path})")
        else:
            typer.secho("[fail] No templates found in active BRS", fg=typer.colors.RED)
            agent_session.append_event(session_file, {"event": "doctor_failed", "stage": "templates", "count": 0})
            failed = True
    except Exception as e:
        typer.secho(f"[fail] Template index: {e}", fg=typer.colors.RED)
        agent_session.append_event(session_file, {"event": "doctor_failed", "stage": "template_index", "error": str(e)})
        failed = True

    if failed:
        agent_session.append_event(session_file, {"event": "doctor_end", "ok": False})
        raise typer.Exit(code=1)
    agent_session.append_event(session_file, {"event": "doctor_end", "ok": True})


@app.command("start")
def start_cmd(
    goal: str = typer.Option("", "--goal", help="Optional analysis goal for non-interactive recommendation"),
    non_interactive: bool = typer.Option(
        False, "--non-interactive", help="Print recommendations and proposal without confirmation prompt"
    ),
):
    """
    Start BPM/BRS-scoped assistant (recommendation-only in this version).
    """
    typer.secho("BPM Agent scope: BPM/BRS analysis support only.", fg=typer.colors.CYAN)
    session_file = agent_session.new_session_file(prefix="start")
    agent_session.append_event(
        session_file,
        {"event": "start_begin", "goal_provided": bool(goal), "non_interactive": non_interactive},
    )

    if not goal:
        goal = typer.prompt("What analysis do you need?")

    try:
        recs = agent_recommend.recommend(goal=goal, top_k=3)
        agent_session.append_event(
            session_file,
            {
                "event": "start_recommendations",
                "goal": goal,
                "template_ids": [r.template_id for r in recs],
            },
        )
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        agent_session.append_event(session_file, {"event": "start_error", "error": str(e)})
        raise typer.Exit(code=1)

    if not recs:
        typer.secho("No matching templates found in the active BRS.", fg=typer.colors.YELLOW)
        agent_session.append_event(session_file, {"event": "start_no_matches", "goal": goal})
        raise typer.Exit(code=1)

    typer.echo("\nTop template recommendations:")
    for i, r in enumerate(recs, start=1):
        conf = "high" if r.score >= 3 else ("medium" if r.score == 2 else "low")
        typer.echo(f"{i}. {r.template_id} (confidence: {conf})")
        typer.echo(f"   why: {r.reason}")
        typer.echo(f"   source: {r.source_path}")

    top = recs[0]
    try:
        proposal = agent_recommend.build_command_proposal(top.template_id)
        agent_session.append_event(
            session_file,
            {
                "event": "start_proposal",
                "template_id": proposal.template_id,
                "command": proposal.command,
                "required_params": proposal.required_params,
            },
        )
    except Exception as e:
        typer.secho(f"Warning: could not build command proposal: {e}", fg=typer.colors.YELLOW)
        agent_session.append_event(session_file, {"event": "start_warning", "warning": str(e)})
        raise typer.Exit(code=0)

    typer.echo("\nProposed command:")
    typer.echo(f"  {proposal.command}")
    if proposal.required_params:
        typer.echo("Required parameters to fill:")
        for p in proposal.required_params:
            typer.echo(f"  - {p}")

    if non_interactive:
        typer.echo("\nNote: execution is disabled in this version (proposal only).")
        agent_session.append_event(session_file, {"event": "start_end", "decision": "non_interactive"})
        return

    decision = typer.prompt("Proceed? (yes/no/edit)", default="no").strip().lower()
    agent_session.append_event(session_file, {"event": "start_decision", "decision": decision})
    if decision == "yes":
        typer.secho("Execution is disabled in this version. Proposal generated only.", fg=typer.colors.YELLOW)
        agent_session.append_event(session_file, {"event": "start_end", "decision": "yes_disabled"})
        return
    if decision == "edit":
        edited = typer.prompt("Edit command", default=proposal.command)
        typer.echo("\nEdited command:")
        typer.echo(f"  {edited}")
        typer.secho("Execution is disabled in this version. Proposal generated only.", fg=typer.colors.YELLOW)
        agent_session.append_event(session_file, {"event": "start_end", "decision": "edit", "edited_command": edited})
        return

    typer.echo("Cancelled.")
    agent_session.append_event(session_file, {"event": "start_end", "decision": "no"})
