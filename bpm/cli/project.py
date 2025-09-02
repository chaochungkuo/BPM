from __future__ import annotations
import typer
from pathlib import Path

from bpm.core import project_service as svc

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help=(
        "Project commands.\n\n"
        "Use 'init' to create a new project directory (writes project.yaml),\n"
        "then 'info' and 'status' to inspect it."
    ),
)


@app.command("init")
def init(
    project_name: str = typer.Argument(..., help="Name of the project (policy enforced by BRS)."),
    project_path: str = typer.Option(..., "--project-path", help="Host-aware path (e.g., nextgen:/projects/NAME)"),
    authors: str = typer.Option("", "--author", help="Comma-separated author ids (e.g., ckuo,lgan)"),
    cwd: str = typer.Option(".", "--cwd", help="Directory to create the project in"),
):
    """
    Create a new project folder and write project.yaml using the active BRS policy.

    Examples:
    - bpm project init 250901_Demo_UKA --project-path nextgen:/projects/250901_Demo_UKA
    - bpm project init MyProj --project-path local:/abs/path --author ckuo,lgan --cwd /tmp
    """
    try:
        pdir = svc.init(Path(cwd).resolve(), project_name, project_path, authors)
    except ValueError as e:
        # Validation errors (e.g., name policy) → friendly message
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        # Unexpected errors → still tell the user, non-zero exit
        typer.secho(f"Unexpected error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=2)

    typer.secho(f"[ok] Created project at: {pdir}", fg=typer.colors.GREEN)


@app.command("info")
def info(
    project_dir: str = typer.Option(".", "--dir", help="Project directory (contains project.yaml)")
):
    """
    Show a concise summary of project.yaml fields (name, status, authors, templates).
    """
    try:
        data = svc.info(Path(project_dir).resolve())
    except FileNotFoundError as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Minimal pretty print; we keep YAML dumping out of CLI for now.
    typer.echo(f"name: {data.get('name')}")
    typer.echo(f"status: {data.get('status')}")
    typer.echo(f"authors: {[a.get('id') for a in (data.get('authors') or [])]}")
    typer.echo(f"templates: {[t.get('id') for t in (data.get('templates') or [])]}")


@app.command("status")
def status(
    project_dir: str = typer.Option(".", "--dir", help="Project directory (contains project.yaml)")
):
    """
    Display a simple status view: project name/status and template entries with statuses.
    """
    try:
        s = svc.status_table(Path(project_dir).resolve())
    except FileNotFoundError as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(s)
