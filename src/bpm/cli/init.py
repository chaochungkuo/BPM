"""Project initialization commands.

This module provides the command-line interface for initializing new BPM projects.
"""

from pathlib import Path
from typing import Optional

import typer

from ..core.controller import Controller, ControllerError
from ..utils.ui.console import BPMConsole

# Initialize console
console = BPMConsole()

def init(
    project_path: str = typer.Argument(
        ...,
        help="Project name or full path in format: YYMMDD_Name1_Name2_Institute_Application"
    ),
    from_project: Optional[Path] = typer.Option(
        None,
        "--from",
        "-fr",
        help="Path to source project.yaml to inherit settings from"
    ),
    authors: Optional[str] = typer.Option(
        None,
        "--authors",
        "-a",
        help="Comma-separated list of author IDs (e.g. ckuo,lgan)"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force overwrite if project directory exists"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed logging information"
    )
) -> None:
    """Initialize a new BPM project.
    
    This command creates a new BPM project with the specified name and configuration.
    The project name should follow the format: YYMMDD_Name1_Name2_Institute_Application.
    
    Options:
        --from/-fr: Path to an existing project.yaml to inherit settings from
        --authors/-a: Comma-separated list of author IDs to add to the project
        --force/-f: Force overwrite if project directory already exists
        --verbose/-v: Show detailed logging information
    
    The project_path argument can be either:
    1. Just the project name (creates in current directory)
    2. Full path including project name
    
    Examples:
        # Create a new project in current directory
        bpm init 230101_Name1_Name2_Institute_Application
        
        # Create a project with full path
        bpm init /path/to/230101_Name1_Name2_Institute_Application
        
        # Create a project inheriting settings from another project
        bpm init 230101_Name1_Name2_Institute_Application --from /path/to/source/project.yaml
        
        # Create a project with specific authors
        bpm init 230101_Name1_Name2_Institute_Application --authors ckuo,lgan
        
        # Force overwrite an existing project
        bpm init 230101_Name1_Name2_Institute_Application --force
        
        # Combine multiple options
        bpm init 230101_Name1_Name2_Institute_Application --from /path/to/source/project.yaml --authors ckuo,lgan --force
    """
    try:
        if verbose:
            console.info(f"Initializing project: {project_path}")
            
        # Convert paths to host format for storage
        project_path = Path(project_path).resolve()
        if verbose:
            console.info(f"Resolved project path: {project_path}")
            
        if from_project:
            from_project = Path(from_project).resolve()
            if verbose:
                console.info(f"Using source project: {from_project}")
        
        # Parse authors list
        author_list = authors.split(",") if authors else []
        if verbose:
            if author_list:
                console.info(f"Adding authors: {', '.join(author_list)}")
            else:
                console.info("No authors specified")
        
        # Initialize controller
        controller = Controller(verbose=verbose)
        if verbose:
            console.info("Initialized controller")
        
        # Create project
        if verbose:
            console.info("Creating project...")
        controller.create_project(project_path, from_project, author_list, force)
        controller.project.save_to_file()
        # Show success message
        console.panel(message=
                      f"Initializing project: {controller.project.info.project_name}\n"
                      f"Project path: {controller.project.info.project_dir}",
                      title="BPM Init",
                      style="info")
        
        if verbose:
            console.info("Project initialization completed successfully")
        
    except ControllerError as e:
        console.error(str(e))
        raise typer.Exit(1)