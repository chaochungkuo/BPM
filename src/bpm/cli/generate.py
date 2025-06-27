# gpm/cli/generate.py
import sys

import typer
import inspect
import yaml
from pathlib import Path
from ..utils.path.paths import host_solver
from typing import Dict, Any, Callable
from ..core.controller import Controller
from ..utils.ui.console import BPMConsole
from .util import get_template_options

console = BPMConsole()
generate_app = typer.Typer(name="generate", 
                  help="Generate template files according to the customized context.")

def make_generate_command(template_name: str,
                          template_desc: str,
                          template_options: Dict[str, Any]) -> Callable:
    def dynamic_generate(**kwargs):
        verbose = kwargs.pop("verbose", False)
        controller = Controller(verbose=verbose)
        project_path = kwargs.pop("project", None)
        output_path = kwargs.pop("output", None)
        force_output_dir = False
        
        if project_path:
            project_path = project_path.resolve()
            console.print(f"[bold green]Project file:[/] {project_path}")
            controller.load_project(project_path)
            if output_path:
                console.info("Output directory is specified, but project file is specified. Ignoring output directory.")
                output_path = None
        else:
            if output_path:
                output_path = host_solver.from_hostpathstr_to_path(output_path)
                console.print(f"[bold green]Output directory:[/] {output_path}")
                controller.create_project(project_path=output_path)
                console.print(f"[bold green]Create a new project in:[/] {output_path}")
                force_output_dir = True
            else:
                console.error("Both project file and output directory are not specified. Please specify one of them.")
                sys.exit(1)

        params = {"template": template_name,
                  "project": project_path,
                  "output": output_path,
                  **kwargs}
        controller.collect_contexts(params=params)
        controller.generate_template(template_name=template_name,
                                     output_dir=output_path,
                                     force_output_dir=force_output_dir)

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