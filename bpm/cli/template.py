from __future__ import annotations
from pathlib import Path
import typer

from bpm.core import template_service as svc

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command("render")
def render(
    template_id: str = typer.Argument(..., help="Template id within the active BRS"),
    project_dir: str = typer.Option(".", "--dir", help="Project directory (contains project.yaml)"),
    dry: bool = typer.Option(False, "--dry", help="Dry-run: only show plan, no changes"),
    param: list[str] = typer.Option(None, "--param", help="KEY=VALUE (can repeat)"),
    out: str = typer.Option(None, "--out", help="Ad-hoc output directory (do not touch project.yaml)"),
):
    """
    Render a template into the project. Provide template params with --param KEY=VALUE.
    """
    try:
        plan = svc.render(
            Path(project_dir).resolve(),
            template_id,
            params_kv=param,
            dry=dry,
            adhoc_out=Path(out).resolve() if out else None,
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
    template_id: str = typer.Argument(..., help="Template id within the active BRS"),
    project_dir: str = typer.Option(".", "--dir", help="Project directory (contains project.yaml)"),
):
    """
    Execute the template's run entry (e.g., run.sh) with hooks.
    """
    try:
        svc.run(Path(project_dir).resolve(), template_id)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho("[ok] Run completed.", fg=typer.colors.GREEN)


@app.command("publish")
def publish(
    template_id: str = typer.Argument(..., help="Template id within the active BRS"),
    project_dir: str = typer.Option(".", "--dir", help="Project directory (contains project.yaml)"),
):
    """
    Run all publish resolvers defined by the template and persist results.
    """
    try:
        pub = svc.publish(Path(project_dir).resolve(), template_id)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.echo(str(pub))
