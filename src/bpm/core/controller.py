"""Controller for BPM operations.

This module provides the main Controller class for managing BPM operations.

This module serves as the central coordinator for BPM operations, managing:
- Project and template operations
- Workflow execution
- Configuration management
- Repository handling

Example:
    >>> controller = Controller()
    >>> controller.set_active_repository("bpm-repo", "1.0.0")
    >>> controller.create_project("my_project")
    >>> controller.generate_template("demultiplexing.bclconvert")
    >>> controller.run_workflow("workflow.yaml")
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from rich.pretty import pprint
import importlib
import typer
import sys
import shutil

from bpm.core.project import Project
from bpm.core.template import Template
from bpm.core.config import ConfigLoader
from bpm.core.repo import CacheManager
from bpm.utils.ui.console import BPMConsole
from bpm.core.helpers import get_cachedir, flatten_dict, nested_flatten_dict
from bpm.utils.path import host_solver
from bpm.core.template.models import StructureType

# Configure rich console
console = BPMConsole()

class ControllerError(Exception):
    """Base exception for controller errors."""
    def __init__(self, message: str) -> None:
        super().__init__(message)
        console.error(message)

class Controller:
    """Main controller class for managing BPM operations."""
    
    def __init__(self, verbose: bool = False) -> None:
        """Initialize controller.
        
        Args:
            verbose: If True, show detailed logging information
        """
        self.verbose = verbose
        self.cache_manager = CacheManager(cache_dir=get_cachedir())
        self.config_loader = ConfigLoader(config_dir=self.cache_manager.get_config_path())
        self.project: Optional[Project] = None
        self.template: Optional[Template] = None
        self.context = None
        
        self.host_mappings = self.config_loader.get_value("environment", "host_paths")
        self.host_solver = host_solver.update_mappings(
            host_mappings=self.host_mappings)

    def get_context_value(self, key_path: str) -> Any:
        """Get a value from context using dot notation or direct key matching.
        
        Args:
            key_path: Key to search for. Can be a dot-separated path (e.g., "cmd_params.template")
                     or a direct key (e.g., "template")
            
        Returns:
            The value at the specified path or the first matching key found
            
        Raises:
            ControllerError: If context is not initialized or key is not found
        """
        if not self.context:
            raise ControllerError("Context is not initialized. Call collect_contexts() first.")
            
        if not key_path:
            raise ControllerError("Key path cannot be empty")
        
        if not isinstance(key_path, str):
            raise ControllerError(f"Value for key '{key_path}' is not a string")

        # If key contains dots, use dot notation path
        if "." in key_path:
            keys = key_path.split(".")
            value = self.context
            
            for i, key in enumerate(keys):
                if not isinstance(value, dict):
                    current_path = ".".join(keys[:i])
                    raise ControllerError(
                        f"Invalid path: '{current_path}' is not a dictionary"
                    )
                    
                if key not in value:
                    current_path = ".".join(keys[:i+1])
                    raise ControllerError(
                        f"Key '{current_path}' not found in context"
                    )
                    
                value = value[key]
            if isinstance(value, Path):
                value = str(value)
            return value
        else:
            # If key doesn't contain dots, search all levels
            def search_dict(d: dict, target_key: str) -> Any:
                if target_key in d:
                    return d[target_key]
                
                for value in d.values():
                    if isinstance(value, dict):
                        try:
                            return search_dict(value, target_key)
                        except ControllerError:
                            continue
                
                raise ControllerError(f"Key '{target_key}' not found in context")
            
            return search_dict(self.context, key_path)

    def collect_contexts(self, params: dict[str, Any]) -> None:
        """Collect context from all providers and add to context.
        
        Args:
            params: Dictionary of parameters to add to context
        """
        if self.verbose:
            console.info("Collecting contexts from all providers...")
            
        # Get project context if available
        if self.project:
            project_context = self.project.export_as_dict()
            if self.verbose:
                console.info("Project context collected")
        else:
            project_context = {}
        # Get config context
        if self.config_loader:
            config_context = self.config_loader.configs
            if self.verbose:
                console.info("Config context collected")
        # Get parameters from command line
        if params:
            for param, value in params.items():
                if isinstance(value, Path):
                    params[param] = value.absolute()
            params_context = params
            if self.verbose:
                console.info("Command line parameters collected")
            # Get config context
            context = {
                "cmd_params": params_context,
                "project": project_context,
                "repo_config": config_context,
            }
        else:
            context = {
                "project": project_context,
                "repo_config": config_context,
            }
        
        self.context = context
        # pprint(self.context)
        if self.verbose:
            console.info("All contexts merged successfully")

    def generate_template(self,
                          template_name: str,
                          output_dir: Path,
                          force_output_dir: bool = False) -> None:
        """Load a template.
        
        Args:
            template_name: Name of template to load
            output_dir: Output directory path
        Raises:
            ControllerError: If template loading fails
        """
        template_path = self.cache_manager.get_template_path(template_name)
        self.template = Template(template_path,
                                 config_loader=self.config_loader,
                                 verbose=self.verbose)
        self.process_template_inputs()
        self.context["template_inputs"] = nested_flatten_dict(self.template_inputs)
        self.process_template_post_hooks()
        self.check_template_required_tools()
        
        if self.project and not force_output_dir:
            render_target = self.resolve_template_output_dir_with_project()
        elif output_dir:
            render_target = output_dir
        else:
            console.error(f"Both --output and --project are not defined.")
            sys.exit(1)
            
        self.render_template(output_dir=render_target)
        self.insert_temp_to_project()
        self.project.save_to_file()

    def process_template_inputs(self) -> None:
        """Process template inputs and resolve their values.
        
        This method processes all template inputs, resolving their values from
        context, defaults, or resolvers. It also handles type conversion for
        different input types.
        
        Raises:
            ControllerError: If required inputs are missing or invalid
        """
        if self.verbose:
            console.info("Processing template inputs...")
            
        self.template_inputs = {}
        context_dict = nested_flatten_dict(self.context)
        # Convert all paths recursively to Path objects
        context_dict = self._convert_paths_recursively(context_dict, self.host_solver)
        console.dict(context_dict)
        for input_name, input_config in self.template.config.inputs.items():
            if self.verbose:
                console.info(f"Processing input: {input_name}")   
            # Required input
            if input_config.required:
                # Get input from context
                try:
                    self.template_inputs[input_name] = \
                        self.get_context_value(input_name)
                    if self.verbose:
                        console.info(f"Required input '{input_name}' found in context")
                # If input is not found in context, raise error
                except ControllerError as e:
                    console.error(f"Required input '{input_name}' should be provided.")
                    sys.exit(1)
                if self.template_inputs[input_name] is None:
                    console.error(f"Required input '{input_name}' should be provided.")
                    sys.exit(1)
            else: # Optional input
                # Get input from context if it is defined
                if self.get_context_value(input_name) is not None:
                    # Get input from context if it is defined
                    self.template_inputs[input_name] = \
                        self.get_context_value(input_name)
                    if self.verbose:
                        console.info(f"Optional input '{input_name}' found in context")
                # If input is not found in context, use default value
                else:
                    # Default input for non-required inputs
                    if input_config.default:
                        console.info(f"Default value for '{input_name}': {input_config.default}")
                        console.info(context_dict(input_config.default))
                        if context_dict(input_config.default):
                            self.template_inputs[input_name] = \
                                context_dict(input_config.default)
                        else:
                                self.template_inputs[input_name] = input_config.default
                        if self.verbose:
                            console.info(f"Using default value for '{input_name}'")
                        if isinstance(input_config.default, str):
                            try:
                                self.template_inputs[input_name] = \
                                    self.get_context_value(input_config.default)
                                if self.verbose:
                                    console.info(f"Resolved default value for '{input_name}' from context")
                            except ControllerError as e:
                                continue
                    elif input_config.default_resolver:
                        if self.verbose:
                            console.info(f"Using resolver for '{input_name}'")
                        self.template_inputs[input_name] = \
                            self._resolver(input_config.default_resolver)
                    else:
                        console.error(f"No default value or resolver found for input '{input_name}'")
                        sys.exit(1)

            # Resolve the input value
            if input_config.type == "path" and self.template_inputs[input_name] is not None:
                # self.template_inputs[input_name] = \
                #     host_solver.from_hostpath_to_path(self.template_inputs[input_name])
                if self.verbose:
                    console.info(f"Resolved path for '{input_name}'")
            if input_config.type == "list" and self.template_inputs[input_name] is not None:
                self.template_inputs[input_name] = \
                    self.template_inputs[input_name].split(",")
                if self.verbose:
                    console.info(f"Split list for '{input_name}'")
            if input_config.type == "int" and self.template_inputs[input_name] is not None:
                self.template_inputs[input_name] = \
                    int(self.template_inputs[input_name])
                if self.verbose:
                    console.info(f"Converted to integer for '{input_name}'")
            if input_config.type == "float" and self.template_inputs[input_name] is not None:
                self.template_inputs[input_name] = \
                    float(self.template_inputs[input_name])
                if self.verbose:
                    console.info(f"Converted to float for '{input_name}'")
            if input_config.type == "bool" and self.template_inputs[input_name] is not None:
                self.template_inputs[input_name] = \
                    bool(self.template_inputs[input_name])
                if self.verbose:
                    console.info(f"Converted to boolean for '{input_name}'")
                    
        if self.verbose:
            console.info("All template inputs processed successfully")

    def process_template_post_hooks(self) -> None:
        """Process template post hooks."""
        if self.verbose:
            console.info("Processing template post hooks...")
        for post_hook in self.template.config.post_hooks:
            console.info(f"Processing post hook: {post_hook}")
            self._posthook(post_hook)

    def _resolver(self, resolver: str) -> Any:
        """Resolve a value from the context.
        
        Args:
            resolver: Resolver type
            
        Returns:
            Resolved value
            
        Raises:
            ControllerError: If resolver file not found or resolution fails
        """
        resolver_dir = self.cache_manager.get_resolvers()
        resolver_file = resolver_dir / f"{resolver}.py"
        if not resolver_file.exists():
            raise ControllerError(f"Resolver file '{resolver_file}' not found")
        
        # Add resolver directory to Python path
        import sys
        if str(resolver_dir) not in sys.path:
            sys.path.append(str(resolver_dir))
        
        # Import the module using just the filename without extension
        resolver_module = importlib.import_module(resolver)
        resolver_function = getattr(resolver_module, resolver)
        if self.verbose:
            console.dict(nested_flatten_dict(self.context))
        return resolver_function(nested_flatten_dict(self.context))

    def _posthook(self, posthook: str) -> Any:
        """Run a post-hook.

        Args:
            posthooker: Post-hook type
            
        Returns:
            None
            
        Raises:
            ControllerError: If post-hook file not found or post-hook fails
        """
        posthook_dir = self.cache_manager.get_post_hooks()
        posthook_file = posthook_dir / f"{posthook}.py"
        if not posthook_file.exists():
            raise ControllerError(f"Post-hook file '{posthook_file}' not found")
        
        # Add post-hook directory to Python path
        import sys
        if str(posthook_dir) not in sys.path:
            sys.path.append(str(posthook_dir))
        
        # Import the module using just the filename without extension
        posthook_module = importlib.import_module(posthook)
        posthook_function = getattr(posthook_module, posthook)
        return posthook_function(nested_flatten_dict(self.context))

    def resolve_template_output_dir_with_project(self) -> Path:
        """Resolve the template output directory with the project."""
        console.warning(f"Project directory: {self.project.info.project_dir}")
        if self.template.config.structure == StructureType.SUBSECTION:
            render_target = self.project.info.project_dir / \
                self.template.config.section / self.template.config.name
        else:
            render_target = self.project.info.project_dir / \
                self.template.config.name
        return render_target

    def render_template(self, output_dir: Path) -> None:
        """Render the current template.
        
        This method renders the template with the current context and saves the
        rendered template to the project.
        
        Raises:
            ControllerError: If no template is loaded
        """
        # Get template context
        render_context = self.template_inputs
        render_context.update(self.context)
        if self.verbose:
            console.info("Render context:")
            pprint(render_context)
        # Render template
        self.template.render(context=render_context,
                             output_dir=output_dir)
        if self.verbose:
            console.info(f"Rendered template to: {output_dir}")

    def insert_temp_to_project(self) -> None:
        """Insert the rendered template into the project.
        
        This method adds the template inputs and outputs to the project's
        configuration. It creates a new section in the project for the template
        with all its inputs and empty outputs.
        
        Raises:
            ControllerError: If no template is loaded or no project exists
        """
        if not self.template:
            raise ControllerError("No template loaded")
        if not self.project:
            raise ControllerError("No project loaded")
        
        keys_to_remove = {'cmd_params', 'project', 'repo_config'}
        section = {k: v for k, v in self.template_inputs.items() if k not in keys_to_remove}
        for output in self.template.config.outputs:
            section[output] = ""
        section_name = self.template.config.section
        if self.template.config.structure == StructureType.SUBSECTION:
            self.project.add_project_section(section_name,
                                             self.template.config.name,
                                             section)
        else:
            self.project.add_project_section(section_name,
                                             "",
                                             section)
        if self.verbose:
            console.info(f"Adding template section '{section_name}' to project")
        

    def create_project(self,
                       project_path: Path,
                       from_project: Optional[Path] = None,
                       authors: list[str] | None = None,
                       force: bool = False) -> None:
        """Create a new project.
        
        Args:
            project_path: Path where project will be created
            from_project: Optional path to existing project to copy from
            authors: List of author IDs to add to project
            force: If True, overwrite existing project without confirmation
            
        Raises:
            ControllerError: If project creation fails
        """
        try:
            # Check if project directory exists
            if project_path.exists() and not force:
                if not typer.confirm(f"Project directory '{project_path}' already exists. Overwrite?"):
                    raise ControllerError("Project creation cancelled by user")
            
            # Create project
            console.info(f"Creating project at {project_path}")
            self.project = Project(project_dir=project_path,
                                   config_loader=self.config_loader)
            if from_project:
                # Replace sections with previous project
                previous_project = Project(project_dir=from_project.parent,
                                           config_loader=self.config_loader)
                previous_project.read_from_file(from_project)
                self.project._sections = previous_project._sections
                self.project.history = previous_project.history

            if authors:
                # Add authors to project
                for person in authors:
                    person_info = self.config_loader.get_author_info(person)
                    self.project.add_author(person_info)
            console.success(f"Created project at {project_path}")
        except Exception as e:
            raise ControllerError(f"Failed to create project: {e}")

    def load_project(self, project_yaml: Path) -> None:
        """Load an existing project.
        
        Args:
            project_path: Path to project
            
        Raises:
            ControllerError: If project loading fails
        """
        try:
            project_path = project_yaml.parent
            self.project = Project(project_path, config_loader=self.config_loader)
            self.project.read_from_file(project_yaml)
            
            console.success(f"Loaded project from {project_yaml}")
        except Exception as e:
            console.error(f"Failed to load project: {e}")
            sys.exit(1)

    def check_template_required_tools(self) -> None:
        """Check if all required tools are installed."""
        if not self.template:
            raise ControllerError("No template loaded")
        tool_paths = self.context["repo_config"]["environment"]["tool_paths"]
        for command in self.template.config.required_commands:
            if command in tool_paths:
                tool_path = tool_paths[command]
            else:
                tool_path = command
                
            if shutil.which(tool_path):
                if self.verbose:
                    console.info(f"'{tool_path}' is available in PATH.")
            else:
                console.warning(f"'{tool_path}' is NOT in PATH. You can customize the repo config environment.yaml to add the path to the tool.")

    def update_template_outputs(self, section: str, template_name: str) -> None:
        """Update template outputs in the project.
        
        This method updates the output values for a specific template in the project
        by running the output resolvers defined in the template.
        
        Args:
            section: Template section name (can be empty)
            template_name: Template name
            
        Raises:
            ControllerError: If template or project is not loaded, or if update fails
        """
        self.collect_contexts(params={})
        template_path = self.cache_manager.get_template_path(template_name)
        # console.print(f"Template path: {template_path}")
        self.template = Template(template_path,
                                 config_loader=self.config_loader,
                                 verbose=self.verbose)
        # Get template section
        section = self.template.config.section
        template_name = self.template.config.name
        console.info(f"Template section: {section}, template name: {template_name}")
        if self.template.config.structure == StructureType.SUBSECTION:
            template_section = self.project.get_project_section(section,
                                                                template_name)
        else:
            template_section = self.project.get_project_section(section, "")
        # Process each output
        for output_name in self.template.config.outputs:
            if self.verbose:
                console.info(f"Processing output: {output_name}")
                
            # Get output resolver from template config
            output_config = self.template.config.outputs.get(output_name)
            if not output_config or not output_config.resolver:
                if self.verbose:
                    console.warning(f"No resolver found for output {output_name}")
                continue
                
            try:
                # Run resolver
                if self.verbose:
                    console.info(f"Running resolver for output {output_name}")
                resolved_value = self._resolver(output_config.resolver)
                
                # Update project section
                template_section[output_name] = resolved_value
                if self.verbose:
                    console.info(f"Updated output {output_name} with resolved value")
                    
            except Exception as e:
                if self.verbose:
                    console.error(f"Failed to resolve output {output_name}: {e}")
                continue
        if self.template.config.structure == StructureType.SUBSECTION:
            self.project.add_project_section(section, template_name, template_section)
        else:
            self.project.add_project_section(section, "", template_section)
        # Save updated project
        try:
            self.project.save_to_file()
            if self.verbose:
                console.info("Saved updated project configuration")
        except Exception as e:
            raise ControllerError(f"Failed to save updated project: {e}")

    def _convert_paths_recursively(self, obj, host_solver):
        """
        Recursively convert string paths to Path objects in nested data structures.
        
        Args:
            obj: The object to process (dict, list, tuple, or other types)
            host_solver: The host solver instance for path conversion
            
        Returns:
            The processed object with paths converted
        """
        if isinstance(obj, dict):
            # Process dictionary recursively
            result = {}
            for k, v in obj.items():
                result[k] = self._convert_paths_recursively(v, host_solver)
            return result
        elif isinstance(obj, (list, tuple)):
            # Process list/tuple recursively
            return type(obj)(self._convert_paths_recursively(item, host_solver) for item in obj)
        elif isinstance(obj, str):
            # Convert string to Path if it exists and looks like a path
            if obj and not obj.startswith(('http://', 'https://', 'ftp://')):
                console.info(f"Converting path: {obj}")
                try:
                    resolved_path = host_solver.from_hostpathstr_to_path(obj)
                    # Check if path exists (file or directory)
                    # if resolved_path.exists():
                    # console.info(f"Path exists: {resolved_path}")
                    return resolved_path
                    # else:
                    #     console.warning(f"Path does not exist: {resolved_path}")
                    #     return obj
                except Exception as e:
                    # console.warning(f"Path resolution failed for '{obj}': {e}")
                    # If path conversion fails, return original string
                    return obj
            else:
                return obj
        else:
            # Return other types as-is
            return obj
        