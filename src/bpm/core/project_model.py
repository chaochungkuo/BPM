from datetime import datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any

from httpx import Client, RequestError
from pydantic import BaseModel, HttpUrl, SecretStr, field_validator
from ruamel.yaml import YAML

yaml = YAML()
yaml.default_flow_style = False
yaml.indent(sequence=4, offset=2)
# Enable ordered dictionary support
yaml.preserve_quotes = True
yaml.explicit_start = True


class ProjectStatus(StrEnum):
    not_started = "not_started"
    running = "running"
    pending = "pending"
    completed = "completed"
    failed = "failed"


class BasicInfo(BaseModel):
    project_dir: Path  # Project path can be validated using custom validator
    name: str | None = None
    project_date: datetime | None = None
    institute: str | None = None
    application: str | None = None  # Can be converted to StrEnum
    authors: list[str] | None = None
    created_at: datetime = datetime.now()
    # TODO: Make the retention date configurable
    retention_until: datetime = datetime.now() + timedelta(
        days=30
    )  # default retention time of 30 days

    def model_post_init(self, context: Any) -> None:
        project_name = self.project_dir.name
        parts = str(project_name).split("_")
        assert (
            len(parts) >= 5 and len(parts) <= 6
        )  # Some groups names are compounded Schneider-Kramann
        self.project_date = datetime.strptime(parts[0], "%Y%m%d")
        self.application = parts[-1]
        self.institute = parts[-2]


class DemultiplexInfo(BaseModel):
    method_name: str
    samplesheet_path: Path
    raw_date_path: Path
    demux_dir: Path
    fastq_dir: Path
    fastq_multiqc: Path
    status: ProjectStatus
    updated_at: datetime


class ProcessingInfo(BaseModel):
    method_name: str  # Can be also an enum
    fastq_input: Path
    processing_dir: Path
    results_dir: Path
    multiqc_report: Path
    status: ProjectStatus
    updated_at: datetime


class AnalysisInfo(BaseModel):
    template: str  # Can be validated be in the list of templates
    script: Path
    output_html: Path
    status: ProjectStatus


class ExportInfo(BaseModel):
    export_dir: Path
    apache_url: HttpUrl  # should be validated after export
    report_url: HttpUrl  # should be validated after export
    cloud_export_url: HttpUrl
    export_use: str
    export_password: SecretStr
    status: ProjectStatus

    # Validate that URLS exist
    @field_validator("apache_url", "report_url", "cloud_export_url", mode="before")
    @classmethod
    def validate_urls(cls, link: HttpUrl) -> HttpUrl:
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
    command: str


# Can be also dataclass
class Project:
    __slots__ = [
        "info",
        "demultiplexing",
        "processing",
        "analysis",
        "export",
        "history",
    ]

    def __init__(self, project_dir: Path) -> None:
        self.info: BasicInfo = BasicInfo(project_dir=project_dir)
        self.demultiplexing: dict[str, DemultiplexInfo] = {}
        self.processing: dict[str, ProcessingInfo] = {}
        self.analysis: dict[str, AnalysisInfo] = {}
        self.export: ExportInfo | None = None
        self.history: list[History] = []

    def set_retenion_date(self, date: datetime) -> None:
        self.info.retention_until = date

    def can_be_cleaned(self) -> bool:
        return datetime.now() > self.info.retention_until

    def add_demux_info(self, info: DemultiplexInfo) -> None:
        self._add_info(self.demultiplexing, info.method_name, info, check_exists=True)

    def add_processing_info(self, processing: ProcessingInfo) -> None:
        self._add_info(
            self.processing, processing.method_name, processing, check_exists=True
        )

    def add_analysis_info(self, analysis: AnalysisInfo) -> None:
        self._add_info(self.analysis, analysis.template, analysis, check_exists=True)

    def add_history(self, cmd: str) -> None:
        self.history.append(History(command=cmd))

    def get_status_summary(self) -> dict[str, Any]:
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

    def read_from_file(self, yaml_file: Path) -> "Project":  # type: ignore
        pass

    def serialize_to_file(self, yaml_path: Path) -> None:
        project_dict = {
            "info": _serialize(self.info),
            "demultiplexing": _serialize(self.demultiplexing),
            "processing": _serialize(self.processing),
            "analysis": _serialize(self.analysis),
            "export": _serialize(self.export),
            "history": _serialize(self.history),
        }

        with open(yaml_path, "w") as f:
            yaml.dump(project_dict, f)

    def _add_info(self, container: dict, key, value, check_exists: bool = True) -> None:
        if check_exists and container.get(key):
            raise ValueError("The method already exists")
        container[key] = value


def _serialize(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return _serialize(obj.model_dump())
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
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
