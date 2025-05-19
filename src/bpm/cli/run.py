"""Run command module."""
import typer

app = typer.Typer(help="Run BPM templates and workflows.")

@app.command()
def run(
    template: str = typer.Argument(..., help="Template to run"),
    project_dir: str = typer.Option(..., help="Project directory"),
):
    """Run a BPM template."""
    typer.echo(f"Running template '{template}' in {project_dir}")
    # TODO: Implement template running 