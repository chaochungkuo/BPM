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
    adopt: list[Path] = typer.Option(None, "--adopt", help="Adopt one or more ad-hoc folders (with bpm.meta.yaml) into the new project", show_default=False),
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

    # Optionally adopt ad-hoc folders
    if adopt:
        try:
            svc.adopt(pdir, [Path(a).resolve() for a in adopt], on_exists="merge")
            typer.secho(f"[ok] Adopted {len(adopt)} ad-hoc folder(s) into project.", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(f"Warning: failed to adopt ad-hoc folders: {e}", err=True, fg=typer.colors.YELLOW)

    typer.secho(f"[ok] Created project at: {pdir}", fg=typer.colors.GREEN)


@app.command("info")
def info(
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table (default), plain, or json",
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
    # Preserve original author list for JSON, but display full names + affiliation in human formats
    authors_raw = (data.get("authors") or [])
    authors_ids = [a.get("id") for a in authors_raw]
    def _author_display(a: dict) -> str:
        name = (a or {}).get("name") or (a or {}).get("id") or ""
        aff = (a or {}).get("affiliation")
        return f"{name} ({aff})" if aff else str(name)
    authors_disp = ", ".join(_author_display(a) for a in authors_raw)
    templates = [t.get("id") for t in (data.get("templates") or [])]
    templates_full = list(data.get("templates") or [])

    fmt = (format or "table").lower()

    if fmt == "json":
        import json

        typer.echo(
            json.dumps(
                {
                    "name": name,
                    "status": status,
                    "authors": authors_ids,
                    "templates": templates,
                    "templates_full": templates_full,
                },
                indent=2,
            )
        )
        return

    if fmt == "table":
        try:
            from rich.console import Console
            from rich.table import Table
            from rich import box
        except Exception:
            fmt = "plain"  # fallback
        else:
            table = Table(
                title="Project Info",
                box=box.MINIMAL_DOUBLE_HEAD,
                header_style="bold cyan",
                row_styles=["", "dim"],
            )
            table.add_column("Key", style="bold", no_wrap=True)
            table.add_column("Value")
            table.add_row("Name", str(name))
            table.add_row("Status", str(status))
            table.add_row("Authors", authors_disp)
            table.add_row("Templates", ", ".join(map(str, templates)))
            Console().print(table)

            # Detailed templates table (3 columns: ID, Status, Key-Value)
            if templates_full:
                t2 = Table(
                    title="Templates",
                    box=box.MINIMAL_DOUBLE_HEAD,
                    header_style="bold cyan",
                )
                t2.add_column("ID", style="cyan", no_wrap=True)
                t2.add_column("Status", style="bold", width=10)
                t2.add_column("Key-Value", overflow="fold")

                def _fmt_bool(v):
                    return "true" if bool(v) else "false"

                def _kv_block(t: dict) -> str:
                    lines: list[str] = []
                    # Params
                    params = t.get("params") or {}
                    lines.append("[cyan]Params[/cyan]")
                    if params:
                        for k in sorted(params.keys()):
                            v = params.get(k)
                            if isinstance(v, bool):
                                v = _fmt_bool(v)
                            lines.append(f"[green]{k}[/green] {v}")
                    else:
                        lines.append("(none)")

                    # Published
                    pub = t.get("published") or {}
                    lines.append("")
                    lines.append("[cyan]Published[/cyan]")
                    if pub:
                        for k in sorted(pub.keys()):
                            sv = str(pub.get(k))
                            lines.append(f"[green]{k}[/green] {sv}")
                    else:
                        lines.append("(none)")

                    # Source
                    src = t.get("source") or {}
                    lines.append("")
                    lines.append("[cyan]Source[/cyan]")
                    if src:
                        for key in ("brs_id", "brs_version", "template_id"):
                            if key in src and src.get(key) is not None:
                                lines.append(f"[green]{key}[/green] {src.get(key)}")
                    else:
                        lines.append("(none)")

                    return "\n".join(lines)

                for t in templates_full:
                    t2.add_row(
                        str(t.get("id")),
                        str(t.get("status", "")),
                        _kv_block(t),
                    )
                Console().print(t2)
            return

    # plain (default; preserves existing test expectations)
    typer.echo(f"name: {name}")
    typer.echo(f"status: {status}")
    typer.echo(f"authors: {authors_disp}")
    typer.echo(f"templates: {templates}")
    if templates_full:
        typer.echo("templates_detail:")
        for t in templates_full:
            tid = t.get("id")
            typer.echo(f"- id: {tid}")
            typer.echo(f"  status: {t.get('status')}")
            if t.get("params"):
                typer.echo("  params:")
                for k, v in (t.get("params") or {}).items():
                    if isinstance(v, bool):
                        v = "true" if v else "false"
                    typer.echo(f"    {k}: {v}")
            if t.get("published"):
                typer.echo("  published:")
                for k, v in (t.get("published") or {}).items():
                    typer.echo(f"    {k}: {v}")
            if t.get("source"):
                s = t.get("source") or {}
                typer.echo(f"  source: brs={s.get('brs_id','')} ver={s.get('brs_version','')} tpl={s.get('template_id','')}")


@app.command("adopt")
def adopt(
    from_dir: list[Path] = typer.Option(..., "--from", help="Ad-hoc folder(s) to adopt (contain bpm.meta.yaml)", show_default=False),
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
    on_exists: str = typer.Option("merge", "--on-exists", help="Collision policy: skip|merge|overwrite", show_default=True),
):
    """
    Insert one or more ad-hoc bpm.meta.yaml records into an existing project.yaml.
    """
    try:
        svc.adopt(project_dir.resolve(), [Path(d).resolve() for d in from_dir], on_exists=on_exists)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho("[ok] Adoption completed.", fg=typer.colors.GREEN)


@app.command("status")
def status(
    project_dir: Path = typer.Option(Path("."), "--dir", help="Project directory (contains project.yaml)"),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table (default), plain, or json",
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

    fmt = (format or "table").lower()
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
            from rich import box
        except Exception:
            # Fallback to plain
            s = svc.status_table(project_dir.resolve())
            typer.echo(s)
            return

        table = Table(
            title=f"Project Status: {name} ({status_val})",
            box=box.MINIMAL_DOUBLE_HEAD,
            header_style="bold cyan",
            row_styles=["", "dim"],
        )
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
