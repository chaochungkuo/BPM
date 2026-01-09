from __future__ import annotations
from pathlib import Path
import typer

from bpm.core import template_service as svc
from bpm.core import brs_loader
from bpm.core.descriptor_loader import load as load_desc

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help=(
        "Template commands.\n\n"
        "Render templates (with param precedence: defaults < project < CLI),\n"
        "run entries with hooks, and publish via resolvers."
    ),
)


# Dynamic completion for template ids
def _complete_template_ids(ctx, incomplete: str):
    try:
        p = brs_loader.get_paths().templates_dir
        ids = [d.name for d in p.iterdir() if d.is_dir()]
    except Exception:
        ids = []
    return [i for i in ids if i.startswith(incomplete)]


@app.command(
    "render",
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)
def render(
    ctx: typer.Context,
    template_id: str = typer.Argument(..., help="Template id within the active BRS", autocompletion=_complete_template_ids),
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
    alias: str = typer.Option(None, "--alias", help="Instance name to render under (stored as template id in project.yaml)"),
    dry: bool = typer.Option(False, "--dry", help="Dry-run: only show plan, no changes"),
    param: list[str] = typer.Option(None, "--param", help="KEY=VALUE (can repeat)"),
    out: Path = typer.Option(None, "--out", help="Ad-hoc output directory (do not touch project.yaml)"),
    allow_outside_cwd: bool = typer.Option(False, "--allow-outside-cwd/--no-allow-outside-cwd", help="Bypass cwd==--dir safety check (advanced)"),
):
    """
    Render a template into the project (or to --out in ad‑hoc mode).

    Notes:
    - Param precedence: descriptor defaults < stored project params < CLI --param
    - Ad‑hoc (with --out): skips hooks and project.yaml updates; writes bpm.meta.yaml
    """
    # Safety: in project mode, encourage running from the project directory to avoid confusion
    if not out:
        if project_dir.resolve() != Path(".").resolve():
            if not allow_outside_cwd:
                # Backward-compatible: warn but continue to support --dir workflows and tests
                typer.secho(
                    "Warning: running from outside the project directory; consider 'cd' into it or pass --allow-outside-cwd to silence this warning.",
                    err=True,
                    fg=typer.colors.YELLOW,
                )

    # Support template-defined CLI flags by mapping them into --param KEY=VALUE
    # Example: if a param declares cli: "--bcl", users can pass "--bcl /path" or "--bcl=/path".
    # Bool params: "--flag" -> true, "--no-flag" -> false.
    def _parse_template_flags(extra_args: list[str]) -> list[str]:
        try:
            desc = load_desc(template_id)
        except Exception:
            return []
        # Build flag map
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
            # Handle --no-flag for bools
            if arg.startswith("--no-"):
                base = "--" + arg[5:]
                if base in flag_map and flag_map[base][1] == "bool":
                    pname, _ = flag_map[base]
                    out_params[pname] = "false"
                    i += 1
                    continue
            # Handle --flag=value
            if "=" in arg:
                flag, value = arg.split("=", 1)
                if flag in flag_map:
                    pname, ptype = flag_map[flag]
                    out_params[pname] = value
                    i += 1
                    continue
            # Handle --flag [value]
            if arg in flag_map:
                pname, ptype = flag_map[arg]
                if ptype == "bool":
                    # Support forms:
                    #   --flag            -> true
                    #   --flag true/false -> parsed boolean (consume next token)
                    val = "true"
                    if i + 1 < n and not extra_args[i + 1].startswith("-"):
                        nxt = extra_args[i + 1].strip().lower()
                        if nxt in ("true", "false", "1", "0", "yes", "no", "on", "off"):
                            val = nxt
                            i += 1  # consume next as value
                    out_params[pname] = val
                    i += 1
                    continue
                # need a value from next token for non-bool
                if i + 1 < n and not extra_args[i + 1].startswith("-"):
                    out_params[pname] = extra_args[i + 1]
                    i += 2
                    continue
                else:
                    # missing value; ignore and move on
                    i += 1
                    continue
            # Unknown flag: ignore here; Typer ignored it already due to context settings
            i += 1
        # Convert to KEY=VALUE list
        return [f"{k}={v}" for k, v in out_params.items()]

    # Best-effort environment/tools availability warning (non-fatal)
    def _warn_missing_tools(tpl_id: str) -> None:
        try:
            desc = load_desc(tpl_id)
        except Exception:
            return
        try:
            from shutil import which
        except Exception:
            return
        missing_req = [t for t in (desc.tools_required or []) if which(t) is None]
        missing_opt = [t for t in (desc.tools_optional or []) if which(t) is None]
        if missing_req or missing_opt:
            parts = []
            if missing_req:
                parts.append(f"required: {', '.join(missing_req)}")
            if missing_opt:
                parts.append(f"optional: {', '.join(missing_opt)}")
            typer.secho(
                "Warning: tools not found on PATH (" + "; ".join(parts) + ").\n"
                "         BPM doesn’t manage environments; install/activate the right env before 'bpm template run'.",
                err=True,
                fg=typer.colors.YELLOW,
            )

    try:
        # Merge explicit --param with mapped template flags
        extra_params = _parse_template_flags(list(ctx.args or []))
        merged_params = (param or []) + extra_params
        # Emit non-fatal warnings about missing tools up-front
        _warn_missing_tools(template_id)
        plan = svc.render(
            project_dir.resolve(),
            template_id,
            alias=alias,
            params_kv=merged_params,
            dry=dry,
            adhoc_out=out.resolve() if out else None,
        )
    except Exception as e:
        # Provide a helpful hint for ad-hoc rendering when project.yaml is missing
        msg = str(e)
        if (isinstance(e, FileNotFoundError) or "project.yaml not found" in msg) and not out:
            typer.secho(
                "Hint: To render without a project, pass --out /path to render in ad-hoc mode.",
                err=True,
                fg=typer.colors.YELLOW,
            )
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if dry:
        for action, src, dst in plan:
            typer.echo(f"{action:6}  {src or '-':40} -> {dst}")
    else:
        if out:
            typer.secho("[ok] Rendered (ad-hoc).", fg=typer.colors.GREEN)
        else:
            typer.secho("[ok] Rendered.", fg=typer.colors.GREEN)


