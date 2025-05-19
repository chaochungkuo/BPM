"""Configuration management module for BPM.

This module provides functionality to access configuration values from YAML files
using dot notation. It uses importlib.resources to locate config files within the
package structure, making it work reliably in both development and installed environments.
"""

import yaml
from collections.abc import Mapping
from pathlib import Path
import importlib.resources
from typing import Any, Optional, Dict


def flatten_dict(d: Dict[str, Any], parent_key: str = '') -> Dict[str, Any]:
    """Flatten a nested dictionary using dot notation.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for nested dictionaries
        
    Returns:
        Flattened dictionary with dot notation keys
    """
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, Mapping):
            items.update(flatten_dict(v, new_key))
        else:
            items[new_key] = v
    return items


def get_bpm_config(filename: str, key: Optional[str] = None) -> Any:
    """Access nested config values using dot notation.

    This function loads a YAML config file and retrieves a value using dot notation
    to navigate nested dictionaries. For example, 'templates_dir.default' would
    access the 'default' key within the 'templates_dir' dictionary.
    
    If no key is provided, returns the entire configuration dictionary flattened
    using dot notation for nested keys.

    Args:
        filename: Name of the config file to load (e.g., 'main.yaml')
        key: Optional dot-notation path to the config value (e.g., 'templates_dir.default').
             If None, returns the entire config dictionary flattened.

    Returns:
        The config value at the specified path, or the entire flattened config if no key provided.
        Can be any YAML-compatible type (str, int, float, bool, list, dict, etc.)

    Raises:
        FileNotFoundError: If the config file doesn't exist in the package's config directory
        KeyError: If any part of the dot-notation path is missing in the config
        yaml.YAMLError: If the config file contains invalid YAML

    Example:
        >>> get_bpm_config("main.yaml")  # Get entire flattened config
        {'templates_dir.default': 'templates', 'template_status.statuses.completed': 'completed', ...}
        >>> get_bpm_config("main.yaml", "templates_dir.default")
        'templates'
        >>> get_bpm_config("main.yaml", "template_status.statuses.completed")
        'completed'
    """
    try:
        # Use importlib.resources to locate the config file
        config_path = Path(importlib.resources.files("bpm.config")) / filename
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {filename}")
            
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            
        # Return flattened config if no key provided
        if key is None:
            return flatten_dict(config)
            
        keys = key.split(".")
        value = config
        for k in keys:
            if isinstance(value, Mapping) and k in value:
                value = value[k]
            else:
                raise KeyError(f"Config key not found: {'.'.join(keys)} (missing: '{k}')")
        return value
        
    except (FileNotFoundError, KeyError, yaml.YAMLError):
        # Re-raise specific errors
        raise
    except Exception as e:
        # Wrap unexpected errors
        raise RuntimeError(f"Error accessing config {filename}: {e}")