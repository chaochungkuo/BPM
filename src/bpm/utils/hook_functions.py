import importlib.util
import sys
from typing import Callable
from pathlib import Path

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