from __future__ import annotations

import os
import json
from pathlib import Path
import re
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from bpm.core import agent_config
from bpm.core import agent_provider
from bpm.core import agent_recommend
from bpm.core import agent_session
from bpm.core import agent_template_index
from bpm.core import agent_methods
from bpm.core import brs_loader
from bpm.core.descriptor_loader import load as load_desc
from bpm.core.agent_config import AgentConfig

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help=(
        "Agent commands.\n\n"
        "Configure and run a BPM/BRS-scoped assistant for template discovery and guidance."
    ),
)
_console = Console()


def _render_template_context() -> str:
    try:
        entries = agent_template_index.list_templates()
    except Exception:
        entries = []
    if not entries:
        return "No active template metadata available."

    lines = []
    for e in entries[:50]:
        lines.append(f"- {e.template_id} ({e.descriptor_path})")
    return "Active BPM/BRS templates:\n" + "\n".join(lines)

def _build_system_prompt() -> str:
    return (
        "You are BPM Agent, a CLI assistant strictly scoped to BPM/BRS.\n"
        "Rules:\n"
        "1) Only answer BPM/BRS analysis, templates, render/run guidance.\n"
        "2) If out of scope, refuse briefly and redirect to BPM/BRS.\n"
        "3) Prefer concrete commands and parameter guidance.\n"
        "4) Do not claim actions were executed unless explicitly reported.\n"
    )

def _build_runtime_hint(user_text: str) -> str:
    recs = agent_recommend.recommend(goal=user_text, top_k=3)
    if not recs:
        return "No matching template recommendations."
    lines = ["Top template matches for current user turn:"]
    for r in recs:
        lines.append(f"- {r.template_id}: {r.reason} [source: {r.source_path}]")
    for r in recs[:2]:
        details = _template_detail_hint(r.template_id)
        if details:
            lines.append(details)
    try:
        p = agent_recommend.build_command_proposal(recs[0].template_id)
        lines.append(f"Suggested starter command: {p.command}")
    except Exception:
        pass
    return "\n".join(lines)


def _template_detail_hint(template_id: str) -> str:
    try:
        desc = load_desc(template_id)
    except Exception:
        return ""

    important = []
    pattern = re.compile(r"(genome|assembly|quant|spike|umi|protocol|stranded|align|salmon|star)", re.I)
    for pname, pspec in (desc.params or {}).items():
        if not pattern.search(str(pname)):
            continue
        default = getattr(pspec, "default", None)
        ptype = getattr(pspec, "type", "str")
        req = bool(getattr(pspec, "required", False))
        important.append(f"{pname}<{ptype}> default={default!r} required={str(req).lower()}")
    important = important[:8]

    run_hints = _extract_run_script_hints(template_id, desc.run_entry or "run.sh")
    out: list[str] = [f"Template detail [{template_id}]:"]
    if important:
        out.append("- Important params: " + "; ".join(important))
    if run_hints:
        out.append("- Run hints: " + " | ".join(run_hints[:6]))
    return "\n".join(out)


def _extract_run_script_hints(template_id: str, run_entry: str) -> list[str]:
    try:
        tdir = brs_loader.get_paths().templates_dir / template_id
    except Exception:
        return []

    candidates = [
        tdir / run_entry,
        tdir / f"{run_entry}.j2",
        tdir / "run.sh",
        tdir / "run.sh.j2",
    ]
    script = next((p for p in candidates if p.exists()), None)
    if script is None:
        return []

    raw = script.read_text(encoding="utf-8", errors="replace")
    hints: list[str] = []
    pattern = re.compile(r"(genome|assembly|quant|spike|umi|protocol|stranded|align|salmon|star)", re.I)
    for ln in raw.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if not pattern.search(s):
            continue
        s = re.sub(r"\s+", " ", s)
        hints.append(s[:180])
    return hints[:12]

def _trim_history(messages: list[dict[str, str]], max_messages: int = 20) -> list[dict[str, str]]:
    if len(messages) <= max_messages:
        return messages
    # Keep the first system message and the latest conversation turns.
    head = messages[:1] if messages and messages[0].get("role") == "system" else []
    tail = messages[-(max_messages - len(head)) :]
    return head + tail


