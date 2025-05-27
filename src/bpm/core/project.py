"""Project module for BPM.

This module defines the core data structures for managing bioinformatics projects.
It includes models for project information, processing stages, and status tracking.

The module uses Pydantic for data validation and serialization, with custom handling
for special types like Path and datetime objects.

Example:
    >>> project = Project(Path("/path/to/project"))
    >>> project.info.name = "230101_Project_GF_RNAseq"
    >>> project.add_processing_info(ProcessingInfo(...))
    >>> project.serialize_to_file(Path("project.yaml"))
"""

from datetime import datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any, Self

from httpx import Client, RequestError
from pydantic import BaseModel, HttpUrl, SecretStr, field_validator, model_validator, ValidationError
from ruamel.yaml import YAML
from rich.console import Console
from rich.panel import Panel

from bpm.utils.file_io import load_yaml, save_yaml
from bpm.core.config import get_bpm_config
# Configure YAML serializer
yaml = YAML()
yaml.default_flow_style = False
yaml.indent(sequence=4, offset=2)
yaml.preserve_quotes = True
yaml.explicit_start = True

# Configure rich console
console = Console()


class ProjectStatus(StrEnum):
    """Enumeration of possible project statuses.
    
    Attributes:
        not_started: Project has been created but not started
        running: Project is currently being processed
        pending: Project is waiting for resources or dependencies
        completed: Project has finished successfully
        failed: Project encountered an error and failed
    """
    not_started = "not_started"
    running = "running"
    pending = "pending"
    completed = "completed"
    failed = "failed"


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
            console.print(Panel(error_msg, title="Project Name Error", border_style="red"))
            raise ValueError(error_msg)
    
    @staticmethod
    def validate_date(date_str: str) -> None:
        """Validate date format in project name.
        
        Args:
            date_str: Date string to validate
            
        Raises:
            ValueError: If date format is invalid
        """
        try:
            datetime.strptime(date_str, "%y%m%d")
        except ValueError as e:
            error_msg = (
                f"Invalid date format in project name: {date_str}\n\n"
                "Date must be in YYMMDD format\n"
                "Example: 230102 for January 2, 2023"
            )
            console.print(Panel(error_msg, title="Date Format Error", border_style="red"))
            raise ValueError(error_msg) from e


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


class BasicInfo(BaseModel):
    """Basic project information model.
    
    This model stores essential project metadata including directory, name,
    dates, and authorship information. It automatically extracts information
    from the project directory name following the format:
    YYMMDD_name1_name2_institute_application

    Attributes:
        project_dir: Path to project directory
        name: Project name (extracted from directory)
        project_date: Project start date (extracted from name)
        institute: Institute name (extracted from name)
        application: Application type (extracted from name)
        authors: List of project authors
        created_at: Project creation timestamp
        retention_until: Project retention deadline
    """
    project_dir: Path
    name: str | None = None
    project_date: str | None = None
    institute: str | None = None
    application: str | None = None
    authors: list[str] = []
    created_at: datetime = datetime.now()
    retention_until: datetime | None = None

    @model_validator(mode='before')
    @classmethod
    def validate_project_name(cls, data: Any) -> Any:
        """Validate project name format before model creation.
        
        Args:
            data: Raw input data, could be dict or other types
            
        Returns:
            Validated data
            
        Raises:
            ValueError: If project name doesn't match expected format
        """
        if not isinstance(data, dict):
            return data
            
        project_dir = data.get('project_dir')
        if not project_dir:
            return data
            
        project_name = project_dir.name
        try:
            ProjectNameValidator.validate_format(project_name)
            ProjectNameValidator.validate_date(project_name.split("_")[0])
        except ValueError as e:
            # Re-raise as ValueError to maintain clean error message
            raise ValueError(str(e))
        
        return data

    def model_post_init(self, context) -> None:
        """Extract project information from directory name.
        
        Raises:
            ValueError: If project name doesn't match expected format
        """
        try:
            project_name = self.project_dir.name
            self.name = project_name
            
            date, name1, institute, application = ProjectNameExtractor.extract_components(project_name)
            self.project_date = date
            self.institute = institute
            self.application = application
            
        except Exception as e:
            if not isinstance(e, ValueError):
                error_msg = (
                    f"Error processing project name: {str(e)}\n\n"
                    "Please ensure the project directory name follows the format:\n"
                    "YYMMDD_name1_name2_institute_application"
                )
                console.print(Panel(error_msg, title="Project Name Error", border_style="red"))
                raise ValueError(error_msg) from e
            raise


