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


@app.command("render")
def render(
    template_id: str = typer.Argument(..., help="Template id within the active BRS", autocompletion=_complete_template_ids),
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
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

    try:
        plan = svc.render(
            project_dir.resolve(),
            template_id,
            params_kv=param,
            dry=dry,
            adhoc_out=out.resolve() if out else None,
        )
    except Exception as e:
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
            }
        )
    files_list = [f"{src} -> {dst}" for (src, dst) in (desc.render_files or [])]
    hooks_map = desc.hooks or {}
    publish_map = desc.publish or {}
    requires = list(desc.required_templates or [])

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
            t3.add_column("Description")
            if params_list:
                for p in params_list:
                    t3.add_row(
                        str(p.get("name")),
                        str(p.get("type")),
                        "yes" if p.get("required") else "no",
                        "" if p.get("default") is None else str(p.get("default")),
                        str(p.get("cli") or ""),
                        str(p.get("description") or ""),
                    )
            console.print(t3)

            # Hooks
            t4 = Table(title="Hooks", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
            t4.add_column("Stage", style="bold")
            t4.add_column("Callables")
            for stage in ("post_render", "pre_run", "post_run"):
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
        typer.echo(
            f"  - {p['name']} (type={p['type']}, required={'yes' if p['required'] else 'no'}, default={p['default']}, cli={p['cli']})"
        )
    typer.echo("required_templates:")
    for r in requires or []:
        typer.echo(f"  - {r}")
    typer.echo("publish:")
    for k, spec in publish_map.items():
        typer.echo(f"  - {k}: {(spec or {}).get('resolver')}")


@app.command("run")
def run(
    template_id: str = typer.Argument(..., help="Template id within the active BRS", autocompletion=_complete_template_ids),
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
    allow_outside_cwd: bool = typer.Option(False, "--allow-outside-cwd/--no-allow-outside-cwd", help="Bypass cwd==--dir safety check (advanced)"),
):
    """
    Execute the template's run entry (e.g., run.sh) with pre/post hooks.
    """
    # Safety: require running from the project directory unless explicitly allowed
    if project_dir.resolve() != Path(".").resolve():
        if not allow_outside_cwd:
            typer.secho(
                "Warning: running from outside the project directory; consider 'cd' into it or pass --allow-outside-cwd to silence this warning.",
                err=True,
                fg=typer.colors.YELLOW,
            )

    try:
        svc.run(project_dir.resolve(), template_id)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho("[ok] Run completed.", fg=typer.colors.GREEN)


@app.command("publish")
def publish(
    template_id: str = typer.Argument(..., help="Template id within the active BRS", autocompletion=_complete_template_ids),
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
    allow_outside_cwd: bool = typer.Option(False, "--allow-outside-cwd/--no-allow-outside-cwd", help="Bypass cwd==--dir safety check (advanced)"),
):
    """
    Run all publish resolvers defined by the template and persist results into project.yaml.
    """
    # Safety: require running from the project directory unless explicitly allowed
    if project_dir.resolve() != Path(".").resolve():
        if not allow_outside_cwd:
            typer.secho(
                "Warning: running from outside the project directory; consider 'cd' into it or pass --allow-outside-cwd to silence this warning.",
                err=True,
                fg=typer.colors.YELLOW,
            )

    try:
        pub = svc.publish(project_dir.resolve(), template_id)
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
