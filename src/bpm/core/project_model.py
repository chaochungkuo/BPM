from datetime import date, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, HttpUrl, SecretStr


class ProjectStatus(StrEnum):
    not_started = "not_started"
    running = "running"
    pending = "pending"
    completed = "completed"
    failed = "failed"


class BasicInfo(BaseModel):
    name: str
    date: date
    institute: str
    application: str  # Can be converted to StrEnum
    authors: list[str]
    project_dir: Path  # Project path can be validated using custom validator
    created_at: datetime


class DemultiplexInfo(BaseModel):
    method: str
    samplesheet_path: Path
    raw_date_path: Path
    demux_dir: Path
    fastq_dir: Path
    fastq_multiqc: Path
    status: ProjectStatus
    updated_at: datetime


class ProcessingInfo(BaseModel):
    method: str  # Can be also an enum
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
    report_url: HttpUrl
    cloud_export_url: HttpUrl
    export_use: str
    export_password: SecretStr
    status: ProjectStatus


class History:
    command: str


class ProjectModel(BaseModel):
    basic_info: BasicInfo
    demultiplex_info: list[DemultiplexInfo] | None
    processing_info: list[ProcessingInfo] | None
    analysis_info: list[AnalysisInfo] | None
    export_info: ExportInfo | None
    history: list[History] | None
