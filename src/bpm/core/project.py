from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
from bpm.core.config import get_bpm_config
import os
import getpass
from collections import OrderedDict

from ruamel.yaml import YAML
from pathlib import Path

yaml = YAML()
yaml.default_flow_style = False
yaml.indent(sequence=4, offset=2)
# Enable ordered dictionary support
yaml.preserve_quotes = True
yaml.explicit_start = True


class Project:
    """Handle project.yaml operations and configuration management.
    
    This class manages the project configuration file, providing functionality for:
    - Project initialization and file operations (create, load, save)
    - Template status tracking and validation
    - Project history logging with user and host information
    - Path and value management using dot notation
    - Project retention date management
    
    The project file is stored in YAML format and contains sections for:
    - project: Core project information (always at the top)
    - template sections: Configuration for different processing templates
    - history: Command execution history (always at the bottom)
    
    Example:
        >>> project = Project("project.yaml")
        >>> project.update_template_status("demultiplexing", "bclconvert", "running")
        >>> project.add_history("bpm run bclconvert")
        >>> project.set_retention_until("2024-12-31")
        >>> project.save("project.yaml")
    """
    
    def __init__(
        self,
        project_file: str | Path | None = None,
    ) -> None:
        """Initialize Project with optional project.yaml path.
        
        Args:
            project_file: Path to the project file. If None, a new file will be created
                        with default configuration from main.yaml.
        
        Raises:
            ValueError: If project_info is missing when creating new project
            FileNotFoundError: If project file doesn't exist
            yaml.YAMLError: If the project file contains invalid YAML
        """
        if project_file is None:
            self.data = OrderedDict(get_bpm_config("main.yaml", "project_base"))
            self.data['project']['created_at'] = datetime.now().isoformat()
        # Try to load existing file
        else:
            try:
                self.data = self._load(project_file)
            except:
                raise FileNotFoundError(f"Project file not found: {project_file}")

    def _load(self, project_file: str | Path) -> OrderedDict[str, Any]:
        """Load project.yaml file.
        
        Args:
            project_file: Path to the project file to load
            
        Returns:
            OrderedDict containing project data with the following structure:
            {
                'project': {...},  # Project information (always first)
                'section_name': {  # Template sections
                    'template_name': {
                        'status': str,
                        'updated_at': str,
                        ...
                    }
                },
                'history': [...]  # Command history (always last)
            }
        
        Raises:
            FileNotFoundError: If project file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        try:
            with open(project_file, 'r') as f:
                return yaml.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Project file not found: {project_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {project_file}: {e}")
    
    def save(self, project_file: str | Path) -> None:
        """Save changes to project.yaml.
        
        Args:
            project_file: Path where the project file should be saved
            
        Raises:
            IOError: If file cannot be written
            PermissionError: If insufficient permissions to write file
        """
        try:
            # Create a new ordered dictionary with the desired section order
            ordered_data = OrderedDict()
            
            # Always put project section first
            if 'project' in self.data:
                ordered_data['project'] = self.data['project']
            
            # Add all other sections except history
            for section in self.data:
                if section not in ['project', 'history']:
                    ordered_data[section] = self.data[section]
            
            # Always put history section last
            if 'history' in self.data:
                ordered_data['history'] = self.data['history']
            
            with open(project_file, 'w') as f:
                yaml.dump(ordered_data, f)
        except Exception as e:
            raise IOError(f"Failed to save project file: {e}")
    
    def list_templates(self) -> Dict[str, list[str]]:
        """List all templates by section.
        
        Returns:
            Dictionary mapping section names to lists of template names.
            Example:
                {
                    'demultiplexing': ['bclconvert'],
                    'processing': ['nfcore_3mRNAseq']
                }
        """
        templates = {}
        for section in self.data:
            if section not in ['project', 'history']:
                templates[section] = list(self.data[section].keys())
        return templates
    
    # Status Management
    def get_template_status(self, section: str, template: str) -> str:
        """Get status of a template.
        
        Args:
            section: Template section name (e.g., 'demultiplexing')
            template: Template name within the section (e.g., 'bclconvert')
        
        Returns:
            Current status of the template as a string
            
        Raises:
            KeyError: If section or template doesn't exist
        """
        
        status = self.data[section][template]['status']
        return status
    
    def update_template_status(self, section: str, template: str, status: str) -> None:
        """Update status of a template.
        
        Args:
            section: Template section name (e.g., 'demultiplexing')
            template: Template name within the section (e.g., 'bclconvert')
            status: New status to set (must be one of the valid statuses)
        
        Raises:
            ValueError: If status is invalid or transition is not allowed
            KeyError: If section or template doesn't exist
        """
        valid_statuses = get_bpm_config("main.yaml",
                                        "template_status.statuses")
        # Get current status
        current_status = self.get_template_status(section, template)
        
        # Check if transition is valid
        if status not in valid_statuses:
            raise ValueError(
                f"Cannot transition from {current_status} to {status}. "
                f"Valid transitions: {valid_statuses}"
            )
        
        self.update_section(section, template, {
            'status': status,
            'updated_at': datetime.now().isoformat()
        })
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of all template statuses.
        
        Returns:
            Dictionary containing:
            - total_templates: Total number of templates
            - status_counts: Count of templates in each status
            - templates_by_status: Lists of templates grouped by status
            Example:
                {
                    'total_templates': 2,
                    'status_counts': {'running': 1, 'completed': 1},
                    'templates_by_status': {
                        'running': ['demultiplexing.bclconvert'],
                        'completed': ['processing.nfcore_3mRNAseq']
                    }
                }
        """
        valid_statuses = get_bpm_config("main.yaml",
                                        "template_status.statuses")
        summary = {
            'total_templates': 0,
            'status_counts': {status: 0 for status in valid_statuses},
            'templates_by_status': {status: [] for status in valid_statuses}
        }
        
        for section in self.data:
            if section not in ['project', 'history']:
                for template, data in self.data[section].items():
                    summary['total_templates'] += 1
                    status = data.get('status')
                    summary['status_counts'][status] += 1
                    summary['templates_by_status'][status].append(f"{section}.{template}")
        
        return summary
    
    # History Management
    def add_history(self, command: str) -> None:
        """Add a command to history with user information.
        
        Args:
            command: The command to add to history
            
        The history entry will be in the format:
        "YYMMDD HH:MM user@host command"
        Example: "240315 14:30 john@server bpm run bclconvert"
        """
        if 'history' not in self.data:
            self.data['history'] = []
        
        # Get user and host information
        user = getpass.getuser()
        host = os.uname().nodename
        
        # Format timestamp and create history entry
        timestamp = datetime.now().strftime("%y%m%d %H:%M")
        history_entry = f"{timestamp} {user}@{host} {command}"
        
        self.data['history'].append(history_entry)
    
    # Section Management
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get a section from project data.
        
        Args:
            section: Section name to retrieve (e.g., 'project', 'history', 'demultiplexing')
        
        Returns:
            Dictionary containing section data
            
        Raises:
            KeyError: If section doesn't exist
        """
        if section not in self.data:
            raise KeyError(f"Section not found: '{section}'")
        return self.data[section]
    
    def update_section(self, section: str, subsection: str, data: Dict[str, Any]) -> None:
        """Update a subsection in project data.
        
        Args:
            section: Section name (e.g., 'demultiplexing')
            subsection: Subsection name (e.g., 'bclconvert')
            data: Dictionary containing new data to merge with existing subsection
            
        Note:
            - This will merge the new data with existing subsection data
            - If section or subsection doesn't exist, they will be created
            - An 'updated_at' timestamp will be added if not present
        """
        if section not in self.data:
            self.data[section] = {}
        
        if subsection not in self.data[section]:
            self.data[section][subsection] = {}
        
        # Update the subsection with new data
        self.data[section][subsection].update(data)
        
        # Add timestamp if not present
        if 'updated_at' not in self.data[section][subsection]:
            self.data[section][subsection]['updated_at'] = datetime.now().isoformat()
    
    def insert_section(self, section: str, data: Dict[str, Any]) -> None:
        """Insert a new section into project data.
        
        Args:
            section: Section name to insert
            data: Dictionary containing section data
            
        Raises:
            ValueError: If section already exists
        """
        if section in self.data:
            raise ValueError(f"Section {section} already exists")
        self.data[section] = data
    
    # Path and Value Management
    def get_value(self, path: str) -> Any:
        """Get a value using dot notation.
        
        Args:
            path: Dot-separated path to the value (e.g., 'demultiplexing.bclconvert.fastq_dir')
            
        Returns:
            Value at the specified path
            
        Raises:
            KeyError: If path doesn't exist or is invalid
        """
        keys = path.split(".")
        value = self.data
        for key in keys:
            if key not in value:
                raise KeyError(f"Key not found: '{path}' (missing: '{key}')")
            value = value[key]
        return value
    
    def update_value(self, path: str, value: Any) -> None:
        """Update a value using dot notation.
        
        Args:
            path: Dot-separated path to the value (e.g., 'demultiplexing.bclconvert.fastq_dir')
            value: New value to set
            
        Note:
            - This will create intermediate dictionaries if they don't exist
            - For template sections, an 'updated_at' timestamp will be added if not present
        """
        # Split the path into keys
        keys = path.split('.')
        # Start with the root data
        current = self.data
        
        # Traverse and create dictionaries as needed
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
        
        # Add timestamp if we're updating a template section
        if len(keys) >= 2 and 'updated_at' not in current:
            current['updated_at'] = datetime.now().isoformat()
    
    # Retention Management
    def set_retention_until(self, date: str | datetime) -> None:
        """Set the date until which the project should be retained.
        
        Args:
            date: ISO format date string (YYYY-MM-DD) or datetime object
        
        Raises:
            ValueError: If date format is invalid or not in ISO format
        """
        if isinstance(date, datetime):
            retention_date = date.isoformat()
        else:
            retention_date = date
        # Validate date format
        try:
            datetime.fromisoformat(retention_date)
        except ValueError:
            raise ValueError(f"Invalid date format: {retention_date}. Use ISO format (YYYY-MM-DD)")
        
        # Update project info
        self.update_value("project.retention_until", retention_date)
    
    def can_be_cleaned(self) -> bool:
        """Check if the project can be cleaned based on retention date.
        
        Returns:
            True if:
            - Project has a retention date
            - Current date is past the retention date
            False if:
            - No retention date is set
            - Retention date is invalid
            - Current date is before retention date
        """
        project_info = self.get_project_info()
        retention_date = project_info.get('retention_until')
        
        if not retention_date:
            return False  # Don't clean if no retention date is set
        
        try:
            retention = datetime.fromisoformat(retention_date)
            return datetime.now() > retention
        except ValueError:
            return False  # Don't clean if date is invalid

    def get_project_info(self) -> Dict[str, Any]:
        """Get project information.
        
        Returns:
            Dictionary containing project information
            
        Raises:
            KeyError: If project section doesn't exist
        """
        return self.get_section("project")