def _print_chat_header(provider: str, model: str) -> None:
    title = Text("BPM Agent Chat", style="bold cyan")
    body = (
        f"Provider: [bold]{provider}[/bold]\n"
        f"Model: [bold]{model}[/bold]\n\n"
        "Commands:\n"
        "  [bold]/help[/bold]       Show command help\n"
        "  [bold]/templates[/bold]  List active template ids\n"
        "  [bold]/recommend X[/bold]  Recommend templates for query X\n"
        "  [bold]exit[/bold] or [bold]quit[/bold]  End session"
    )
    _console.print(Panel.fit(body, title=title, border_style="cyan"))


def _print_agent_message(reply: str) -> None:
    rendered = Markdown(reply, code_theme="monokai", hyperlinks=False)
    _console.print(Panel(rendered, title="agent", border_style="green"))


def _print_user_message(text: str) -> None:
    _console.print(f"[bold cyan]you>[/bold cyan] {text}")


def _handle_chat_command(user_text: str) -> str | None:
    t = user_text.strip()
    if t == "/help":
        _console.print(
            Panel.fit(
                "Commands:\n"
                "  /help\n"
                "  /templates\n"
                "  /recommend <query>\n"
                "  exit | quit",
                title="Help",
                border_style="blue",
            )
        )
        return "handled"
    if t == "/templates":
        try:
            entries = agent_template_index.list_templates()
        except Exception as e:
            _console.print(f"[red]template lookup failed:[/red] {e}")
            return "handled"
        if not entries:
            _console.print("No active templates.")
            return "handled"
        preview = "\n".join([f"- {e.template_id}" for e in entries[:30]])
        _console.print(Panel(preview, title="Templates", border_style="blue"))
        return "handled"
    if t.startswith("/recommend "):
        query = t[len("/recommend ") :].strip()
        recs = agent_recommend.recommend(goal=query, top_k=3)
        if not recs:
            _console.print("No matches.")
            return "handled"
        lines = []
        for r in recs:
            conf = "high" if r.score >= 3 else ("medium" if r.score == 2 else "low")
            lines.append(f"- {r.template_id} ({conf}): {r.reason}")
        _console.print(Panel("\n".join(lines), title=f"Recommendations: {query}", border_style="blue"))
        return "handled"
    return None


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

