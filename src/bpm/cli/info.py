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
    target: str = typer.Argument(..., help="Component or project to get info about"),
    project: Optional[Path] = typer.Option(None, "--project", "-p", help="Path to project.yaml")
):
    """Display information about components or projects."""
    bpm_console.section("BPM Info", f"Getting information for: {target}")
    bpm_console.info(f"Target: {target}")
    if project:
        bpm_console.path(f"Project file: {project}") 