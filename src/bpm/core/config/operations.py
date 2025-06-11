"""Configuration operations for BPM.

This module provides the main ConfigLoader class and its operations for managing
configuration settings.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime

from bpm.core.config.models import MainConfig, AuthorConfig, PolicyConfig
from bpm.utils.ui.console import BPMConsole
from bpm.utils.io.file import load_yaml, save_yaml
from bpm.utils.path import path

# Configure rich console
console = BPMConsole()


class ConfigLoader:
    """Configuration loader for BPM.
    
    This class manages loading and saving configuration settings from YAML files.
    It provides methods for accessing and updating configuration values.

    Attributes:
        config_dir: Path to configuration directory
        configs: Dictionary of loaded configurations
    """
    __slots__ = ["config_dir", "configs", "verbose"]

    def __init__(self, config_dir: Optional[Path] = None, verbose: bool = False) -> None:
        """Initialize configuration loader.
        
        Args:
            config_dir: Optional path to configuration directory
        """
        self.config_dir = config_dir
        self.verbose = verbose
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.load_configs()

    def load_configs(self) -> None:
        """Load all YAML files from the configuration directory.
        
        Raises:
            ValueError: If no configuration directory is specified
            FileNotFoundError: If the directory doesn't exist
        """
        if not self.config_dir:
            raise ValueError("No configuration directory specified")
            
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Configuration directory not found: {self.config_dir}")
            
        # Load all YAML files in the directory
        for file_path in self.config_dir.glob("*.yaml"):
            try:
                config_name = file_path.stem
                self.configs[config_name] = load_yaml(file_path)
                if self.verbose:
                    console.info(f"Loaded configuration: {file_path}")
            except Exception as e:
                console.error(f"Failed to load {file_path.name}: {e}")

    def get_config(self, name: str) -> Dict[str, Any]:
        """Get configuration by name.
        
        Args:
            name: Configuration name (filename without extension)
            
        Returns:
            Configuration dictionary
            
        Raises:
            KeyError: If configuration not found
        """
        if name not in self.configs:
            raise KeyError(f"Configuration not found: {name}")
        return self.configs[name]

    def get_value(self, config_name: str, *keys: str) -> Any:
        """Get a value from configuration using dot notation.
        
        Args:
            config_name: Name of the configuration file
            *keys: Keys to traverse in the configuration
            
        Returns:
            Value at the specified path
            
        Raises:
            KeyError: If path doesn't exist
        """
        config = self.get_config(config_name)
        value = config
        
        for key in keys:
            if not isinstance(value, dict):
                raise KeyError(f"Invalid path: {'.'.join(keys)}")
            value = value[key]
            
        return value

    def set_value(self, config_name: str, value: Any, *keys: str) -> None:
        """Set a value in configuration using dot notation.
        
        Args:
            config_name: Name of the configuration file
            value: Value to set
            *keys: Keys to traverse in the configuration
            
        Raises:
            KeyError: If parent path doesn't exist
        """
        config = self.get_config(config_name)
        current = config
        
        # Navigate to the parent of the target
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            
        # Set the value
        current[keys[-1]] = value

    # def save_config(self, name: str) -> None:
    #     """Save configuration to file.
        
    #     Args:
    #         name: Configuration name to save
            
    #     Raises:
    #         KeyError: If configuration not found
    #     """
    #     if name not in self.configs:
    #         raise KeyError(f"Configuration not found: {name}")
            
    #     config_file = self.config_dir / f"{name}.yaml"
    #     with open(config_file, "w") as f:
    #         yaml.dump(self.configs[name], f)
    #     console.success(f"Saved configuration: {name}")

    def list_configs(self) -> list[str]:
        """List all loaded configurations.
        
        Returns:
            List of configuration names
        """
        return list(self.configs.keys())
    
    def get_author_info(self, author: str) -> str:
        """Get author information from configuration.
        
        Args:
            author: Author ID
            
        Returns:
            Dictionary of author information
        """
        available_authors = self.get_value("main", "authors")
        author_info = f"{available_authors[author]['name']}, " \
                      f"{available_authors[author]['affiliation']} " \
                      f"<{available_authors[author]['email']}>"
        return author_info