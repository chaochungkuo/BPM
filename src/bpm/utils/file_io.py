"""File I/O utilities for BPM.

This module provides utility functions for reading and writing YAML and TOML files.
It includes type hints and error handling for safe file operations.
"""

import logging
from pathlib import Path
from typing import Any, TypeVar, cast

import tomli
import tomli_w
from rich.console import Console
from rich.panel import Panel
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

# Configure logging
logger = logging.getLogger(__name__)

# Configure rich console
console = Console()

# Configure YAML serializer
yaml = YAML()
yaml.default_flow_style = False
yaml.indent(sequence=4, offset=2)
yaml.preserve_quotes = True
yaml.explicit_start = True

T = TypeVar("T")


def _print_error(title: str, message: str, error: Exception | None = None) -> None:
    """Print formatted error message.
    
    Args:
        title: Error title
        message: Error message
        error: Optional exception for additional details
    """
    error_msg = f"{message}\n\nDetails: {str(error)}" if error else message
    console.print(Panel(error_msg, title=title, border_style="red"))
    logger.error(f"{title}: {message}", exc_info=error)


def load_yaml(file_path: Path | str, expected_type: type[T] | None = None) -> T:
    """Load data from a YAML file.
    
    Args:
        file_path: Path to the YAML file
        expected_type: Optional type to cast the loaded data to
        
    Returns:
        Loaded data, optionally cast to expected_type
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        YAMLError: If the file contains invalid YAML
        ValueError: If the loaded data doesn't match expected_type
    """
    try:
        with open(file_path, "r") as f:
            data = yaml.load(f)
            
        if expected_type is not None:
            if not isinstance(data, expected_type):
                error_msg = f"Loaded data is of type {type(data)}, expected {expected_type}"
                _print_error("Type Error", error_msg)
                raise ValueError(error_msg)
            return cast(T, data)
        return cast(T, data)
    except FileNotFoundError as e:
        _print_error("File Not Found", f"YAML file not found: {file_path}", e)
        raise
    except YAMLError as e:
        _print_error("Invalid YAML", f"Invalid YAML in {file_path}", e)
        raise


def save_yaml(data: Any, file_path: Path | str) -> None:
    """Save data to a YAML file.
    
    Args:
        data: Data to save
        file_path: Path to save the YAML file to
        
    Raises:
        OSError: If the file cannot be written
        YAMLError: If the data cannot be serialized to YAML
    """
    try:
        with open(file_path, "w") as f:
            yaml.dump(data, f)
    except OSError as e:
        _print_error("Write Error", f"Failed to write YAML file {file_path}", e)
        raise
    except YAMLError as e:
        _print_error("Serialization Error", "Failed to serialize data to YAML", e)
        raise


def load_toml(file_path: Path | str, expected_type: type[T] | None = None) -> T:
    """Load data from a TOML file.
    
    Args:
        file_path: Path to the TOML file
        expected_type: Optional type to cast the loaded data to
        
    Returns:
        Loaded data, optionally cast to expected_type
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        tomli.TOMLDecodeError: If the file contains invalid TOML
        ValueError: If the loaded data doesn't match expected_type
    """
    try:
        with open(file_path, "rb") as f:
            data = tomli.load(f)
            
        if expected_type is not None:
            if not isinstance(data, expected_type):
                error_msg = f"Loaded data is of type {type(data)}, expected {expected_type}"
                _print_error("Type Error", error_msg)
                raise ValueError(error_msg)
            return cast(T, data)
        return cast(T, data)
    except FileNotFoundError as e:
        _print_error("File Not Found", f"TOML file not found: {file_path}", e)
        raise
    except tomli.TOMLDecodeError as e:
        _print_error("Invalid TOML", f"Invalid TOML in {file_path}", e)
        raise


def save_toml(data: Any, file_path: Path | str) -> None:
    """Save data to a TOML file.
    
    Args:
        data: Data to save
        file_path: Path to save the TOML file to
        
    Raises:
        OSError: If the file cannot be written
        TypeError: If the data cannot be serialized to TOML
    """
    try:
        with open(file_path, "wb") as f:
            tomli_w.dump(data, f)
    except OSError as e:
        _print_error("Write Error", f"Failed to write TOML file {file_path}", e)
        raise
    except TypeError as e:
        _print_error("Serialization Error", "Failed to serialize data to TOML", e)
        raise 