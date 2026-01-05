from __future__ import annotations
from pathlib import Path
from shutil import which
import typer

from bpm.core import workflow_service as svc
from bpm.core import brs_loader

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help=(
        "Workflow commands.\n\n"
        "Run workflows from the active BRS. Workflows execute an entry script and"
        " can optionally record run history in project.yaml."
    ),
)


# Dynamic completion for workflow ids
def _complete_workflow_ids(ctx, incomplete: str):
    try:
        p = brs_loader.get_paths().workflows_dir
        ids = [d.name for d in p.iterdir() if d.is_dir()]
    except Exception:
        ids = []
    return [i for i in ids if i.startswith(incomplete)]


def _warn_missing_tools(workflow_id: str) -> None:
    try:
        desc = svc.load_descriptor(workflow_id)
    except Exception:
        return
    missing_req = [t for t in (desc.tools_required or []) if which(t) is None]
    missing_opt = [t for t in (desc.tools_optional or []) if which(t) is None]
    if not missing_req and not missing_opt:
        return
    parts = []
    if missing_req:
        parts.append(f"required: {', '.join(missing_req)}")
    if missing_opt:
        parts.append(f"optional: {', '.join(missing_opt)}")
    typer.secho(
        "Warning: tools not found on PATH (" + "; ".join(parts) + ").",
        fg=typer.colors.YELLOW,
    )


@app.command(
    "run",
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)
def run(
    ctx: typer.Context,
    workflow_id: str = typer.Argument(..., help="Workflow id within the active BRS", autocompletion=_complete_workflow_ids),
    project: Path | None = typer.Option(None, "--project", help="Path to project.yaml (optional)"),
    project_dir: Path | None = typer.Option(None, "--dir", help="Project directory (deprecated)"),
):
    """
    Execute the workflow's entry script.
    """
    def _parse_workflow_flags(extra_args: list[str]) -> list[str]:
        try:
            desc = svc.load_descriptor(workflow_id)
        except Exception:
            return []
        flag_map = {}
        for k, ps in (desc.params or {}).items():
            cli_flag = getattr(ps, "cli", None)
            if not cli_flag:
                continue
            flag_map[str(cli_flag)] = (k, str(getattr(ps, "type", "str")))
        out_params: dict[str, str] = {}
        i = 0
        n = len(extra_args or [])
        while i < n:
            arg = extra_args[i]
            if not arg.startswith("--"):
                i += 1
                continue
            if arg.startswith("--no-"):
                base = "--" + arg[5:]
                if base in flag_map and flag_map[base][1] == "bool":
                    pname, _ = flag_map[base]
                    out_params[pname] = "false"
                    i += 1
                    continue
            if "=" in arg:
                flag, value = arg.split("=", 1)
                if flag in flag_map:
                    pname, _ = flag_map[flag]
                    out_params[pname] = value
                    i += 1
                    continue
            if arg in flag_map:
                pname, ptype = flag_map[arg]
                if ptype == "bool":
                    val = "true"
                    if i + 1 < n and not extra_args[i + 1].startswith("-"):
                        nxt = extra_args[i + 1].strip().lower()
                        if nxt in ("true", "false", "1", "0", "yes", "no", "on", "off"):
                            val = nxt
                            i += 1
                    out_params[pname] = val
                    i += 1
                    continue
                if i + 1 < n and not extra_args[i + 1].startswith("-"):
                    out_params[pname] = extra_args[i + 1]
                    i += 2
                    continue
                i += 1
                continue
            i += 1
        return [f"{k}={v}" for k, v in out_params.items()]

    try:
        if project and project_dir:
            raise ValueError("Use either --project or --dir, not both.")
        project_path = project
        if project_path is None and project_dir is not None:
            project_path = (project_dir / "project.yaml").resolve()
        merged_params = _parse_workflow_flags(list(ctx.args or []))
        _warn_missing_tools(workflow_id)
        svc.run(workflow_id, project_path=project_path, params_kv=merged_params)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho("[ok] Workflow run completed.", fg=typer.colors.GREEN)


