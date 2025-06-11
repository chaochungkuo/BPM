"""File I/O utilities for BPM.

This module provides utilities for file operations including YAML handling.
"""

import warnings
from pathlib import Path
from typing import Any

import yaml
from ruamel.yaml import YAML

# Configure YAML serializer
yaml_serializer = YAML()
yaml_serializer.default_flow_style = False
yaml_serializer.indent(sequence=4, offset=2)
yaml_serializer.preserve_quotes = True
yaml_serializer.explicit_start = True

def load_yaml(file_path: Path) -> dict[str, Any]:
    """Load YAML file.
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        Dictionary containing YAML data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If file contains invalid YAML
    """
    with open(file_path) as f:
        return yaml.safe_load(f)

def save_yaml(data: dict[str, Any], file_path: Path) -> None:
    """Save data to YAML file.
    
    Args:
        data: Data to save
        file_path: Path to save YAML file
        
    Raises:
        yaml.YAMLError: If data cannot be serialized to YAML
    """
    with open(file_path, "w") as f:
        yaml_serializer.dump(data, f) 