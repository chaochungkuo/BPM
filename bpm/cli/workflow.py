from __future__ import annotations
from pathlib import Path
import typer

from bpm.core import workflow_service as svc

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command("render")
def render(
    workflow_id: str = typer.Argument(..., help="Workflow id within the active BRS"),
    project_dir: str = typer.Option(".", "--dir", help="Project directory (contains project.yaml)"),
    dry: bool = typer.Option(False, "--dry", help="Dry-run: only show plan, no changes"),
    param: list[str] = typer.Option(None, "--param", help="KEY=VALUE (can repeat)"),
):
    """
    Render a workflow into the project. Provide workflow params with --param KEY=VALUE.
    """
    try:
        plan = svc.render(Path(project_dir).resolve(), workflow_id, params_kv=param, dry=dry)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if dry:
        for action, src, dst in plan:
            typer.echo(f"{action:6}  {src or '-':40} -> {dst}")
    else:
        typer.secho("[ok] Rendered workflow.", fg=typer.colors.GREEN)


@app.command("run")
def run(
    workflow_id: str = typer.Argument(..., help="Workflow id within the active BRS"),
    project_dir: str = typer.Option(".", "--dir", help="Project directory (contains project.yaml)"),
):
    """
    Execute the workflow's run entry (e.g., run.sh).
    """
    try:
        svc.run(Path(project_dir).resolve(), workflow_id)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho("[ok] Workflow run completed.", fg=typer.colors.GREEN)

