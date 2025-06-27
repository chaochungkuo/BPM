from typing import Dict, Any
from pathlib import Path
import typer
import yaml
from bpm.core.controller import Controller


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


def get_template_outputs(template_name: str) -> Dict[str, Any]:
    controller = Controller()
    template_path = controller.cache_manager.get_template_path(template_name)
    config_path = template_path / "template_config.yaml"

    if not config_path.exists():
        raise typer.Exit(f"[bold red]Template config not found:[/] {config_path}")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    options = {}
    for key, spec in config.get("outputs", {}).items():
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
    return options