"""Generate command module."""
import typer
from pathlib import Path
from typing import Any, Dict, List, Optional
import shutil
import inspect
from rich import print
from bpm.core.template import Template
from bpm.core.context import Context
from bpm.core.project_bk import Project
from bpm.cli.helper import discover_templates, load_template_config

app = typer.Typer(help="Generate files/scripts from templates.")


def check_required_commands(required_commands: List[str]) -> None:
    """Check if all required commands are available."""
    missing_commands = []
    for cmd in required_commands:
        if not shutil.which(cmd):
            missing_commands.append(cmd)
    
    if missing_commands:
        raise typer.Exit(
            f"Required commands not found: {', '.join(missing_commands)}\n"
            "Please install them and try again."
        )

def create_command_function(config: Dict[str, Any], template_path: Path):
    """Create a command function with the specified parameters."""
    
    # Create parameter annotations and defaults
    annotations = {
        "project_yaml": Optional[Path],  # Add project-yaml parameter
        "force": bool  # Add force parameter
    }
    defaults = {
        "project_yaml": None,  # Default to None
        "force": False  # Default to False
    }
    
    for name, props in config["inputs"].items():
        # Set parameter type
        annotations[name] = str
        
        # Set default value
        if props.get("required", False):
            defaults[name] = ...
        else:
            defaults[name] = props.get("default", None)
    
    def command(**kwargs):
        """Template command implementation."""
        print(f"Rendering [bold blue]{config['name']}[/bold blue]:")
        print(f"{config['description']}")
        
        # Create context with optional project
        project = None
        if kwargs.get("project_yaml"):
            project = Project(kwargs["project_yaml"])
        context = Context(cli_params=kwargs, project=project, environment=True)
        
        # Create and execute template
        template = Template(template_name=config['section']+"."+config['name'])
        template.load_inputs(context)
        template.apply_hook_functions(context)
        
        # Check if output directory exists after hooks are applied
        output_dir = Path(context.get("output_dir"))
        if output_dir.exists():
            if kwargs.get("force"):
                print(f"[yellow]Output directory exists. Force overwriting...[/yellow]")
                shutil.rmtree(output_dir)
            else:
                raise typer.Exit(
                    f"Output directory '{output_dir}' already exists.\n"
                    "Use --force to overwrite it."
                )
        
        template.render(target_dir=context.get("output_dir"),
                       context=context.get_all())
    
    # Set the function's annotations and defaults
    command.__annotations__ = annotations
    
    # Create the function signature
    params = []
    for name, param_type in annotations.items():
        default = defaults[name]
        if name == "project_yaml":
            help_text = "Path to project.yaml file"
        elif name == "force":
            help_text = "Force overwrite existing output directory"
        else:
            help_text = config["inputs"][name].get("description", "")
            if default is not ... and name != "project_yaml" and "default" in config["inputs"][name]:
                help_text += f" [default: {default}]"
            
        param = inspect.Parameter(
            name,
            inspect.Parameter.KEYWORD_ONLY,
            default=typer.Option(default=default, help=help_text),
            annotation=param_type
        )
        params.append(param)
    
    command.__signature__ = inspect.Signature(parameters=params)
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
            help=config.get("description", f"Run {template_name} template")
        )(command_func)
        
except Exception as e:
    print(f"Error discovering templates: {e}", err=True) 