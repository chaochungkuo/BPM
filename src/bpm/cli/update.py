"""Update template outputs in a project.

This module provides the update command for updating template outputs in a project.
"""

import typer
from pathlib import Path
from typing import Optional, Tuple
from rich.pretty import pprint
from ..core.controller import Controller
from ..utils.ui.console import BPMConsole
from ..utils.path import host_solver
from .util import get_template_outputs

console = BPMConsole()

def parse_template_name(template: str) -> Tuple[str, str]:
    """Parse template name into section and name.
    
    Args:
        template: Template name in format 'section:name'
        
    Returns:
        Tuple of (section, name)
        
    Raises:
        typer.Exit: If template name is not in the correct format
    """
    if ":" not in template:
        console.error("Template name must be in format 'section:name' (e.g., 'demultiplexing:bclconvert')")
        raise typer.Exit(1)
        
    section, name = template.split(":")
    if not section or not name:
        console.error("Both section and name are required in format 'section:name'")
        raise typer.Exit(1)
        
    return section, name

def update(
    template: str = typer.Option(
        ...,
        "--template",
        "-t",
        help="Template name in format 'section:name' (e.g., 'demultiplexing:bclconvert')"
    ),
    project: Path = typer.Option(
        ...,
        "--project",
        "-p",
        help="Path to project.yaml"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed logging information"
    )
) -> None:
    """Update template outputs in a project.
    
    This command updates the output values for a specific template in a project
    by running the output resolvers defined in the template.
    """
    # output_opts = get_template_outputs(template)
    # pprint(output_opts)
    try:
        # Parse template name
        section, name = parse_template_name(template)
        # Initialize controller
        controller = Controller(verbose=verbose)
        if verbose:
            console.info(f"Template section: {section}, name: {name}")
        if project:
            # project = host_solver.from_hostpathstr_to_path(str(project))
            project = project.resolve()
            console.print(f"[bold green]Project file:[/] {project}")
            controller.load_project(project)
        else:
            console.error("Project file is required")
            raise typer.Exit(1)
        
        # Update outputs
        try:
            controller.update_template_outputs(section, template)
            console.success(f"Successfully updated outputs for template {template}")
        except Exception as e:
            console.error(f"Failed to update outputs: {e}")
            # raise typer.Exit(1)
            
    except Exception as e:
        console.error(f"An error occurred: {e}")
        # raise typer.Exit(1)