class DemultiplexInfo(BaseModel):
    """Demultiplexing information model.
    
    Tracks information about the demultiplexing process including input/output
    paths and current status.

    Attributes:
        method_name: Name of demultiplexing method used
        samplesheet_path: Path to samplesheet file
        raw_date_path: Path to raw data
        demux_dir: Demultiplexing output directory
        fastq_dir: FASTQ output directory
        fastq_multiqc: MultiQC report path
        status: Current demultiplexing status
        updated_at: Last update timestamp
    """
    method_name: str
    samplesheet_path: Path
    raw_date_path: Path
    demux_dir: Path
    fastq_dir: Path
    fastq_multiqc: Path
    status: ProjectStatus
    updated_at: datetime = datetime.now()


class ProcessingInfo(BaseModel):
    """Processing information model.
    
    Tracks information about data processing steps including input/output
    paths and current status.

    Attributes:
        method_name: Name of processing method
        fastq_input: Input FASTQ directory
        processing_dir: Processing output directory
        results_dir: Results directory
        multiqc_report: MultiQC report path
        status: Current processing status
        updated_at: Last update timestamp
    """
    method_name: str
    fastq_input: Path
    processing_dir: Path
    results_dir: Path
    multiqc_report: Path
    status: ProjectStatus
    updated_at: datetime


class AnalysisInfo(BaseModel):
    """Analysis information model.
    
    Tracks information about analysis steps including script paths
    and current status.

    Attributes:
        template: Analysis template name
        script: Path to analysis script
        output_html: Path to HTML output
        status: Current analysis status
    """
    template: str
    script: Path
    output_html: Path
    status: ProjectStatus


class ReportInfo(BaseModel):
    """Report information model.
    
    Tracks information about project reports including paths
    and current status.

    Attributes:
        report_entry: Path to report entry
        report_url: URL to report
        status: Current report status
    """
    report_entry: Path
    report_url: HttpUrl
    status: ProjectStatus


class ExportInfo(BaseModel):
    """Export information model.
    
    Tracks information about project exports including paths,
    URLs, and access credentials.

    Attributes:
        export_dir: Export directory path
        apache_url: Apache server URL
        report_url: Report URL
        cloud_export_url: Cloud export URL
        export_use: Export user
        export_password: Export password
        status: Current export status
    """
    export_dir: Path
    apache_url: HttpUrl
    report_url: HttpUrl
    cloud_export_url: HttpUrl
    export_use: str
    export_password: SecretStr
    status: ProjectStatus

    @field_validator("apache_url", "report_url", "cloud_export_url", mode="before")
    @classmethod
    def validate_urls(cls, link: HttpUrl) -> HttpUrl:
        """Validate that URLs are accessible.
        
        Args:
            link: URL to validate
            
        Returns:
            Validated URL
            
        Raises:
            ValueError: If URL is not accessible or returns error
        """
        try:
            with Client() as client:
                response = client.head(str(link), timeout=5)
                if response.status_code >= 400:
                    raise ValueError(
                        f"The following url: {link} appears to be in valid. status code {response.status_code}"
                    )
        except RequestError as e:
            raise ValueError(f"URL check failed: {e}")
        return link


class History(BaseModel):
    """Command history model.
    
    Tracks executed commands with timestamps.

    Attributes:
        command: Executed command string
        date: Command execution timestamp
    """
    command: str
    date: datetime = datetime.now()


