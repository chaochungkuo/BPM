import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import HttpUrl, SecretStr
from ruamel.yaml import YAML

from bpm.core.project_model import (
    AnalysisInfo,
    DemultiplexInfo,
    ExportInfo,
    History,
    ProcessingInfo,
    Project,
    ProjectStatus,
)

# Basic project path used in tests
TEST_PROJECT_PATH = Path("/tmp/20240501_NameA_NameB_institute_app")


@pytest.fixture
def project():
    return Project(project_dir=TEST_PROJECT_PATH)


def test_basic_info_fields(project):
    assert project.info.project_date == datetime(2024, 5, 1)
    assert project.info.institute == "institute"
    assert project.info.application == "app"
    assert isinstance(project.info.created_at, datetime)
    assert project.info.retention_until > datetime.now()


def test_add_demux_info(project):
    info = DemultiplexInfo(
        method_name="demux1",
        samplesheet_path=Path("/tmp/sheet.csv"),
        raw_date_path=Path("/tmp/raw"),
        demux_dir=Path("/tmp/demux"),
        fastq_dir=Path("/tmp/fastq"),
        fastq_multiqc=Path("/tmp/multiqc"),
        status=ProjectStatus.pending,
        updated_at=datetime.now(),
    )
    project.add_demux_info(info)
    assert "demux1" in project.demultiplexing


def test_duplicate_demux_raises(project):
    info = DemultiplexInfo(
        method_name="demux1",
        samplesheet_path=Path("/tmp/sheet.csv"),
        raw_date_path=Path("/tmp/raw"),
        demux_dir=Path("/tmp/demux"),
        fastq_dir=Path("/tmp/fastq"),
        fastq_multiqc=Path("/tmp/multiqc"),
        status=ProjectStatus.pending,
        updated_at=datetime.now(),
    )
    project.add_demux_info(info)
    with pytest.raises(ValueError):
        project.add_demux_info(info)


def test_add_processing_info(project):
    proc = ProcessingInfo(
        method_name="process1",
        fastq_input=Path("/tmp/input"),
        processing_dir=Path("/tmp/proc"),
        results_dir=Path("/tmp/results"),
        multiqc_report=Path("/tmp/multiqc"),
        status=ProjectStatus.running,
        updated_at=datetime.now(),
    )
    project.add_processing_info(proc)
    assert "process1" in project.processing


def test_add_analysis_info(project):
    analysis = AnalysisInfo(
        template="template1",
        script=Path("/tmp/script.py"),
        output_html=Path("/tmp/out.html"),
        status=ProjectStatus.completed,
    )
    project.add_analysis_info(analysis)
    assert "template1" in project.analysis


def test_add_history(project):
    project.add_history("echo hello")
    assert project.history[0].command == "echo hello"


def test_status_summary(project):
    project.add_demux_info(
        DemultiplexInfo(
            method_name="d1",
            samplesheet_path=Path("/a"),
            raw_date_path=Path("/b"),
            demux_dir=Path("/c"),
            fastq_dir=Path("/d"),
            fastq_multiqc=Path("/e"),
            status=ProjectStatus.running,
            updated_at=datetime.now(),
        )
    )
    summary = project.get_status_summary()
    assert summary["total_templates"] == 1
    assert summary["status_counts"]["running"] == 1
    assert "d1" in summary["template_by_status"]["running"]


def test_retention_check(project):
    assert not project.can_be_cleaned()
    project.set_retenion_date(datetime.now() - timedelta(days=1))
    assert project.can_be_cleaned()


def test_serialize_to_file(tmp_path: Path):
    # Setup a Project instance with sample data
    project_dir = tmp_path / "20230501_NameA_NameB_inst_app"
    project_dir.mkdir()
    project = Project(project_dir=project_dir)

    # Add some demultiplexing info
    demux_info = DemultiplexInfo(
        method_name="method1",
        samplesheet_path=project_dir / "samplesheet.csv",
        raw_date_path=project_dir / "raw_data",
        demux_dir=project_dir / "demux",
        fastq_dir=project_dir / "fastq",
        fastq_multiqc=project_dir / "multiqc.html",
        status=ProjectStatus.running,
        updated_at=datetime.now(),
    )
    project.add_demux_info(demux_info)

    # Serialize to YAML file
    yaml_file = tmp_path / "project.yaml"
    project.serialize_to_file(yaml_file)

    yaml = YAML()
    # Read back the YAML content
    with yaml_file.open() as f:
        data = yaml.load(f)

    # Assertions to verify YAML content
    assert "info" in data
    assert "demultiplexing" in data
    assert "method1" in data["demultiplexing"]
    assert data["demultiplexing"]["method1"]["method_name"] == "method1"
    assert data["demultiplexing"]["method1"]["status"] == ProjectStatus.running.value
    assert "processing" in data
    assert "analysis" in data
    assert "export" in data
    assert "history" in data


@pytest.mark.skip
def test_export_info_url_validation():
    with patch("bpm.core.project_model.Client.head") as mock_head:
        # Simulate 200 OK response
        mock_response = type("obj", (object,), {"status_code": 200})
        mock_head.return_value.__aenter__.return_value = mock_response

        export = ExportInfo.model_validate(
            {
                "export_dir": "/tmp/export",
                "apache_url": "http://localhost/apache",
                "report_url": "http://localhost/report",
                "cloud_export_url": "http://localhost/cloud",
                "export_use": "reporting",
                "export_password": SecretStr("secret"),
                "status": "pending",
            }
        )

        assert export.apache_url == HttpUrl("http://localhost/apache")
        assert export.status == ProjectStatus.pending
