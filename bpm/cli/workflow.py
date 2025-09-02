from __future__ import annotations
from pathlib import Path
import typer

from bpm.core import workflow_service as svc
from bpm.core import brs_loader

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help=(
        "Workflow commands.\n\n"
        "Render and run workflows from the active BRS. Workflows do not modify project.yaml."
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


@app.command("render")
def render(
    workflow_id: str = typer.Argument(..., help="Workflow id within the active BRS", autocompletion=_complete_workflow_ids),
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
    dry: bool = typer.Option(False, "--dry", help="Dry-run: only show plan, no changes"),
    param: list[str] = typer.Option(None, "--param", help="KEY=VALUE (can repeat)"),
):
    """
    Render a workflow into the project output tree. No project.yaml updates.
    """
    try:
        plan = svc.render(project_dir.resolve(), workflow_id, params_kv=param, dry=dry)
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
    workflow_id: str = typer.Argument(..., help="Workflow id within the active BRS", autocompletion=_complete_workflow_ids),
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
):
    """
    Execute the workflow's run entry (e.g., run.sh) in the rendered folder.
    """
    try:
        svc.run(project_dir.resolve(), workflow_id)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho("[ok] Workflow run completed.", fg=typer.colors.GREEN)