class Project:
    """Main project class for managing bioinformatics projects.
    
    This class manages all aspects of a bioinformatics project including
    basic information, processing steps, analysis, reporting, and history.
    It provides methods for adding and updating project information and
    serializing the project state to YAML.

    Attributes:
        info: Basic project information
        demultiplexing: Demultiplexing information
        processing: Dictionary of processing steps
        analysis: Dictionary of analysis steps
        report: Report information
        export: Export information
        history: Command history
    """
    __slots__ = [
        "info",
        "demultiplexing",
        "processing",
        "analysis",
        "report",
        "export",
        "history",
    ]

    def __init__(self, project_dir: Path) -> None:
        """Initialize a new project.
        
        Args:
            project_dir: Path to project directory
        """
        self.info: BasicInfo = BasicInfo(project_dir=project_dir)
        self.demultiplexing: DemultiplexInfo | None = None
        self.processing: dict[str, ProcessingInfo] = {}
        self.analysis: dict[str, AnalysisInfo] = {}
        self.report: ReportInfo | None = None
        self.export: ExportInfo | None = None
        self.history: list[History] = []

    def set_retention_date(self, date: datetime = None) -> None:
        """Set project retention date.
        
        Args:
            date: Retention deadline
        """
        if date is None:
            retention_days = get_bpm_config("main.yaml", "policy.retention_policy")
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

    def add_demux_info(self, info: DemultiplexInfo, override_exiting=True) -> None:
        """Add demultiplexing information.
        
        Args:
            info: Demultiplexing information
            override_exiting: Whether to override existing info
            
        Raises:
            ValueError: If info exists and override is False
        """
        if self.info and not override_exiting:
            raise ValueError("A demultiplexing information already exists")
        self.demultiplexing = info

    def add_processing_info(self, processing: ProcessingInfo) -> None:
        """Add processing information.
        
        Args:
            processing: Processing information
            
        Raises:
            ValueError: If method already exists
        """
        self._add_info(
            self.processing, processing.method_name, processing, check_exists=True
        )

    def add_analysis_info(self, analysis: AnalysisInfo) -> None:
        """Add analysis information.
        
        Args:
            analysis: Analysis information
            
        Raises:
            ValueError: If template already exists
        """
        self._add_info(self.analysis, analysis.template, analysis, check_exists=True)

    def add_history(self, cmd: str) -> None:
        """Add command to history.
        
        Args:
            cmd: Command string to add
        """
        self.history.append(History(command=cmd))

    def get_status_summary(self) -> dict[str, Any]:
        """Get summary of project status.
        
        Returns:
            Dictionary containing status counts and template lists
        """
        status: dict[str, Any] = {
            "total_templates": 0,
            "status_counts": {s.value: 0 for s in ProjectStatus.__members__.values()},
            "template_by_status": {
                s.value: [] for s in ProjectStatus.__members__.values()
            },
        }

        for category in [self.demultiplexing, self.processing, self.analysis]:
            for method, entry in category.items():
                status["total_templates"] += 1
                status["status_counts"][entry.status.value] += 1
                key = (
                    entry.method_name
                    if category is not self.analysis
                    else entry.template
                )
                status["template_by_status"][entry.status.value].append(key)

        return status

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
        data = load_yaml(yaml_file)
        
        # Update project attributes from loaded data
        if "info" in data:
            self.info = BasicInfo(**data["info"])
        if "demultiplexing" in data:
            self.demultiplexing = DemultiplexInfo(**data["demultiplexing"])
        if "processing" in data:
            self.processing = {
                k: ProcessingInfo(**v) for k, v in data["processing"].items()
            }
        if "analysis" in data:
            self.analysis = {
                k: AnalysisInfo(**v) for k, v in data["analysis"].items()
            }
        if "report" in data:
            self.report = ReportInfo(**data["report"])
        if "export" in data:
            self.export = ExportInfo(**data["export"])
        if "history" in data:
            self.history = [History(**h) for h in data["history"]]
            
        return self

    def serialize_to_file(self, yaml_path: Path) -> None:
        """Serialize project to YAML file.
        
        Args:
            yaml_path: Path to output YAML file
            
        Raises:
            OSError: If the file cannot be written
            YAMLError: If the data cannot be serialized to YAML
        """
        project_dict = {
            "info": _serialize(self.info),
            "demultiplexing": _serialize(self.demultiplexing),
            "processing": _serialize(self.processing),
            "analysis": _serialize(self.analysis),
            "report": _serialize(self.report),
            "export": _serialize(self.export),
            "history": _serialize(self.history),
        }
        
        save_yaml(project_dict, yaml_path)

    def _add_info(self, container: dict, key, value, check_exists: bool = True) -> None:
        """Add information to container.
        
        Args:
            container: Target container dictionary
            key: Key to add
            value: Value to add
            check_exists: Whether to check for existing key
            
        Raises:
            ValueError: If key exists and check_exists is True
        """
        if check_exists and container.get(key):
            raise ValueError("The method already exists")
        container[key] = value

    def add_author(self, author: str) -> None:
        """Add author to project.
        
        Args:
            author: Author name
        """
        available_authors = get_bpm_config("main.yaml", "authors")
        if author not in available_authors:
            raise ValueError(f"Author {author} is not in the list of available authors [{', '.join(available_authors)}]")
        else:
            self.info.authors.append(f"{available_authors[author]['name']}, "
                                     f"{available_authors[author]['affiliation']} "
                                     f"<{available_authors[author]['email']}>")

def _serialize(obj: Any) -> Any:
    """Serialize object to YAML-compatible format.
    
    Args:
        obj: Object to serialize
        
    Returns:
        Serialized object
    """
    if isinstance(obj, BaseModel):
        return _serialize(obj.model_dump())
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M")  # Format without seconds
    if isinstance(obj, SecretStr):
        return obj.get_secret_value()
    if isinstance(obj, ProjectStatus):
        return obj.value
    if isinstance(obj, dict):
        if len(obj.keys()) == 0:
            return None
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        if len(obj) == 0:
            return None
        return [_serialize(v) for v in obj]
    return obj
