"""Update command module."""
import typer
from pathlib import Path
from typing import Any, Dict, List
from rich import print
from bpm.core.project import Project
from bpm.cli.helper import discover_templates, load_template_config, \
    locate_project_yaml, resolve_parameter_value
import sys
from bpm.core.config import get_bpm_config
from datetime import datetime
app = typer.Typer(help="Update the project.yaml file with the latest status of the template.")


def create_command_function(config: Dict[str, Any], template_path: Path):
    """Create a command function for updating project.yaml with template outputs."""
    
    def command():
        """Template update implementation."""
        print(f"Updating {config['name']} ({config['description']})")
        
        # Load project.yaml
        project_yaml = locate_project_yaml()
        if project_yaml is None:
            print("project.yaml not found.")
            sys.exit(0)
        else:
            project = Project(project_yaml)
            
            # Create template instance
            # template = Template(template_name=f"{config['section']}.{config['name']}")
            
            # Get output paths from project.yaml
            resolved_params = {}
            for name, props in config["outputs"].items():
                value = resolve_parameter_value(name, props, {})
                resolved_params[name] = value
                print(f"  {name}: {value}")
            
            for name, value in resolved_params.items():
                
                project.update_value(".".join([config["section"],
                                               config["name"],
                                               name]), str(value))
            project.update_value(".".join([config["section"],
                                               config["name"],
                                               "status"]), 
                                 get_bpm_config("main.yaml", "template_status.statuses.completed"))
            project.update_value(".".join([config["section"],
                                               config["name"],
                                               "updated_at"]), 
                                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            project.save(str(project_yaml))
            print("\nUpdated outputs in project.yaml:")
    
    return command

# Discover and register all templates
try:
    for section, template_name, template_path in discover_templates():
        # Load the template configuration
        config = load_template_config(template_path)
        
        # Create the command function
        command_func = create_command_function(config, template_path)
        
        # Register the command with its name and help text
        app.command(
            f"{section}.{template_name}",
            help=config.get("description", f"Update {template_name} template outputs")
        )(command_func)
        
except Exception as e:
    print(f"Error discovering templates: {e}", err=True) 