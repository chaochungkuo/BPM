"""Template management for BPM.

This module handles template operations including:
- Loading and validating templates
- Processing inputs from project.yaml
- Rendering template files
- Registering outputs back to project.yaml

Example:
    >>> template = Template("demultiplexing.bclconvert")
    >>> template.load_inputs(context)
    >>> template.render("output_dir")
    >>> template.register_output("project.yaml")
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import yaml
import jinja2
from datetime import datetime
from importlib.resources import as_file, files
from bpm.core.project import Project
from bpm.core.config import get_bpm_config
from bpm.core.context import Context
from bpm.utils.check_tools import check_programs


class TemplateError(Exception):
    """Base exception for template errors."""
    pass

class TemplateValidationError(TemplateError):
    """Exception for template validation errors."""
    pass

class TemplateRenderError(TemplateError):
    """Exception for template rendering errors."""
    pass

class TemplateNotFoundError(TemplateError):
    """Exception for when template is not found in any directory."""
    pass

class Template:
    """Handle template operations.
    
    This class manages template operations including:
    - Loading and validating templates
    - Processing inputs from project.yaml
    - Rendering template files
    - Registering outputs back to project.yaml
    
    Example:
        >>> template = Template("demultiplexing.bclconvert")
        >>> template.load_inputs(context)
        >>> template.render("output_dir")
        >>> template.register_output("project.yaml")
    """
    
    def __init__(self, template_name: str):
        """Initialize template.
        
        Args:
            template_name: Full name of the template (e.g., "demultiplexing.bclconvert")
        
        Raises:
            TemplateError: If template is not found or invalid
        """
        self.full_name = template_name
        self.section, self.name = template_name.split(".", 1)
        self.template_dir = self._find_template_dir(template_name)
        
        if not self.template_dir:
            raise TemplateNotFoundError(f"Template not found: {template_name}")
        
        # Load template configuration
        self.config = self._load_config()
        
        # Initialize Jinja2 environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=False
        )
        
        # Track template files
        self.files: Set[Path] = set()
        self._register_files()
    
    def _find_template_dir(self, template_name: str) -> Optional[Path]:
        """Find the template directory for a given template name.
        
        Args:
            template_name: Name of the template in format 'section.template'
            
        Returns:
            Path to the template directory if found, None otherwise
        """
        section, template = template_name.split(".", 1)
        
        # Get template directories from config
        template_config = get_bpm_config("main.yaml", "templates_dir")
        template_dirs = []
        
        # Add default template directory
        if not template_config.get("user_only", False):
            template_dirs.append(
                files(template_config["default"])._paths[0])
        
        # Add user template directories
        for user_dir in template_config.get("user", []):
            template_dirs.append(Path(user_dir))
        # Search for template in each directory
        for template_dir in template_dirs:
            # First try section/template path
            template_path = template_dir / Path(section) / Path(template)
            if template_path.exists():
                return template_path
            
            # Then try just the template name
            template_path = template_dir / Path(template)
            if template_path.exists():
                return template_path
        
        return None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load template configuration.
        
        Returns:
            Dictionary containing template configuration
        
        Raises:
            TemplateError: If template_config.yaml is not found or invalid
        """
        config_path = self.template_dir / "template_config.yaml"
        try:
            with open(config_path) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise TemplateError(f"template_config.yaml not found in template: {self.name}")
        except yaml.YAMLError as e:
            raise TemplateError(f"Invalid template_config.yaml in template {self.name}: {e}")
    
    def _register_files(self) -> None:
        """Register all files in the template directory."""
        for root, _, files in os.walk(self.template_dir):
            for file in files:
                if file != "template_config.yaml":  # Skip template_config file
                    self.files.add(Path(root) / file)
    
    def load_inputs(self, context: Context) -> None:
        """Load and validate inputs from context.
        
        Args:
            context: Context object containing input values
        
        Raises:
            TemplateError: If inputs are invalid or missing
        """
        
        # Get required inputs from template_config
        required_inputs = self.config.get("inputs", {})
        self.inputs = {}
        
        # Validate and load inputs
        for input_name, input_config in required_inputs.items():
            # Get value from context
            value = context.get(input_name)
            
            # Validate required inputs
            if value is None and input_config.get("required", True):
                raise TemplateValidationError(
                    f"Required input not found: {input_name}"
                )
            
            self.inputs[input_name] = value
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type.
        
        Args:
            value: Value to validate
            expected_type: Expected type name
        
        Returns:
            True if value is of expected type
        """
        type_map = {
            "string": str,
            "integer": int,
            "float": float,
            "boolean": bool,
            "list": list,
            "dict": dict
        }
        return isinstance(value, type_map.get(expected_type, str))
    
    def render(self, target_dir: str | Path, context: Dict[str, Any] = None) -> None:
        """Render template files to target directory.
        
        Args:
            target_dir: Directory to render files to
        
        Raises:
            TemplateRenderError: If rendering fails
        """
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Render each file
        for file_path in self.files:
            try:
                # Get relative path from template directory
                rel_path = file_path.relative_to(self.template_dir)
                target_path = target_dir / rel_path
                
                # Create parent directories
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Check if file needs templating
                if file_path.suffix in get_bpm_config(
                    filename="main.yaml",
                    key="template_files_rendered")["formats"]:
                    # Render template
                    template = self.env.get_template(str(rel_path))
                    content = template.render(**context)
                    
                    # Write rendered content
                    with open(target_path, "w") as f:
                        f.write(content)
                else:
                    # Copy file as is
                    shutil.copy2(file_path, target_path)
            
            except Exception as e:
                raise TemplateRenderError(
                    f"Failed to render {file_path}: {e}"
                )
    
    # def register_output(self, project_file: str | Path) -> None:
    #     """Register outputs in project.yaml.
        
    #     Args:
    #         project_file: Path to project.yaml
        
    #     Raises:
    #         TemplateError: If output registration fails
    #     """
    #     project = Project(project_file)
        
    #     # Get output definitions from config
    #     outputs = self.config.get("outputs", {})
        
    #     # Register each output
    #     for output_name, output_config in outputs.items():
    #         try:
    #             # Get output value
    #             value = self._get_output_value(output_config)
                
    #             # Update project
    #             project.update_value(output_config["path"], value)
                
    #             # Update status if specified
    #             if "status" in output_config:
    #                 project.update_template_status(
    #                     output_config["section"],
    #                     self.name,
    #                     output_config["status"]
    #                 )
            
    #         except Exception as e:
    #             raise TemplateError(
    #                 f"Failed to register output {output_name}: {e}"
    #             )
    
    # def _get_output_value(self, output_config: Dict[str, Any]) -> Any:
    #     """Get output value based on configuration.
        
    #     Args:
    #         output_config: Output configuration
        
    #     Returns:
    #         Output value
        
    #     Raises:
    #         TemplateError: If output value cannot be determined
    #     """
    #     # Handle different output types
    #     output_type = output_config.get("type", "path")
        
    #     if output_type == "path":
    #         # Check if path exists
    #         path = Path(output_config["value"])
    #         if not path.exists():
    #             raise TemplateError(f"Output path does not exist: {path}")
    #         return str(path)
        
    #     elif output_type == "file_content":
    #         # Read file content
    #         path = Path(output_config["value"])
    #         if not path.exists():
    #             raise TemplateError(f"Output file does not exist: {path}")
    #         with open(path) as f:
    #             return f.read()
        
    #     elif output_type == "static":
    #         # Return static value
    #         return output_config["value"]
        
    #     else:
    #         raise TemplateError(f"Unknown output type: {output_type}")
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate template configuration.
        
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        # Check required config sections
        required_sections = ["inputs", "outputs"]
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing required section: {section}")
        
        # Validate inputs
        for input_name, input_config in self.config.get("inputs", {}).items():
            if "path" not in input_config:
                errors.append(f"Missing path for input: {input_name}")
        
        # Validate outputs
        for output_name, output_config in self.config.get("outputs", {}).items():
            if "path" not in output_config:
                errors.append(f"Missing path for output: {output_name}")
            if "value" not in output_config:
                errors.append(f"Missing value for output: {output_name}")
        
        # Check required programs
        if "required_programs" in self.config:
            programs_found, missing_programs = check_programs(
                self.config["required_programs"])
            if not programs_found:
                errors.append(f"Required programs not found in PATH: {', '.join(missing_programs)}")
        
        return len(errors) == 0, errors