@app.command("methods")
def methods_cmd(
    project_dir: str = typer.Option(".", "--dir", help="Project directory containing project.yaml"),
    style: str = typer.Option("full", "--style", help="Output style: full|concise"),
    out: str | None = typer.Option(None, "--out", help="Write output markdown to a file path"),
):
    """
    Generate a publication-oriented methods draft from project history.
    """
    try:
        result = agent_methods.generate_methods_markdown(Path(project_dir), style=style)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if out:
        out_path = Path(out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result.markdown, encoding="utf-8")
        typer.secho(
            f"[ok] Methods draft written: {out_path} "
            f"(templates={result.templates_count}, citations={result.citation_count})",
            fg=typer.colors.GREEN,
        )
        return

    typer.echo(result.markdown)


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
    analysis_type: str = typer.Option("", "--analysis-type", help="Optional analysis type hint"),
    input_path: str = typer.Option("", "--input-path", help="Optional input path hint"),
    platform: str = typer.Option("", "--platform", help="Optional platform hint"),
    output_goal: str = typer.Option("", "--output-goal", help="Optional output goal hint"),
    compute_mode: str = typer.Option("", "--compute-mode", help="Optional compute mode hint"),
    chat: bool = typer.Option(True, "--chat/--no-chat", help="Enable LLM chat mode (default: on)"),
    non_interactive: bool = typer.Option(
        False, "--non-interactive", help="Print recommendations and proposal without confirmation prompt"
    ),
):
    """
    Start BPM/BRS-scoped assistant.
    """
    typer.secho("BPM Agent scope: BPM/BRS analysis support only.", fg=typer.colors.CYAN)
    typer.secho("Hello, I am BPM Agent. I can help with BPM/BRS analysis planning and template selection.", fg=typer.colors.CYAN)
    session_file = agent_session.new_session_file(prefix="start")
    agent_session.append_event(
        session_file,
        {
            "event": "start_begin",
            "goal_provided": bool(goal),
            "non_interactive": non_interactive,
            "hints": {
                "analysis_type": analysis_type,
                "input_path": input_path,
                "platform": platform,
                "output_goal": output_goal,
                "compute_mode": compute_mode,
            },
        },
    )

    # Interactive LLM chat mode (default)
    if chat and (not non_interactive):
        try:
            cfg = agent_config.load_config()
            agent_config.validate_config(cfg)
        except Exception as e:
            typer.secho(f"Error: agent provider not configured: {e}", err=True, fg=typer.colors.RED)
            typer.echo("Run: bpm agent config")
            agent_session.append_event(session_file, {"event": "start_error", "stage": "config", "error": str(e)})
            raise typer.Exit(code=1)

        health = agent_provider.healthcheck(cfg)
        if not health.ok:
            typer.secho(f"Error: provider check failed: {health.message}", err=True, fg=typer.colors.RED)
            agent_session.append_event(
                session_file, {"event": "start_error", "stage": "provider_health", "error": health.message}
            )
            raise typer.Exit(code=1)

        model_check = agent_provider.check_model_available(cfg)
        if not model_check.ok:
            typer.secho(f"Error: model unavailable: {model_check.message}", err=True, fg=typer.colors.RED)
            agent_session.append_event(
                session_file, {"event": "start_error", "stage": "model_check", "error": model_check.message}
            )
            raise typer.Exit(code=1)

        _print_chat_header(cfg.provider, cfg.model)
        typer.echo("")

        messages: list[dict[str, str]] = [
            {"role": "system", "content": _build_system_prompt()},
            {"role": "system", "content": _render_template_context()},
        ]
        pending = goal.strip() if goal else ""

        while True:
            if pending:
                user_text = pending
                pending = ""
                _print_user_message(user_text)
            else:
                user_text = typer.prompt("you").strip()

            if user_text.lower() in ("exit", "quit", "/exit", "/quit"):
                agent_session.append_event(session_file, {"event": "start_end", "decision": "quit"})
                typer.echo("Session ended.")
                return
            if _handle_chat_command(user_text):
                continue

            runtime_hint = _build_runtime_hint(user_text)
            request_messages = list(messages)
            request_messages.append({"role": "system", "content": runtime_hint})
            request_messages.append({"role": "user", "content": user_text})

            agent_session.append_event(session_file, {"event": "chat_user", "text": user_text})
            try:
                resp = agent_provider.chat(cfg, request_messages)
                reply = resp.text
            except Exception as e:
                msg = str(e)
                typer.secho(f"agent error: {msg}", fg=typer.colors.RED)
                agent_session.append_event(session_file, {"event": "chat_error", "error": msg})
                continue

            _print_agent_message(reply)
            agent_session.append_event(session_file, {"event": "chat_assistant", "text": reply})

            messages.append({"role": "user", "content": user_text})
            messages.append({"role": "assistant", "content": reply})
            messages = _trim_history(messages, max_messages=20)

    # Recommendation-only mode
    if not goal:
        goal = typer.prompt("What analysis do you need?")

    intent = agent_recommend.Intent(
        goal=goal,
        analysis_type=analysis_type,
        input_path=input_path,
        platform=platform,
        output_goal=output_goal,
        compute_mode=compute_mode,
    )

    try:
        recs = agent_recommend.recommend_from_intent(intent=intent, top_k=3)

        # Adaptive questioning: ask only when recommendation is ambiguous.
        asked: list[str] = []
        if (not non_interactive) and agent_recommend.is_ambiguous(recs):
            if not intent.analysis_type:
                intent = agent_recommend.Intent(
                    goal=intent.goal,
                    analysis_type=typer.prompt("Analysis type (optional; enter to skip)", default=""),
                    input_path=intent.input_path,
                    platform=intent.platform,
                    output_goal=intent.output_goal,
                    compute_mode=intent.compute_mode,
                )
                asked.append("analysis_type")
                recs = agent_recommend.recommend_from_intent(intent=intent, top_k=3)

        if (not non_interactive) and agent_recommend.is_ambiguous(recs):
            if not intent.input_path:
                intent = agent_recommend.Intent(
                    goal=intent.goal,
                    analysis_type=intent.analysis_type,
                    input_path=typer.prompt("Input path hint (optional; enter to skip)", default=""),
                    platform=intent.platform,
                    output_goal=intent.output_goal,
                    compute_mode=intent.compute_mode,
                )
                asked.append("input_path")
                recs = agent_recommend.recommend_from_intent(intent=intent, top_k=3)

        agent_session.append_event(
            session_file,
            {
                "event": "start_recommendations",
                "goal": intent.goal,
                "asked_questions": asked,
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
