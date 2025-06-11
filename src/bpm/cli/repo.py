"""Repository management commands.

This module provides the command-line interface for managing BPM repositories.
"""

import os
from pathlib import Path
import typer
from typing import Optional

from rich.console import Console
from rich.table import Table

from ..core.controller import Controller
from ..utils.ui.console import BPMConsole
from ..utils.path import path
from ..core.repo import CacheManager, RepositoryError
from ..core.helpers import get_cachedir

# Initialize console
console = BPMConsole()

# Get cache directory from environment or use default
cache_dir = get_cachedir()

# Initialize cache manager
cache_manager = CacheManager(cache_dir=cache_dir)

# Create the Typer app
repo_app = typer.Typer(
    name="repo",
    help="Manage BPM repositories.",
    add_completion=True,
    rich_markup_mode="rich"
)

def add_repo(source: Path) -> None:
    """Add a repository to the cache.
    
    Args:
        source: Path to repository directory
        
    The repository must contain a valid repo.yaml file with required metadata.
    """
    try:
        cache_manager.add_repository(source)
    except RepositoryError as e:
        console.error(str(e))
        raise typer.Exit(1)

def list_repos() -> None:
    """List all cached repositories."""
    repos = cache_manager.list_repositories()
    
    if not repos:
        console.print("No repositories cached")
        return
        
    active_repo = cache_manager.get_active_repository()
    console.print("Cached repositories:")
    for name, info in repos.items():
        if name == active_repo:
            console.print(f"  * {name} (active)")
        else:
            console.print(f"  - {name}")

def repo_info(name: str) -> None:
    """Show detailed information about a repository.
    
    Args:
        name: Name of repository to show info for
    """
    repos = cache_manager.list_repositories()
    
    if name not in repos:
        console.error(f"Repository '{name}' not found")
        raise typer.Exit(1)
        
    info = repos[name]
    active_repo = cache_manager.get_active_repository()
    
    console.section("Repository Information", name)
    
    # Basic Information
    console.print("\n[bold]Basic Information[/bold]")
    console.print(f"Name: {info['name']}")
    console.print(f"Version: {info['version']}")
    console.print(f"Description: {info['description']}")
    console.print(f"Last Updated: {info['last_updated']}")
    
    # Maintainer Information
    console.print("\n[bold]Maintainer Information[/bold]")
    for maintainer in info['maintainer']:
        console.print(f"- {maintainer}")
        
    # Institution Information
    console.print("\n[bold]Institution[/bold]")
    console.print(info['institution'])
    
    # License Information
    console.print("\n[bold]License[/bold]")
    console.print(info['license'])
    
    # Status
    console.print("\n[bold]Status[/bold]")
    if name == active_repo:
        console.print("Active: Yes")
    else:
        console.print("Active: No")
        
    # Location
    console.print("\n[bold]Location[/bold]")
    console.print(f"Path: {info['path']}")

def select_repo(name: str) -> None:
    """Select a repository as active.
    
    Args:
        name: Name of repository to select
    """
    try:
        cache_manager.select_repository(name)
        console.success(f"Selected repository: {name}")
    except RepositoryError as e:
        console.error(str(e))
        raise typer.Exit(1)

def remove_repo(name: str) -> None:
    """Remove a repository from the cache.
    
    Args:
        name: Name of repository to remove
    """
    try:
        cache_manager.remove_repository(name)
        console.success(f"Removed repository: {name}")
    except RepositoryError as e:
        console.error(str(e))
        raise typer.Exit(1)

def update_repo(name: Optional[str] = None) -> None:
    """Update a repository from its source.
    
    Args:
        name: Optional name of repository to update. If not provided,
             updates the active repository.
    """
    try:
        if name is None:
            name = cache_manager.get_active_repository()
            if not name:
                console.error("No active repository")
                raise typer.Exit(1)
                
        cache_manager.update_repository(name)
        console.success(f"Updated repository: {name}")
    except RepositoryError as e:
        console.error(str(e))
        raise typer.Exit(1)

# Add commands
repo_app.command()(add_repo)
repo_app.command()(list_repos)
repo_app.command()(repo_info)
repo_app.command()(select_repo)
repo_app.command()(remove_repo)
repo_app.command()(update_repo)

# Export the app for use in main.py
app = repo_app 