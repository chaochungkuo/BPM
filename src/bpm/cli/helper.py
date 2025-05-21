import yaml
from pathlib import Path
from typing import Any, Dict, List, Tuple
from rich import print
import os


def get_templates_dir() -> Path:
    """Get the templates directory path."""
    # Get the directory containing this file
    current_dir = Path(__file__).parent
    # Go up to src/bpm and then to templates
    return current_dir.parent / "templates"


def discover_templates() -> List[Tuple[str, str, Path]]:
    """Discover all templates in the templates directory.
    
    Returns:
        List of tuples containing (section, template_name, template_path)
    """
    templates_dir = get_templates_dir()
    if not templates_dir.exists():
        raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

    templates = []
    # Iterate through sections (e.g., demultiplexing, processing)
    for section_dir in templates_dir.iterdir():
        if not section_dir.is_dir():
            continue
            
        # Iterate through templates in each section
        for template_dir in section_dir.iterdir():
            if not template_dir.is_dir():
                continue
                
            config_path = template_dir / "template_config.yaml"
            if config_path.exists():
                templates.append((
                    section_dir.name,  # section name
                    template_dir.name,  # template name
                    config_path  # full path to config
                ))
    
    return templates

def load_template_config(template_yaml: Path) -> Dict[str, Any]:
    """Load template configuration from YAML file."""
    try:
        with open(template_yaml, 'r') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid template config in {template_yaml}: {e}")

def locate_project_yaml() -> Path | None:
    """Locate the project.yaml file in the current directory and its subdirectories.
    
    Returns:
        Path to the first project.yaml file found, or None if no file is found
    """
    current_dir = Path.cwd()
    project_files = []
    
    # Walk through all subdirectories
    for root, _, files in os.walk(current_dir):
        if "project.yaml" in files:
            project_files.append(Path(root) / "project.yaml")
    
    if not project_files:
        return None
    
    if len(project_files) > 1:
        print("Warning: Multiple project.yaml files found:")
        for file in project_files:
            print(f"  - {file}")
        print(f"Using: {project_files[0]}")
    
    return project_files[0]