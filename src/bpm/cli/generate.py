# gpm/cli/generate.py

import typer
import inspect
import yaml
from pathlib import Path
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

        if project_path:
            project_path = Path(project_path).resolve()
            console.print(f"[bold green]Project file:[/] {project_path}")
            controller.load_project(project_path)

        params = {"template": template_name, "project": project_path, **kwargs}
        controller.collect_contexts(params=params)
        controller.load_template(template_name=template_name)

    # Create dynamic function signature
    parameters = [
        inspect.Parameter(
            "project",
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=typer.Option(
                None,
                "--project",
                "-p",
                help="Path to project.yaml. If not specified, will generate a new project in the output directory defined by --output-dir."
            ),
            annotation=Path,
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
        for template in controller.cache_manager.list_templates():
            console.print(f"Registering template: {template}")
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