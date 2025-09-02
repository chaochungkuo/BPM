from __future__ import annotations
import typer
from pathlib import Path

from bpm.core import project_service as svc

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command("init")
def init(
    project_name: str = typer.Argument(..., help="Name of the project (policy enforced by BRS)."),
    project_path: str = typer.Option(..., "--project-path", help="Host-aware path (e.g., nextgen:/projects/NAME)"),
    authors: str = typer.Option("", "--author", help="Comma-separated author ids (e.g., ckuo,lgan)"),
    cwd: str = typer.Option(".", "--cwd", help="Directory to create the project in"),
):
    """
    Create a new project directory and write project.yaml.
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
    Show raw project information (YAML-like dict).
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
    Display a simple status summary.
    """
    try:
        s = svc.status_table(Path(project_dir).resolve())
    except FileNotFoundError as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(s)