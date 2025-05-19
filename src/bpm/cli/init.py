"""Initialize command module."""
import typer

app = typer.Typer(help="Initialize a new BPM project.")

@app.command()
def init(
    project_dir: str = typer.Argument(..., help="Directory to initialize the project in"),
    name: str = typer.Option(..., help="Project name"),
):
    """Initialize a new BPM project."""
    typer.echo(f"Initializing project '{name}' in {project_dir}")
    # TODO: Implement project initialization 