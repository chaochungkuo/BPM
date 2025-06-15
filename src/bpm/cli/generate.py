# gpm/cli/generate.py

import typer
import inspect
import yaml
from pathlib import Path
from ..utils.path.paths import host_solver
from typing import Dict, Any, Callable
from ..core.controller import Controller
from ..utils.ui.console import BPMConsole

console = BPMConsole()
generate_app = typer.Typer(name="generate", 
                  help="Generate template files according to the customized context.")

def get_template_options(template_name: str) -> Dict[str, Any]:
    controller = Controller()
    template_path = controller.cache_manager.get_template_path(template_name)
    config_path = template_path / "template_config.yaml"

    if not config_path.exists():
        raise typer.Exit(f"[bold red]Template config not found:[/] {config_path}")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    options = {}
    for key, spec in config.get("inputs", {}).items():
        opt_type = {
            "boolean": bool,
            "integer": int,
            "float": float,
            "path": Path
        }.get(spec.get("type"), str)

        options[key] = {
            "default": None if spec.get("required") else spec.get("default"),
            "help": spec.get("description", key),
            "type": opt_type
        }
    description = config.get("description", "")
    return description, options

def make_generate_command(template_name: str,
                          template_desc: str,
                          template_options: Dict[str, Any]) -> Callable:
    def dynamic_generate(**kwargs):
        verbose = kwargs.pop("verbose", False)
        controller = Controller(verbose=verbose)
        project_path = kwargs.pop("project", None)
        output_path = kwargs.pop("output", None)

        if project_path:
            project_path = host_solver.from_hostpath_to_path(project_path)
            console.print(f"[bold green]Project file:[/] {project_path}")
            controller.load_project(project_path)

        if output_path:
            output_path = host_solver.from_hostpath_to_path(output_path)
            console.print(f"[bold green]Output directory:[/] {output_path}")

        params = {"template": template_name,
                  "project": project_path,
                  "output": output_path,
                  **kwargs}
        controller.collect_contexts(params=params)
        controller.generate_template(template_name=template_name,
                                     output_dir=output_path)

    # Create dynamic function signature
    parameters = [
        inspect.Parameter(
            "project",
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=typer.Option(
                None,
                "--project",
                "-p",
                help="Path to project.yaml. If not specified, will generate a new project in the output directory defined by --output."
            ),
            annotation=Path,
        ),
        inspect.Parameter(
            "output",
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=typer.Option(
                None,
                "--output",
                "-o",
                help="Output directory path. If --project is specified, the output directory will be under the project directory."
            ),
            annotation=str,
        ),
        inspect.Parameter(
            "verbose",
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=typer.Option(
                False,
                "--verbose",
                "-v",
                help="Show detailed logging information"
            ),
            annotation=bool,
        )
    ]

    for name, spec in template_options.items():
        option = typer.Option(
            default=spec["default"],
            help=spec["help"]
        )
        
        parameters.append(
            inspect.Parameter(
                name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=option,
                annotation=spec["type"],
            )
        )

    dynamic_generate.__doc__ = template_desc
    dynamic_generate.__signature__ = inspect.Signature(parameters)
    return dynamic_generate

def register_generate_commands():
    
    try:
        controller = Controller()
        template_list = controller.cache_manager.list_templates()
        for template in template_list:
            # console.print(f"Registering template: {template}")
            temp_desc, opts = get_template_options(template)
            cmd = make_generate_command(template, temp_desc, opts)
            generate_app.command(name=template)(cmd)
    except Exception as e:
        if "No configuration directory specified" in str(e):
            console.warning(f"No repository configured. Check bpm repo --help")
        else:
            console.error(f"{str(e)}")

# Register commands when module is imported
register_generate_commands()