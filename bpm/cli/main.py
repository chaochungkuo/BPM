import typer
from bpm.cli import project as project_cli
from bpm.cli import template as template_cli
from bpm.cli import resource as resource_cli
from bpm.cli import workflow as workflow_cli

app = typer.Typer(
    no_args_is_help=True,
    add_completion=True,
    help=(
        "🔬 Bioinformatics Project Manager (BPM)\n\n"
        "BPM is a lightweight, Python-based CLI that adds a management layer to your\n"
        "bioinformatics projects. It brings order and reusability without locking you\n"
        "into a single framework.\n\n"
        "What it is: a stable engine to manage projects and reusable templates stored\n"
        "in BRS (Bioinformatics Resource Stores).\n\n"
        "What it isn’t: not a workflow engine (Nextflow/Snakemake), not a LIMS, not a\n"
        "cloud service. BPM complements these by organizing and recording your analysis\n"
        "state in plain files (project.yaml, stores.yaml).\n\n"
        "Use the subcommands below to manage resources, initialize projects, render\n"
        "and run templates, or execute workflows."
    ),
)
app.add_typer(project_cli.app, name="project", help="Create and inspect BPM projects.")
app.add_typer(template_cli.app, name="template", help="Render/run/publish templates from the active BRS.")
app.add_typer(resource_cli.app, name="resource", help="Manage BRS resource stores (add/activate/list/info/remove).")
app.add_typer(workflow_cli.app, name="workflow", help="Render and run workflows from the active BRS.")

if __name__ == "__main__":
    app()
