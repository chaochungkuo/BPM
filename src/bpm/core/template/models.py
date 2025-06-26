"""Template data models for BPM.

This module defines the core data structures for template information and sections.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from pydantic import BaseModel, Field, validator
from bpm.utils.path import host_solver


class StructureType(str, Enum):
    """Template structure type in project.yaml."""
    SUBSECTION = "subsection"
    FLAT = "flat"


class InputType(str, Enum):
    """Input field types for templates."""
    PATH = "path"
    BOOLEAN = "boolean"
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"


class TemplateInput(BaseModel):
    """Template input field model.
    
    This model represents an input field in a template configuration,
    including its type, requirements, and description.

    Attributes:
        type: Input field type (path, boolean, string, etc.)
        required: Whether the input is required
        default: Default value if not required
        description: Detailed description of the input
        resolve_with: Optional resolver function name
    """
    type: InputType
    required: bool = False
    default: Any = None
    description: str | None = None
    default_resolver: str | None = None

    @validator('default')
    def convert_path_default(cls, v, values):
        """Convert path default values using host_solver.
        
        Args:
            v: The value to validate
            values: Dictionary of other field values
            
        Returns:
            Converted path if type is path, otherwise original value
        """
        if values.get('type') == InputType.PATH and v is not None:
            try:
                return host_solver.from_hostpathstr_to_path(v)
            except ValueError:
                return v
        return v


class TemplateOutput(BaseModel):
    """Template output field model.
    
    This model represents an output field in a template configuration,
    including its type and description.

    Attributes:
        type: Output field type (path, string, etc.)
        description: Detailed description of the output
        resolve_with: Resolver function name to get the value
    """
    type: InputType
    description: str | None = None
    resolver: str | None = None
    value: Any = None

    @validator('value')
    def convert_path_value(cls, v, values):
        """Convert path values using host_solver.
        
        Args:
            v: The value to validate
            values: Dictionary of other field values
            
        Returns:
            Converted path if type is path, otherwise original value
        """
        if values.get('type') == InputType.PATH and v is not None:
            try:
                return host_solver.from_hostpathstr_to_path(v)
            except ValueError:
                return v
        return v


class TemplateConfig(BaseModel):
    """Template configuration model.
    
    This model represents the complete template configuration including
    metadata, inputs, outputs, and execution requirements.

    Attributes:
        section: Section name in project.yaml
        name: Template name
        structure: How to organize in project.yaml
        description: Template description
        inputs: Dictionary of input fields
        outputs: Dictionary of output fields
        post_hooks: List of post-hook function names
        required_commands: List of required command names
    """
    section: str
    name: str
    structure: StructureType = StructureType.SUBSECTION
    description: str | None = None
    inputs: Dict[str, TemplateInput] = Field(default_factory=dict)
    outputs: Dict[str, TemplateOutput] = Field(default_factory=dict)
    post_hooks: List[str] = Field(default_factory=list)
    required_commands: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now) 