@app.command("info")
def info_cmd(
    template_id: str = typer.Argument(..., help="Template id within the active BRS", autocompletion=_complete_template_ids),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table (default), plain, or json",
        show_default=True,
    ),
):
    """
    Show detailed information for a template: params (type/required/default/cli),
    render target and files, hooks, dependencies, and publish resolvers.

    Tip: Use this to discover supported params before rendering.
    """
    try:
        desc = load_desc(template_id)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Build a structured payload for table/plain/json
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
                "exists": getattr(ps, "exists", None),
            }
        )
    files_list = [f"{src} -> {dst}" for (src, dst) in (desc.render_files or [])]
    hooks_map = desc.hooks or {}
    publish_map = desc.publish or {}
    requires = list(desc.required_templates or [])
    tools_req = list(getattr(desc, "tools_required", []) or [])
    tools_opt = list(getattr(desc, "tools_optional", []) or [])

    fmt = (format or "table").lower()
    if fmt == "json":
        import json

        payload = {
            "id": desc.id,
            "description": desc.description,
            "render_into": desc.render_into,
            "files": files_list,
            "params": params_list,
            "hooks": hooks_map,
            "required_templates": requires,
            "publish": publish_map,
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
            # Overview table
            t1 = Table(title=f"Template: {desc.id}", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
            t1.add_column("Field", style="bold", no_wrap=True)
            t1.add_column("Value")
            t1.add_row("Description", str(desc.description or ""))
            t1.add_row("Render Into", str(desc.render_into))
            t1.add_row("Required Templates", ", ".join(requires) if requires else "-")
            console.print(t1)

            # Files
            t2 = Table(title="Render Files", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
            t2.add_column("Mapping")
            if files_list:
                for m in files_list:
                    t2.add_row(m)
            console.print(t2)

            # Params
            t3 = Table(title="Parameters", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
            t3.add_column("Name", style="cyan", no_wrap=True)
            t3.add_column("Type", width=8)
            t3.add_column("Required", width=9)
            t3.add_column("Default")
            t3.add_column("CLI")
            t3.add_column("Exists", width=7)
            t3.add_column("Description")
            if params_list:
                for p in params_list:
                    dval = p.get("default")
                    if isinstance(dval, bool):
                        dstr = "true" if dval else "false"
                    else:
                        dstr = "" if dval is None else str(dval)
                    t3.add_row(
                        str(p.get("name")),
                        str(p.get("type")),
                        "yes" if p.get("required") else "no",
                        dstr,
                        str(p.get("cli") or ""),
                        str(p.get("exists") or ""),
                        str(p.get("description") or ""),
                    )
            console.print(t3)

            # Hooks
            t4 = Table(title="Hooks", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
            t4.add_column("Stage", style="bold")
            t4.add_column("Callables")
            for stage in ("pre_render", "post_render", "pre_run", "post_run"):
                entries = hooks_map.get(stage) or []
                t4.add_row(stage, "\n".join(map(str, entries)) if entries else "-")
            console.print(t4)

            # Publish
            t5 = Table(title="Publish", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
            t5.add_column("Key", style="bold")
            t5.add_column("Resolver")
            if publish_map:
                for key, spec in publish_map.items():
                    resolver = (spec or {}).get("resolver", "")
                    t5.add_row(str(key), str(resolver))
            console.print(t5)
            # Tools
            t6 = Table(title="Tools", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
            t6.add_column("Required")
            t6.add_column("Optional")
            t6.add_row(
                ", ".join(tools_req) if tools_req else "-",
                ", ".join(tools_opt) if tools_opt else "-",
            )
            console.print(t6)
            return

    # plain output
    typer.echo(f"id: {desc.id}")
    typer.echo(f"description: {desc.description}")
    typer.echo(f"render_into: {desc.render_into}")
    typer.echo("files:")
    for m in files_list:
        typer.echo(f"  - {m}")
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
    typer.echo("required_templates:")
    for r in requires or []:
        typer.echo(f"  - {r}")
    typer.echo("publish:")
    for k, spec in publish_map.items():
        typer.echo(f"  - {k}: {(spec or {}).get('resolver')}")
    typer.echo("tools:")
    if tools_req:
        typer.echo("  required:")
        for t in tools_req:
            typer.echo(f"    - {t}")
    if tools_opt:
        typer.echo("  optional:")
        for t in tools_opt:
            typer.echo(f"    - {t}")


@app.command("readme")
def readme_cmd(
    template_id: str = typer.Argument(..., help="Template id within the active BRS", autocompletion=_complete_template_ids),
):
    """
    Show the README.md for a template (if present).
    """
    try:
        tpl_dir = brs_loader.get_paths().templates_dir / template_id
        readme_path = tpl_dir / "README.md"
        if not readme_path.exists():
            typer.secho(
                f"README.md not found for template '{template_id}'.",
                err=True,
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(code=1)
        typer.echo(readme_path.read_text())
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command("run")
def run(
    template_id: str = typer.Argument(..., help="Template id within the active BRS", autocompletion=_complete_template_ids),
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
    out: Path = typer.Option(None, "--out", help="Run in ad-hoc mode from this directory (reads bpm.meta.yaml)"),
    allow_outside_cwd: bool = typer.Option(False, "--allow-outside-cwd/--no-allow-outside-cwd", help="Bypass cwd==--dir safety check (advanced)"),
):
    """
    Execute the template's run entry (e.g., run.sh) with pre/post hooks.
    """
    # Decide mode: project vs ad-hoc
    adhoc_dir: Path | None = None
    if out:
        adhoc_dir = out.resolve()
    else:
        # Auto-detect ad-hoc if no project.yaml but bpm.meta.yaml exists in CWD
        from bpm.core.project_io import project_file_path
        if not project_file_path(project_dir.resolve()).exists() and (Path.cwd() / "bpm.meta.yaml").exists():
            adhoc_dir = Path.cwd()

    # Safety warning for project mode
    if not adhoc_dir and project_dir.resolve() != Path(".").resolve():
        if not allow_outside_cwd:
            typer.secho(
                "Warning: running from outside the project directory; consider 'cd' into it or pass --allow-outside-cwd to silence this warning.",
                err=True,
                fg=typer.colors.YELLOW,
            )

    try:
        svc.run(project_dir.resolve(), template_id, adhoc_out=adhoc_dir)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho("[ok] Run completed.", fg=typer.colors.GREEN)


@app.command("publish")
def publish(
    template_id: str = typer.Argument(..., help="Template id within the active BRS", autocompletion=_complete_template_ids),
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
    out: Path = typer.Option(None, "--out", help="Publish in ad-hoc mode from this directory (reads bpm.meta.yaml)"),
    allow_outside_cwd: bool = typer.Option(False, "--allow-outside-cwd/--no-allow-outside-cwd", help="Bypass cwd==--dir safety check (advanced)"),
):
    """
    Run all publish resolvers defined by the template and persist results into project.yaml.
    """
    # Decide mode: project vs ad-hoc
    adhoc_dir: Path | None = None
    if out:
        adhoc_dir = out.resolve()
    else:
        from bpm.core.project_io import project_file_path
        if not project_file_path(project_dir.resolve()).exists() and (Path.cwd() / "bpm.meta.yaml").exists():
            adhoc_dir = Path.cwd()

    # Safety warning for project mode
    if not adhoc_dir and project_dir.resolve() != Path(".").resolve():
        if not allow_outside_cwd:
            typer.secho(
                "Warning: running from outside the project directory; consider 'cd' into it or pass --allow-outside-cwd to silence this warning.",
                err=True,
                fg=typer.colors.YELLOW,
            )

    try:
        pub = svc.publish(project_dir.resolve(), template_id, adhoc_out=adhoc_dir)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.echo(str(pub))


@app.command("list")
def list_templates(
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table (default), plain, or json",
        show_default=True,
    ),
):
    """
    Show all available templates in the active BRS.
    """
    try:
        tdir = brs_loader.get_paths().templates_dir
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    items = []
    if tdir.exists():
        for d in sorted([p for p in tdir.iterdir() if p.is_dir()]):
            tid = d.name
            try:
                desc = load_desc(tid)
                items.append({"id": desc.id, "description": desc.description or ""})
            except Exception:
                # Skip invalid template folders silently
                continue

    if not items:
        typer.echo("(no templates)")
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
                title="Templates (Active BRS)",
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

    # plain output
    for it in items:
        did = it["id"]
        desc = it.get("description", "")
        if desc:
            typer.echo(f"{did} - {desc}")
        else:
            typer.echo(did)
