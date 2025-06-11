import typer
from bpm.cli import init, info, run
from bpm.cli.repo import app as repo_app
from bpm.cli.generate import generate_app
from bpm.cli.update import update

app = typer.Typer(
    name="bpm",
    help="Bioinformatics Pipeline Manager",
    add_completion=True,
    rich_markup_mode="rich",
)

# Add commands
app.command()(init)
app.add_typer(generate_app, name="generate")
app.command()(info)
app.command()(run)
app.command()(update)
app.add_typer(repo_app, name="repo")

if __name__ == "__main__":
    app() 