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
    workflow: str = typer.Argument(..., help="Workflow to run (e.g., export:html_report_RNAseq)"),
    project: Path = typer.Option(..., "--project", "-p", help="Path to project.yaml")
):
    """Run a workflow."""
    console.section("BPM Run", f"Running workflow: {workflow}")
    console.info(f"Workflow: {workflow}")
    console.path(f"Project file: {project}") 