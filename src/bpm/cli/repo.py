"""Repository management commands.

This module provides the command-line interface for managing BPM repositories.
"""

from pathlib import Path
import typer
from typing import Optional

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

def add_repo(
    source: str,
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed logging information"
    )
) -> None:
    """Add a repository to the cache.
    
    Args:
        source: Path to repository directory
        verbose: Show detailed logging information
        
    The repository must contain a valid repo.yaml file with required metadata.
    """
    try:
        if verbose:
            console.info(f"Adding repository from {source}")
            
        cache_manager.add_repository(source)
        
        if verbose:
            console.info("Repository added successfully")
            
    except RepositoryError as e:
        console.error(str(e))
        raise typer.Exit(1)

def list_repos(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed logging information"
    )
) -> None:
    """List all cached repositories.
    
    Args:
        verbose: Show detailed logging information
    """
    if verbose:
        console.info("Listing cached repositories")
        
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
            
    if verbose:
        console.info(f"Found {len(repos)} repositories")

def repo_info(
    name: str,
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed logging information"
    )
) -> None:
    """Show detailed information about a repository.
    
    Args:
        name: Name of repository to show info for
        verbose: Show detailed logging information
    """
    if verbose:
        console.info(f"Getting information for repository: {name}")
        
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
    
    if verbose:
        console.info("Repository information displayed successfully")

def select_repo(
    name: str,
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed logging information"
    )
) -> None:
    """Select a repository as active.
    
    Args:
        name: Name of repository to select
        verbose: Show detailed logging information
    """
    try:
        if verbose:
            console.info(f"Selecting repository: {name}")
            
        cache_manager.select_repository(name)
        console.success(f"Selected repository: {name}")
        
        if verbose:
            console.info("Repository selection completed")
            
    except RepositoryError as e:
        console.error(str(e))
        raise typer.Exit(1)

def remove_repo(
    name: str,
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed logging information"
    )
) -> None:
    """Remove a repository from the cache.
    
    Args:
        name: Name of repository to remove
        verbose: Show detailed logging information
    """
    try:
        if verbose:
            console.info(f"Removing repository: {name}")
            
        cache_manager.remove_repository(name)
        console.success(f"Removed repository: {name}")
        
        if verbose:
            console.info("Repository removal completed")
            
    except RepositoryError as e:
        console.error(str(e))
        raise typer.Exit(1)

def update_repo(
    name: Optional[str] = None,
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed logging information"
    )
) -> None:
    """Update a repository from its source.
    
    Args:
        name: Optional name of repository to update. If not provided,
             updates the active repository.
        verbose: Show detailed logging information
    """
    try:
        if name is None:
            name = cache_manager.get_active_repository()
            if not name:
                console.error("No active repository")
                raise typer.Exit(1)
                
        if verbose:
            console.info(f"Updating repository: {name}")
            
        cache_manager.update_repository(name)
        console.success(f"Updated repository: {name}")
        
        if verbose:
            console.info("Repository update completed")
            
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