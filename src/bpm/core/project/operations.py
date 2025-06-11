"""Project operations for BPM.

This module provides the main Project class and its operations for managing
bioinformatics projects.
"""

import os, sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from pydantic import BaseModel
from ruamel.yaml import YAML

from bpm.core.config import ConfigLoader
from bpm.core.project.models import BasicInfo, History, ProjectStatus
from bpm.utils.ui.console import BPMConsole
from bpm.utils.path import host_solver

# Configure YAML serializer
yaml = YAML()
yaml.default_flow_style = False
yaml.width = 4096
yaml.indent(sequence=4, offset=2)
yaml.preserve_quotes = True
yaml.explicit_start = True

# Configure rich console
console = BPMConsole()


class ProjectNameValidator:
    """Validator for project name format and content."""
    
    @staticmethod
    def validate_format(project_name: str) -> None:
        """Validate project name format.
        
        Args:
            project_name: Project name to validate
            
        Raises:
            ValueError: If project name doesn't match expected format
        """
        parts = project_name.split("_")
        if not (5 <= len(parts) <= 6):
            error_msg = (
                f"Invalid project name format: {project_name}\n\n"
                "Project name must follow the format:\n"
                "YYMMDD_name1_name2_institute_application\n\n"
            )
            console.error(error_msg)
            raise ValueError(error_msg)
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Validate date format in project name.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if date is valid, False otherwise
        """
        try:
            datetime.strptime(date_str, "%y%m%d")
            return True
        except ValueError:
            return False


class ProjectNameExtractor:
    """Extractor for project name components."""
    
    @staticmethod
    def extract_components(project_name: str) -> tuple[str, str, str, str]:
        """Extract components from project name.
        
        Args:
            project_name: Project name to extract from
            
        Returns:
            Tuple of (date, name1, institute, application)
            
        Raises:
            ValueError: If project name format is invalid
        """
        parts = project_name.split("_")
        if not (5 <= len(parts) <= 6):
            raise ValueError("Invalid project name format")
            
        return parts[0], parts[1], parts[-2], parts[-1]


class Project():
    """Main project class for managing bioinformatics projects.
    
    This class manages all aspects of a bioinformatics project including
    basic information and history. It provides methods for adding and updating
    project information and serializing the project state to YAML.

    Attributes:
        info: Basic project information
        history: Command history
        _sections: Dictionary of project sections
        config_loader: ConfigLoader instance for configuration management
    """
    __slots__ = ["info", "history", "_sections", "config_loader"]

    def __init__(self,
                 project_dir: Path,
                 config_loader: Optional[ConfigLoader] = None) -> None:
        """Initialize a new project.
        
        Args:
            project_dir: Path to project directory
            config_loader: Optional ConfigLoader instance
        """
        # Extract project name from directory basename
        project_name = project_dir.name
        
        # Try to extract date from project name
        project_date = None
        
        if len(project_name) >= 6 and \
            ProjectNameValidator.validate_date(project_name[0:6]):
            project_date = project_name[0:6]
        
        # Create basic info with project name and date
        self.info: BasicInfo = BasicInfo(
            project_dir=project_dir,
            project_name=project_name,
            project_date=project_date,
            authors=[]  # Initialize empty authors list
        )
        self.history: list[History] = []
        self._sections: dict[str, BaseModel] = {}
        self.config_loader = config_loader
        host_solver.update_mappings(
            host_mappings=self.config_loader.get_value("environment", "host_paths"))

    def get_context(self) -> dict[str, Any]:
        """Get project context.
        
        Returns:
            Dictionary of project context data
        """
        return {
            "project_dir": self.info.project_dir,
            "project_name": self.info.project_name,
            "project_date": self.info.project_date,
            "authors": self.info.authors,
            "settings": self._sections
        }

    def set_retention_date(self, date: datetime = None) -> None:
        """Set project retention date.
        
        Args:
            date: Retention deadline
        """
        if date is None:
            if not self.config_loader or not self.config_loader.main_config:
                raise ValueError("ConfigLoader not available")
            retention_days = self.config_loader.main_config.policy.retention_policy
            self.info.retention_until = datetime.now() + timedelta(days=retention_days)
        else:
            self.info.retention_until = date

    def can_be_cleaned(self) -> bool:
        """Check if project can be cleaned up.
        
        Returns:
            True if project has passed retention date
        """
        return (
            datetime.now() > self.info.retention_until
            if self.info.retention_until
            else False
        )

    def add_history(self) -> None:
        """Add command to history.
        
        Args:
            cmd: Command string to add
        """
        cmd = " ".join(sys.argv)
        # Extract command after last 'bpm' occurrence
        cmd_parts = cmd.split()
        if cmd_parts[0].endswith("/bpm"):
            cmd_parts[0] = "bpm"
        
        cmd = " ".join(cmd_parts)
        
        # Get current timestamp with seconds
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create history entry
        history_entry = f"{timestamp}: {cmd}"
        
        self.history.append(history_entry)

    def add_project_section(self, name: str, section: BaseModel) -> None:
        """Add a new section to the project.
        
        Args:
            name: Section name
            section: Section model instance
            
        Example:
            >>> project.add_project_section("demultiplexing", DemultiplexInfo(...))
        """
        if name in self._sections:
            self._sections[name].update(section)
        else:
            self._sections[name] = section

    def get_project_section(self, name: str) -> BaseModel | None:
        """Get a project section by name.
        
        Args:
            name: Section name
            
        Returns:
            Section model instance or None if not found
        """
        return self._sections.get(name)

    def _resolve_host_paths(self, data: Any) -> Any:
        """Recursively resolve host paths in data.
        
        Args:
            data: Data to process
            
        Returns:
            Data with resolved paths
        """
        if isinstance(data, str):
            # Check if string is a host path
            try:
                return host_solver.from_host_path(data)
            except ValueError:
                return data
        elif isinstance(data, dict):
            return {k: self._resolve_host_paths(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._resolve_host_paths(item) for item in data]
        return data

    def read_from_file(self, yaml_file: Path) -> "Project":
        """Read project from YAML file.
        
        Args:
            yaml_file: Path to YAML file
            
        Returns:
            Project instance
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            YAMLError: If the file contains invalid YAML
            ValueError: If the loaded data doesn't match expected structure
        """
        with open(yaml_file) as f:
            data = yaml.load(f)
        
        # Update project attributes from loaded data
        if "info" in data:
            # Resolve host paths in info data
            info_data = self._resolve_host_paths(data["info"])
            self.info = BasicInfo(**info_data)
            
        if "history" in data:
            self.history = []
            for entry in data["history"]:
                self.history.append(entry)
            
        # Load sections and resolve host paths
        for key, value in data.items():
            if key not in ["info", "history"]:
                self._sections[key] = self._resolve_host_paths(value)
            
        return self

    def export_as_dict(self) -> dict[str, Any]:
        """Export project data as a dictionary.
        
        This method converts all project data into a dictionary format suitable
        for serialization or external use. It handles conversion of:
        - Path objects to host-aware paths
        - Datetime objects to strings
        - BaseModel instances to dictionaries
        - Empty collections to None
        
        Returns:
            dict[str, Any]: Dictionary containing all project data
            
        Example:
            >>> project_dict = project.export_as_dict()
            >>> # Use the dictionary for external purposes
            >>> json.dumps(project_dict)
        """
        return self._serialize_to_dict()

    def _serialize_to_dict(self) -> dict[str, Any]:
        """Serialize project to dictionary.
        
        Internal method used for YAML serialization. Consider using
        export_as_dict() for external use.
        
        Returns:
            Dictionary representation of project
        """
        # Start with required fields
        project_dict = {
            "info": self._convert_to_serializable(self.info),
        }
        
        # Add sections if not empty
        if self._sections:
            project_dict.update({name: self._convert_to_serializable(section) for name, section in self._sections.items()})
        # Add history
        project_dict["history"] = self.history
        return project_dict
    
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
            return self._convert_to_serializable(obj.model_dump())
        if isinstance(obj, Path):
            host_aware_path = host_solver.to_host_path(obj)
            return host_aware_path
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")  # Include seconds for command history
        if isinstance(obj, ProjectStatus):
            return obj.value
        if isinstance(obj, dict):
            if not obj:  # Empty dict
                return None
            return {k: self._convert_to_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            if not obj:  # Empty list
                return None
            return [self._convert_to_serializable(v) for v in obj]
        return obj

    def save_to_file(self) -> None:
        """Save project settings to project.yaml.
        
        Args:
            cmd: Optional command string to record in history
        """
        # Convert to dictionary
        project_dict = self._serialize_to_dict()
        # Ensure project directory exists
        self.info.project_dir.mkdir(parents=True, exist_ok=True)
        self.add_history()
        with open(self.info.project_dir / "project.yaml", "w") as f:
            yaml.dump(project_dict, f)
        console.success(f"Project settings saved to {self.info.project_dir / 'project.yaml'}")

    def add_author(self, author: str) -> None:
        """Add author to project.
        
        Args:
            author: Author name
            
        Raises:
            ValueError: If author is not in available authors list
        """
        self.info.authors.append(author)
    