@app.command("info")
def info_cmd(
    workflow_id: str = typer.Argument(..., help="Workflow id within the active BRS", autocompletion=_complete_workflow_ids),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table (default), plain, or json",
        show_default=True,
    ),
):
    """
    Show detailed information for a workflow: params, run entry/args/env, hooks, and tools.
    """
    try:
        desc = svc.load_descriptor(workflow_id)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    params_list = []
    for k, ps in (desc.params or {}).items():
        params_list.append(
            {
                "name": k,
                "type": getattr(ps, "type", "str"),
                "required": bool(getattr(ps, "required", False)),
                "default": getattr(ps, "default", None),
                "cli": getattr(ps, "cli", None),
                "description": getattr(ps, "description", None),
            }
        )

    hooks_map = desc.hooks or {}
    tools_req = list(getattr(desc, "tools_required", []) or [])
    tools_opt = list(getattr(desc, "tools_optional", []) or [])

    fmt = (format or "table").lower()
    if fmt == "json":
        import json

        payload = {
            "id": desc.id,
            "description": desc.description,
            "run_entry": desc.run_entry or "run.sh",
            "run_args": desc.run_args or [],
            "run_env": desc.run_env or {},
            "params": params_list,
            "hooks": hooks_map,
            "tools": {
                "required": tools_req,
                "optional": tools_opt,
            },
        }
        typer.echo(json.dumps(payload, indent=2))
        return

    if fmt == "table":
        try:
            from rich.console import Console
            from rich.table import Table
            from rich import box
        except Exception:
            fmt = "plain"
        else:
            console = Console()
            t1 = Table(title=f"Workflow: {desc.id}", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
            t1.add_column("Field", style="bold", no_wrap=True)
            t1.add_column("Value")
            t1.add_row("Description", str(desc.description or ""))
            t1.add_row("Run Entry", str(desc.run_entry or "run.sh"))
            t1.add_row("Run Args", " ".join(desc.run_args) if desc.run_args else "-")
            t1.add_row("Run Env", ", ".join(desc.run_env.keys()) if desc.run_env else "-")
            console.print(t1)

            t2 = Table(title="Parameters", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
            t2.add_column("Name", style="cyan", no_wrap=True)
            t2.add_column("Type", width=8)
            t2.add_column("Required", width=9)
            t2.add_column("Default")
            t2.add_column("CLI")
            t2.add_column("Description")
            if params_list:
                for p in params_list:
                    dval = p.get("default")
                    if isinstance(dval, bool):
                        dstr = "true" if dval else "false"
                    else:
                        dstr = "" if dval is None else str(dval)
                    t2.add_row(
                        str(p.get("name")),
                        str(p.get("type")),
                        "yes" if p.get("required") else "no",
                        dstr,
                        str(p.get("cli") or ""),
                        str(p.get("description") or ""),
                    )
            console.print(t2)

            t3 = Table(title="Hooks", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
            t3.add_column("Stage", style="bold")
            t3.add_column("Callables")
            for stage in ("pre_run", "post_run"):
                entries = hooks_map.get(stage) or []
                t3.add_row(stage, "\n".join(map(str, entries)) if entries else "-")
            console.print(t3)

            t4 = Table(title="Tools", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
            t4.add_column("Required")
            t4.add_column("Optional")
            t4.add_row(
                ", ".join(tools_req) if tools_req else "-",
                ", ".join(tools_opt) if tools_opt else "-",
            )
            console.print(t4)
            return

    typer.echo(f"id: {desc.id}")
    typer.echo(f"description: {desc.description}")
    typer.echo(f"run_entry: {desc.run_entry or 'run.sh'}")
    typer.echo("run_args:")
    for a in desc.run_args or []:
        typer.echo(f"  - {a}")
    typer.echo("run_env:")
    for k, v in (desc.run_env or {}).items():
        typer.echo(f"  - {k}: {v}")
    typer.echo("params:")
    for p in params_list:
        dval = p.get("default")
        if isinstance(dval, bool):
            dstr = "true" if dval else "false"
        else:
            dstr = "" if dval is None else str(dval)
        typer.echo(
            f"  - {p['name']} (type={p['type']}, required={'yes' if p['required'] else 'no'}, default={dstr}, cli={p['cli']})"
        )
    typer.echo("hooks:")
    for stage, entries in (hooks_map or {}).items():
        typer.echo(f"  {stage}:")
        for h in entries or []:
            typer.echo(f"    - {h}")
    typer.echo("tools:")
    if tools_req:
        typer.echo("  required:")
        for t in tools_req:
            typer.echo(f"    - {t}")
    if tools_opt:
        typer.echo("  optional:")
        for t in tools_opt:
            typer.echo(f"    - {t}")


@app.command("list")
def list_workflows(
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table (default), plain, or json",
        show_default=True,
    ),
):
    """
    Show all available workflows in the active BRS.
    """
    try:
        wdir = brs_loader.get_paths().workflows_dir
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    items = []
    if wdir.exists():
        for d in sorted([p for p in wdir.iterdir() if p.is_dir()]):
            wid = d.name
            try:
                desc = svc.load_descriptor(wid)
                items.append({"id": desc.id, "description": desc.description or ""})
            except Exception:
                continue

    if not items:
        typer.echo("(no workflows)")
        raise typer.Exit(code=0)

    fmt = (format or "table").lower()
    if fmt == "json":
        import json

        typer.echo(json.dumps(items, indent=2))
        return

    if fmt == "table":
        try:
            from rich.console import Console
            from rich.table import Table
            from rich import box
        except Exception:
            fmt = "plain"
        else:
            table = Table(
                title="Workflows (Active BRS)",
                box=box.MINIMAL_DOUBLE_HEAD,
                header_style="bold cyan",
                row_styles=["", "dim"],
            )
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Description", overflow="fold")
            for it in items:
                table.add_row(str(it["id"]), str(it.get("description", "")))
            Console().print(table)
            return

    for it in items:
        wid = it["id"]
        desc = it.get("description", "")
        if desc:
            typer.echo(f"{wid} - {desc}")
        else:
            typer.echo(wid)
