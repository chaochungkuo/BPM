import typer
from bpm.cli import project as project_cli
from bpm.cli import template as template_cli

app = typer.Typer(no_args_is_help=True, add_completion=False)
app.add_typer(project_cli.app, name="project")   # bpm project ...
app.add_typer(template_cli.app, name="template") # bpm template ...

if __name__ == "__main__":
    app()