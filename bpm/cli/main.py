import typer
from bpm.cli import project as project_cli
from bpm.cli import template as template_cli
from bpm.cli import resource as resource_cli
from bpm.cli import workflow as workflow_cli

app = typer.Typer(no_args_is_help=True, add_completion=False)
app.add_typer(project_cli.app, name="project")
app.add_typer(template_cli.app, name="template")
app.add_typer(resource_cli.app, name="resource")
app.add_typer(workflow_cli.app, name="workflow")

if __name__ == "__main__":
    app()
