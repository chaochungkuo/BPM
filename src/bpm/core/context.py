"""Context management for BPM.

This module provides a unified interface for accessing parameters from both
Project configuration and CLI arguments. It serves as the primary data provider
for templates and hook functions.
"""

import os
from typing import Any, Dict, Optional
from pathlib import Path
from bpm.core.project_bk import Project
from bpm.core.config import get_bpm_config


class ContextError(Exception):
    """Base exception for context errors."""
    pass


class Context:
    """Context manager for BPM parameters.
    
    This class provides unified access to parameters from both Project
    configuration and CLI arguments. It supports nested key access using
    dot notation and can optionally include environment variables.
    
    Example:
        >>> context = Context(cli_params={"output_dir": "results"})
        >>> context["output_dir"]  # Access CLI parameter
        'results'
        >>> context = Context(project=Project("project.yaml"))
        >>> context["section.key"]  # Access project parameter
        'value'
        >>> context = Context(environment=True)
        >>> context["PATH"]  # Access environment variable
        '/usr/bin:/bin'
    """
    
    def __init__(self, 
                 cli_params: Optional[Dict[str, Any]] = None,
                 project: Optional[Project] = None,
                 environment: bool = False):
        """Initialize context.
        
        Args:
            cli_params: Dictionary of CLI parameters
            project: Optional Project instance
            environment: Whether to include environment variables in context
        """
        self.cli_params = cli_params or {}
        self.project = project
        self.environment = {}
        if environment:
            self.environment = get_bpm_config("environment.yaml")
        
    def __getitem__(self, key: str) -> Any:
        """Get parameter value using dictionary access.
        
        Args:
            key: Parameter key, can use dot notation for nested keys
            
        Returns:
            Parameter value
            
        Raises:
            ContextError: If parameter is not found
        """
        # First check CLI parameters
        try:
            return self._get_nested_value(self.cli_params, key)
        except KeyError:
            pass
            
        # Then check project parameters
        if self.project:
            try:
                return self._get_nested_value(self.project.data, key)
            except KeyError:
                pass
                
        # Finally check environment variables
        if self.environment:
            try:
                return self._get_nested_value(self.environment, key)
            except KeyError:
                pass
                
        raise ContextError(f"Parameter not found: {key}")

    def _get_nested_value(self, d: Dict[str, Any], key: str) -> Any:
        """Get value from nested dictionary using dot notation.
        
        Args:
            d: Dictionary to search in
            key: Key using dot notation (e.g., 'tools.bclconvert')
            
        Returns:
            Value from nested dictionary
            
        Raises:
            KeyError: If key is not found
        """
        # Handle direct key access first
        if key in d:
            return d[key]
            
        # Then try nested access
        keys = key.split('.')
        value = d
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                raise KeyError(f"Key not found: {key}")
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """Get parameter value with default fallback.
        
        Args:
            key: Parameter key, can use dot notation for nested keys
            default: Default value if parameter is not found
            
        Returns:
            Parameter value or default
        """
        try:
            return self[key]
        except ContextError:
            return default
            
    def update(self, params: Dict[str, Any]) -> None:
        """Update CLI parameters.
        
        Args:
            params: Dictionary of parameters to update
        """
        self.cli_params.update(params)
        
    def get_all(self) -> Dict[str, Any]:
        """Get all available parameters.
        
        Returns:
            Dictionary containing all parameters from CLI, project, and environment
        """
        params = self.cli_params.copy()
        
        if self.project:
            # Get all project parameters
            project_params = self.project.data
            params.update(project_params)
            
        if self.environment:
            # Add environment variables
            params.update(self.environment)
        return params
        
    def validate_required(self, required_keys: list[str]) -> tuple[bool, list[str]]:
        """Validate that required parameters are present.
        
        Args:
            required_keys: List of required parameter keys
            
        Returns:
            Tuple of (all_required_present, list of missing keys)
        """
        missing = []
        for key in required_keys:
            try:
                self[key]
            except ContextError:
                missing.append(key)
                
        return len(missing) == 0, missing
