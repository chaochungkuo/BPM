"""BPM CLI main module."""
import typer
from bpm.cli import generate, init, run, update

app = typer.Typer(help="BPM - Genomic Project Manager")

# Add subcommands
app.add_typer(generate.app, name="generate")
app.add_typer(init.app, name="init")
app.add_typer(run.app, name="run")
app.add_typer(update.app, name="update")
if __name__ == "__main__":
    app()