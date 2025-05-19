import yaml
from pathlib import Path
from typing import Any, Dict, List, Tuple, Callable
import importlib.util
import sys
from rich import print
from bpm.utils.paths import resolve_path
import os


def get_templates_dir() -> Path:
    """Get the templates directory path."""
    # Get the directory containing this file
    current_dir = Path(__file__).parent
    # Go up to src/bpm and then to templates
    return current_dir.parent / "templates"

def get_hook_functions_dir() -> Path:
    """Get the hook functions directory path."""
    # Get the directory containing this file
    current_dir = Path(__file__).parent
    # Go up to src/bpm and then to hook_functions
    return current_dir.parent / "hook_functions"

def load_hook_function(function_name: str) -> Callable:
    """Load a hook function from the hook_functions directory.
    
    Args:
        function_name: Name of the hook function (without .py extension)
        
    Returns:
        The loaded hook function
        
    Raises:
        ImportError: If the hook function cannot be loaded
        AttributeError: If the hook function doesn't exist in the module
    """
    hook_dir = get_hook_functions_dir()
    hook_file = hook_dir / f"{function_name}.py"
    
    if not hook_file.exists():
        raise ImportError(f"Hook function not found: {function_name}")
    
    # Load the module
    spec = importlib.util.spec_from_file_location(function_name, hook_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load hook function: {function_name}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[function_name] = module
    spec.loader.exec_module(module)
    
    # Get the function (assuming it has the same name as the file)
    if not hasattr(module, function_name):
        raise AttributeError(f"Function {function_name} not found in {hook_file}")
    
    return getattr(module, function_name)

def resolve_parameter_value(param_name: str, param_config: Dict[str, Any], params: Dict[str, Any]) -> Any:
    """Resolve a parameter value using hook functions if specified.
    
    Args:
        param_name: Name of the parameter
        param_config: Parameter configuration from template
        params: Current parameter values
        
    Returns:
        Resolved parameter value
    """
    value = params.get(param_name)
    
    # If there's a resolve_with hook, apply it
    if "resolve_with" in param_config:
        try:
            hook_function = load_hook_function(param_config["resolve_with"])
            value = hook_function(params)
            print(f"  Resolved {param_name} using {param_config['resolve_with']}: {value}")
        except Exception as e:
            print(f"Warning: Could not resolve {param_name} using {param_config['resolve_with']}: {e}")
    elif param_config["type"] == "path":
        value = resolve_path(value)
        
    return value

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