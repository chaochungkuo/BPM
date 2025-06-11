"""Helper functions for BPM core functionality.

This module provides utility functions used across BPM core components.
"""

import os
from pathlib import Path
from typing import Optional

def get_cachedir() -> Path:
    """Get the BPM cache directory path.
    
    This function checks for the BPM_CACHE environment variable first.
    If not set, returns the default cache path in the user's home directory.
    
    Returns:
        Path to the BPM cache directory
        
    Example:
        >>> cache_dir = get_cachedir()
        >>> print(cache_dir)
        /home/user/.cache/bpm  # or whatever the path is
    """
    # Check for BPM_CACHE environment variable
    cache_path = os.environ.get("BPM_CACHE")
    
    if cache_path:
        return Path(cache_path)
    
    # Default cache path in user's home directory
    return Path.home() / ".cache" / "bpm"

def flatten_dict(d: dict) -> dict:
    """Flatten a nested dictionary."""
    flat = {}
    for key, value in d.items():
        if isinstance(value, dict):
            flat.update(flatten_dict(value))
        else:
            flat[key] = value
    return flat

def nested_flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten a nested dictionary using dot notation for nested keys.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for nested dictionaries
        sep: Separator to use between nested keys (default: ".")
        
    Returns:
        Flattened dictionary with dot-separated keys
        
    Example:
        >>> d = {"a": {"b": 1, "c": {"d": 2}}}
        >>> nested_flatten_dict(d)
        {'a.b': 1, 'a.c.d': 2}
    """
    items = []
    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict) and value:  # Check if value is non-empty dict
            items.extend(nested_flatten_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
            
    return dict(items)