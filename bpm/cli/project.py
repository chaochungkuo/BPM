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
    outdir: Path = typer.Option(Path("."), "--outdir", help="Directory to create the project in"),
    authors: str = typer.Option("", "--author", help="Comma-separated author ids (e.g., ckuo,lgan)"),
    host: str = typer.Option(None, "--host", help="Explicit host key to record in project_path (overrides auto-detect)"),
):
    """
    Create a new project folder and write project.yaml using the active BRS policy.

    Examples:
    - bpm project init 250901_Demo_UKA --project-path nextgen:/projects/250901_Demo_UKA
    - bpm project init MyProj --project-path local:/abs/path --author ckuo,lgan --cwd /tmp
    """
    try:
        pdir = svc.init(Path(outdir).resolve(), project_name, authors, host)
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
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
    format: str = typer.Option(
        "plain",
        "--format",
        "-f",
        help="Output format: plain (default), table, or json",
        show_default=True,
    ),
):
    """
    Show a summary of project.yaml (name, status, authors, templates).
    """
    try:
        data = svc.info(project_dir.resolve())
    except FileNotFoundError as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    name = data.get("name")
    status = data.get("status")
    authors = [a.get("id") for a in (data.get("authors") or [])]
    templates = [t.get("id") for t in (data.get("templates") or [])]

    fmt = (format or "plain").lower()

    if fmt == "json":
        import json

        typer.echo(
            json.dumps(
                {
                    "name": name,
                    "status": status,
                    "authors": authors,
                    "templates": templates,
                },
                indent=2,
            )
        )
        return

    if fmt == "table":
        try:
            from rich.console import Console
            from rich.table import Table
        except Exception:
            fmt = "plain"  # fallback
        else:
            table = Table(title="Project Info")
            table.add_column("Key", style="bold", no_wrap=True)
            table.add_column("Value")
            table.add_row("Name", str(name))
            table.add_row("Status", str(status))
            table.add_row("Authors", ", ".join(map(str, authors)))
            table.add_row("Templates", ", ".join(map(str, templates)))
            Console().print(table)
            return

    # plain (default; preserves existing test expectations)
    typer.echo(f"name: {name}")
    typer.echo(f"status: {status}")
    typer.echo(f"authors: {authors}")
    typer.echo(f"templates: {templates}")


@app.command("status")
def status(
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
    format: str = typer.Option(
        "plain",
        "--format",
        "-f",
        help="Output format: plain (default), table, or json",
        show_default=True,
    ),
):
    """
    Display project status: project name/status and template entries with statuses.
    """
    try:
        # For plain we reuse the existing service table to keep tests stable
        if (format or "plain").lower() == "plain":
            s = svc.status_table(project_dir.resolve())
            typer.echo(s)
            return

        data = svc.info(project_dir.resolve())
    except FileNotFoundError as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    name = data.get("name")
    status_val = data.get("status")
    templates = [
        {"id": t.get("id"), "status": t.get("status")}
        for t in (data.get("templates") or [])
    ]

    fmt = (format or "plain").lower()
    if fmt == "json":
        import json

        typer.echo(
            json.dumps(
                {
                    "name": name,
                    "status": status_val,
                    "templates": templates,
                },
                indent=2,
            )
        )
        return

    if fmt == "table":
        try:
            from rich.console import Console
            from rich.table import Table
        except Exception:
            # Fallback to plain
            s = svc.status_table(project_dir.resolve())
            typer.echo(s)
            return

        table = Table(title=f"Project Status: {name} ({status_val})")
        table.add_column("Template", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        if not templates:
            # Leave empty body; Rich shows headers and title
            pass
        else:
            for t in templates:
                table.add_row(str(t.get("id")), str(t.get("status")))
        Console().print(table)
        return

    # Unknown format → treat as plain
    s = svc.status_table(project_dir.resolve())
    typer.echo(s)
