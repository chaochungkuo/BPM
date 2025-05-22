"""Initialize command module."""
import typer
from rich import print
from pathlib import Path
import re
from datetime import datetime
import yaml
from typing import Optional
from bpm.core.config import get_bpm_config
from bpm.core.project import Project
from bpm.utils.paths import to_host_path

def validate_project_name(name: str) -> tuple[bool, str]:
    """Validate project name format and extract date.
    
    Args:
        name: Project name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Expected format: YYMMDD_name1_name2_institute_application
    pattern = r'^(\d{6})_([a-zA-Z0-9]+)_([a-zA-Z0-9]+)_([a-zA-Z0-9]+)_([a-zA-Z0-9]+)$'
    match = re.match(pattern, name)
    
    if not match:
        return False, "Project name must follow format: YYMMDD_name1_name2_institute_application"
    
    # Validate date
    date_str = match.group(1)
    try:
        date = datetime.strptime(date_str, '%y%m%d')
        if date > datetime.now():
            return False, "Project date cannot be in the future"
    except ValueError:
        return False, "Invalid date format in project name"
    
    return True, ""

def create_project_yaml(
    project_dir: Path,
    name: str,
    author: Optional[str] = None
) -> None:
    """Create project.yaml file with project information.
    
    Args:
        project_dir: Project directory path
        name: Project name
        author: Author name (optional)
    """
    # Extract date from project name
    labels = name.split("_")
    # date = datetime.strptime(labels[0], '%y%m%d')
    
    # Create and initialize project
    project_path = project_dir / "project.yaml"
    project = Project()
    
    # Update project information
    project.update_value("project.date", labels[0])
    project.update_value("project.name", labels[1])
    project.update_value("project.institute", labels[3])
    project.update_value("project.application", labels[4])
    project.update_value("project.project_dir", to_host_path(project_dir))
    
    authors = get_bpm_config("main.yaml", "authors")
    author_list = []
    if author:
        author = author.split(",")
        for person in author:
            if person not in authors:
                raise ValueError(f"Author {author} not found in main.yaml")
            else:
                author_info = authors[person]
                info = f"{author_info['name']}, {author_info['affiliation']} <{author_info['email']}>"
                author_list.append(info)
        project.update_value("project.authors", author_list)
    
    # Save project
    project.save(project_path)

def init(
    name: str = typer.Option(..., help="Project name (format: YYMMDD_name1_name2_institute_application)"),
    author: Optional[str] = typer.Option(None, help="Author name from main.yaml"),
):
    """Initialize a new BPM project."""
    # Validate project name
    is_valid, error_msg = validate_project_name(name)
    if not is_valid:
        print(f"[red]Error: {error_msg}[/red]")
        raise typer.Exit(1)
    
    # Create project directory
    project_dir = Path.cwd().resolve() / name
    if project_dir.exists():
        print(f"[red]Error: Project directory '{name}' already exists[/red]")
        raise typer.Exit(1)
    
    # try:
    # Create project directory
    project_dir.mkdir(parents=True, exist_ok=False)
    if not project_dir.exists():
        raise RuntimeError(f"Failed to create project directory: {project_dir}")
        
    print(f"[green]Created project directory: {project_dir}[/green]")
    
    # Create project.yaml
    create_project_yaml(project_dir, name, author)
    print(f"[green]Created project.yaml with project information[/green]")
    
    print(f"\n[bold green]Project '{name}' initialized successfully![/bold green]")
    print(f"Next steps:")
    print(f"1. Review project.yaml in {project_dir}")
    print(f"2. Add your project parameters")
    print(f"3. Add your first template by checking [blue]bpm generate --help[/blue]")
    
    # except Exception as e:
    #     print(f"[red]Error initializing project: {str(e)}[/red]")
    #     if project_dir.exists():
    #         import shutil
    #         shutil.rmtree(project_dir)
    #     raise typer.Exit(1)

# Export init function
__all__ = ['init'] 