"""Run BPM workflows.

This module provides the command-line interface for running BPM workflows.
"""

import typer
from pathlib import Path
from typing import Optional

from rich.console import Console

from ..core.controller import Controller
from ..utils.ui.console import BPMConsole
from ..utils.path import path

# Configure rich console
console = BPMConsole()

def run(
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
    """Run a BPM project.
    
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
        
        # Run project
        if verbose:
            console.info("Starting project execution")
        controller.run_project()
        
    except Exception as e:
        console.error(f"Failed to run project: {e}")
        raise typer.Exit(1) 