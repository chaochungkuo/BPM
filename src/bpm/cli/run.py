"""Run BPM workflows.

This module provides the command-line interface for running BPM workflows.
"""

import typer
import inspect
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from rich.console import Console

from ..core.controller import Controller
from ..utils.ui.console import BPMConsole
from ..utils.path import path

# Configure rich console
console = BPMConsole()
run_app = typer.Typer(name="run", help="Run BPM workflows.")

def get_workflow_options(workflow_name: str) -> Dict[str, Any]:
    """Get workflow configuration and options from workflow config file."""
    controller = Controller()
    workflow_path = controller.cache_manager.get_workflow_path(workflow_name)
    config_path = workflow_path / "workflow_config.yaml"

    if not config_path.exists():
        raise typer.Exit(f"[bold red]Workflow config not found:[/] {config_path}")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    options = {}
    for key, spec in config.get("inputs", {}).items():
        opt_type = {
            "boolean": bool,
            "integer": int,
            "float": float,
            "path": Path
        }.get(spec.get("type"), str)

        options[key] = {
            "default": None if spec.get("required") else spec.get("default"),
            "help": spec.get("description", key),
            "type": opt_type
        }
    description = config.get("description", "")
    return description, options

def make_run_command(workflow_name: str,
                    workflow_desc: str,
                    workflow_options: Dict[str, Any]) -> Callable:
    """Create a dynamic command function for a workflow."""
    def dynamic_run(**kwargs):
        verbose = kwargs.pop("verbose", False)
        controller = Controller(verbose=verbose)
        project_path = kwargs.pop("project", None)

        if project_path:
            project_path = path.host_solver.from_hostpathstr_to_path(project_path)
            console.print(f"[bold green]Project file:[/] {project_path}")
            controller.load_project(project_path)
        else:
            console.error("Project file is required")
            raise typer.Exit(1)

        if verbose:
            console.info(f"Running workflow: {workflow_name}")

        params = {
            "workflow": workflow_name,
            "project": project_path,
            **kwargs
        }
        
        try:
            controller.collect_contexts(params=params)
            controller.run_workflow(workflow_name=workflow_name)
        except Exception as e:
            console.error(f"Failed to run workflow: {e}")
            raise typer.Exit(1)

    # Create dynamic function signature
    parameters = [
        inspect.Parameter(
            "project",
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=typer.Option(
                False,
                "--project",
                "-p",
                help="Path to project.yaml"
            ),
            annotation=Path,
        ),
        inspect.Parameter(
            "verbose",
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=typer.Option(
                False,
                "--verbose",
                "-v",
                help="Show detailed logging information"
            ),
            annotation=bool,
        )
    ]

    for name, spec in workflow_options.items():
        option = typer.Option(
            default=spec["default"],
            help=spec["help"]
        )
        
        parameters.append(
            inspect.Parameter(
                name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=option,
                annotation=spec["type"],
            )
        )

    dynamic_run.__doc__ = workflow_desc
    dynamic_run.__signature__ = inspect.Signature(parameters)
    return dynamic_run

def register_run_commands():
    """Register all available workflows as commands."""
    try:
        controller = Controller()
        workflow_list = controller.cache_manager.list_workflows()
        # console.print(f"Workflow list: {workflow_list}")
        for workflow in workflow_list:
            workflow_desc, opts = get_workflow_options(workflow)
            cmd = make_run_command(workflow, workflow_desc, opts)
            run_app.command(name=workflow)(cmd)
    except Exception as e:
        if "No configuration directory specified" in str(e):
            console.warning(f"No repository configured. Check bpm repo --help")
        else:
            console.error(f"{str(e)}")

# Register commands when module is imported
register_run_commands() 