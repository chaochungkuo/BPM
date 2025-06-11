"""Display project information.

This module provides the command-line interface for displaying project information.
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from ..core.controller import Controller
from ..utils.ui.console import BPMConsole
from ..utils.path.paths import path

# Configure rich console
console = BPMConsole()

import typer

def info(
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
    """Show information about a BPM project.
    
    Args:
        project: Path to project.yaml
        verbose: Show detailed logging information
    """
    try:
        if verbose:
            console.info(f"Loading project from {project}")
            
        # Load project
        if not project.exists():
            console.error(f"Project file not found: {project}")
            raise typer.Exit(1)
            
        # Initialize controller
        controller = Controller(verbose=verbose)
        controller.load_project(project)
        
        # Show project info
        console.panel(
            message=f"Project: {controller.project.info.project_name}\n"
                   f"Path: {controller.project.info.project_dir}\n"
                   f"Authors: {', '.join(controller.project.info.authors)}",
            title="BPM Project Info",
            style="info"
        )
        
    except Exception as e:
        console.error(f"Failed to show project info: {e}")
        raise typer.Exit(1) 