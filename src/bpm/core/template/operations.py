"""Template operations for BPM.

This module provides the main Template class and its operations for managing
bioinformatics project templates.
"""

import sys
from pathlib import Path
from typing import Any, Optional
from datetime import datetime
from rich.pretty import pprint
from pydantic import BaseModel
from ruamel.yaml import YAML
from jinja2 import Environment, FileSystemLoader, select_autoescape
import shutil

from bpm.core.config import ConfigLoader
from bpm.core.template.models import TemplateConfig, TemplateInput, TemplateOutput
from bpm.utils.ui.console import BPMConsole
from bpm.utils.path import path

# Configure YAML serializer
yaml = YAML()
yaml.default_flow_style = False
yaml.indent(sequence=4, offset=2)
yaml.preserve_quotes = True
yaml.explicit_start = True

# Configure rich console
console = BPMConsole()


class Template():
    """Main template class for managing bioinformatics project templates.
    
    This class manages all aspects of a template including configuration,
    inputs, outputs, and execution requirements. It provides methods for
    loading and saving template configurations.

    Attributes:
        config: Template configuration
        config_loader: ConfigLoader instance for configuration management
    """
    __slots__ = ["config", "template_dir", "config_loader", "verbose"]

    def __init__(self,
                 template_dir: Path,
                 config_loader: Optional[ConfigLoader] = None,
                 verbose: bool = False,
                 ) -> None:
        """Initialize a new template.
        
        Args:
            template_dir: Path to template directory
            config_loader: Optional ConfigLoader instance
        """
        self.config = TemplateConfig(
            section=template_dir.parent.name,
            name=template_dir.name
        )
        self.config_loader = config_loader
        self.verbose = verbose
        self.template_dir = template_dir
        template_yaml = template_dir / "template_config.yaml"
        self.read_from_file(template_yaml)

    def read_from_file(self, yaml_file: Path) -> "Template":
        """Read template from YAML file.
        
        Args:
            yaml_file: Path to YAML file
            
        Returns:
            Template instance
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            YAMLError: If the file contains invalid YAML
            ValueError: If the loaded data doesn't match expected structure
        """
        if self.verbose:
            console.info(f"Reading template configuration from {yaml_file}")
            
        with open(yaml_file) as f:
            data = yaml.load(f)
        
        if self.verbose:
            console.info("Template configuration loaded successfully")
            console.info(f"Template section: {data.get('section')}")
            console.info(f"Template name: {data.get('name')}")
            if 'inputs' in data:
                console.info(f"Number of inputs: {len(data['inputs'])}")
            if 'outputs' in data:
                console.info(f"Number of outputs: {len(data['outputs'])}")
        
        # Update template configuration from loaded data
        self.config = TemplateConfig(**data)
        return self

    def export_as_dict(self) -> dict[str, Any]:
        """Export template data as a dictionary.
        
        This method converts all template data into a dictionary format suitable
        for serialization or external use.
        
        Returns:
            dict[str, Any]: Dictionary containing all template data
        """
        if self.verbose:
            console.info("Exporting template configuration to dictionary")
        return self._serialize_to_dict()

    def _serialize_to_dict(self) -> dict[str, Any]:
        """Serialize template to dictionary.
        
        Internal method used for YAML serialization. Consider using
        export_as_dict() for external use.
        
        Returns:
            Dictionary representation of template
        """
        if self.verbose:
            console.info("Serializing template configuration")
        return self._convert_to_serializable(self.config)
    
    def _convert_to_serializable(self, obj: Any) -> Any:
        """Convert a value to YAML-compatible format.
        
        Args:
            obj: Object to convert
            
        Returns:
            Converted object
        """
        if obj is None:
            return None
        if isinstance(obj, BaseModel):
            if self.verbose:
                console.info(f"Converting Pydantic model: {obj.__class__.__name__}")
            return self._convert_to_serializable(obj.model_dump())
        if isinstance(obj, Path):
            if self.verbose:
                console.info(f"Converting Path to string: {obj}")
            return str(obj)
        if isinstance(obj, datetime):
            if self.verbose:
                console.info(f"Converting datetime to string: {obj}")
            return obj.strftime("%Y-%m-%d %H:%M")  # Format without seconds
        if isinstance(obj, dict):
            if not obj:  # Empty dict
                return None
            if self.verbose:
                console.info(f"Converting dictionary with {len(obj)} items")
            return {k: self._convert_to_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            if not obj:  # Empty list
                return None
            if self.verbose:
                console.info(f"Converting list with {len(obj)} items")
            return [self._convert_to_serializable(v) for v in obj]
        return obj

    def save_to_file(self) -> None:
        """Save template configuration to template_config.yaml."""
        if self.verbose:
            console.info("Saving template configuration to file")
            
        # Convert to dictionary
        template_dict = self._serialize_to_dict()
        
        # Ensure template directory exists
        template_dir = Path(self.config.section) / self.config.name
        if self.verbose:
            console.info(f"Creating template directory: {template_dir}")
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        output_file = template_dir / "template_config.yaml"
        if self.verbose:
            console.info(f"Writing configuration to {output_file}")
        with open(output_file, "w") as f:
            yaml.dump(template_dict, f)
        if self.verbose:
            console.info("Template configuration saved successfully")
    
    def render(self, context: dict[str, Any], output_dir: Path) -> None:
        """Render all template files using Jinja2 and write to target_dir.
        
        Args:
            context: Dictionary containing template variables
            output_dir: Output directory path
        Raises:
            SystemExit: If output directory is not specified in context
        """
        if self.verbose:
            console.info("Starting template rendering process")
            console.info(f"Template directory: {self.template_dir}")
            console.info(f"Context keys: {list(context.keys())}")
            console.info(f"Output directory: {output_dir}")
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        template_root = self.template_dir 
        # console.print(context)
            
        env = Environment(
            loader=FileSystemLoader(str(template_root)),
            autoescape=select_autoescape(),
            keep_trailing_newline=True,  # Preserve trailing newlines
            trim_blocks=True,            # Remove first newline after a block
            lstrip_blocks=True          # Remove whitespace before blocks
        )
        
        if self.verbose:
            console.info("Jinja2 environment configured")
            
        for file_path in template_root.rglob("*"):
            if file_path.is_dir() or file_path.name == "template_config.yaml":
                if self.verbose:
                    console.info(f"Skipping {file_path}")
                continue

            rel_path = file_path.relative_to(template_root)
            out_path = output_dir / rel_path
            console.info(f"Output path: {out_path}")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.verbose:
                console.info(f"Processing file: {rel_path}")
                console.info(f"Output path: {out_path}")

            # Try rendering as text, fallback to copy if binary
            try:
                template = env.get_template(str(rel_path))
                if self.verbose:
                    console.info(f"Rendering template: {rel_path}")
                rendered = template.render(context)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(rendered)
                if self.verbose:
                    console.info(f"Successfully rendered: {rel_path}")
            except Exception as e:
                if self.verbose:
                    console.warning(f"Failed to render {rel_path} as template: {str(e)}")
                    console.info(f"Copying file as binary: {rel_path}")
                # If it's a binary file or not a Jinja2 template, just copy it
                shutil.copy2(file_path, out_path)
                
        if self.verbose:
            console.info("Template rendering completed")
        