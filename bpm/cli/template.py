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
):
    """
    Render a template into the project (or to --out in ad‑hoc mode).

    Notes:
    - Param precedence: descriptor defaults < stored project params < CLI --param
    - Ad‑hoc (with --out): skips hooks and project.yaml updates; writes bpm.meta.yaml
    """
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


@app.command("run")
def run(
    template_id: str = typer.Argument(..., help="Template id within the active BRS", autocompletion=_complete_template_ids),
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
):
    """
    Execute the template's run entry (e.g., run.sh) with pre/post hooks.
    """
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
):
    """
    Run all publish resolvers defined by the template and persist results into project.yaml.
    """
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
        except Exception:
            fmt = "plain"
        else:
            table = Table(title="Templates (Active BRS)")
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
