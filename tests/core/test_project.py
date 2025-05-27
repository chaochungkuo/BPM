"""Unit tests for the Project class."""
import pytest
from pathlib import Path
import tempfile
from datetime import datetime, timedelta
from bpm.core.project import (
    Project, BasicInfo, DemultiplexInfo, ProcessingInfo, 
    AnalysisInfo, ReportInfo, ExportInfo, History, ProjectStatus
)

@pytest.fixture
def valid_project_dir():
    """Create a temporary directory with valid project name."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir) / "230101_Test_Project_GF_RNAseq"
        project_dir.mkdir()
        yield project_dir

@pytest.fixture
def project(valid_project_dir):
    """Create a Project instance with valid directory."""
    return Project(valid_project_dir)

def test_project_init_valid(valid_project_dir):
    """Test initializing project with valid directory."""
    project = Project(valid_project_dir)
    assert isinstance(project.info, BasicInfo)
    assert project.info.name == "230101_Test_Project_GF_RNAseq"
    assert project.info.project_date == "230101"
    assert project.info.institute == "GF"
    assert project.info.application == "RNAseq"
    assert project.demultiplexing is None
    assert project.processing == {}
    assert project.analysis == {}
    assert project.report is None
    assert project.export is None
    assert project.history == []

def test_project_init_invalid_format():
    """Test initializing project with invalid name format."""
    with tempfile.TemporaryDirectory() as temp_dir:
        invalid_dir = Path(temp_dir) / "invalid_format"
        invalid_dir.mkdir()
        with pytest.raises(ValueError, match="Invalid project name format"):
            Project(invalid_dir)

def test_project_init_invalid_date():
    """Test initializing project with invalid date format."""
    with tempfile.TemporaryDirectory() as temp_dir:
        invalid_dir = Path(temp_dir) / "CC0101_Test_Test_Project_GF_RNAseq"  # Invalid year
        invalid_dir.mkdir()
        with pytest.raises(ValueError, match="Date Format Error"):
            Project(invalid_dir)

def test_add_demux_info(project):
    """Test adding demultiplexing information."""
    demux_info = DemultiplexInfo(
        method_name="bclconvert",
        samplesheet_path=Path("samplesheet.csv"),
        raw_date_path=Path("raw_data"),
        demux_dir=Path("demux"),
        fastq_dir=Path("fastq"),
        fastq_multiqc=Path("multiqc.html"),
        status=ProjectStatus.not_started
    )
    project.add_demux_info(demux_info)
    assert project.demultiplexing == demux_info

def test_add_processing_info(project):
    """Test adding processing information."""
    processing_info = ProcessingInfo(
        method_name="star",
        fastq_input=Path("fastq"),
        processing_dir=Path("star"),
        results_dir=Path("results"),
        multiqc_report=Path("multiqc.html"),
        status=ProjectStatus.not_started,
        updated_at=datetime.now()
    )
    project.add_processing_info(processing_info)
    assert "star" in project.processing
    assert project.processing["star"] == processing_info

def test_add_analysis_info(project):
    """Test adding analysis information."""
    analysis_info = AnalysisInfo(
        template="differential_expression",
        script=Path("script.R"),
        output_html=Path("report.html"),
        status=ProjectStatus.not_started
    )
    project.add_analysis_info(analysis_info)
    assert "differential_expression" in project.analysis
    assert project.analysis["differential_expression"] == analysis_info

def test_add_history(project):
    """Test adding command history."""
    cmd = "bpm run star"
    project.add_history(cmd)
    assert len(project.history) == 1
    assert project.history[0].command == cmd
    assert isinstance(project.history[0].date, datetime)


def test_serialization(project, tmp_path):
    """Test serializing and deserializing project."""
    # Add some data
    demux_info = DemultiplexInfo(
        method_name="bclconvert",
        samplesheet_path=Path("samplesheet.csv"),
        raw_date_path=Path("raw_data"),
        demux_dir=Path("demux"),
        fastq_dir=Path("fastq"),
        fastq_multiqc=Path("multiqc.html"),
        status=ProjectStatus.completed
    )
    project.add_demux_info(demux_info)
    project.add_history("bpm run bclconvert")
    
    # Serialize
    yaml_path = tmp_path / "project.yaml"
    project.serialize_to_file(yaml_path)
    
    # Deserialize
    new_project = Project(project.info.project_dir)
    new_project.read_from_file(yaml_path)
    
    # Compare
    assert new_project.info.name == project.info.name
    assert new_project.demultiplexing.method_name == project.demultiplexing.method_name
    assert new_project.demultiplexing.status == project.demultiplexing.status
    assert len(new_project.history) == len(project.history)
    assert new_project.history[0].command == project.history[0].command

def test_retention_date(project):
    """Test retention date management."""
    future_date = datetime.now() + timedelta(days=30)
    project.set_retention_date(future_date)
    assert project.info.retention_until == future_date
    assert not project.can_be_cleaned()
    
    past_date = datetime.now() - timedelta(days=1)
    project.set_retention_date(past_date)
    assert project.can_be_cleaned()

def test_add_author(project):
    """Test adding author to project."""
    # Mock config
    def mock_get_bpm_config(filename, key=None):
        if key == "authors":
            return {
                "test_user": {
                    "name": "Test User",
                    "affiliation": "Test Institute",
                    "email": "test@example.com"
                }
            }
        return None
    
    # Apply mock
    import bpm.core.project
    original_get_config = bpm.core.project.get_bpm_config
    bpm.core.project.get_bpm_config = mock_get_bpm_config
    
    try:
        project.add_author("test_user")
        assert len(project.info.authors) == 1
        assert "Test User" in project.info.authors[0]
        assert "Test Institute" in project.info.authors[0]
        assert "test@example.com" in project.info.authors[0]
        
        with pytest.raises(ValueError, match="not in the list of available authors"):
            project.add_author("invalid_user")
    finally:
        # Restore original function
        bpm.core.project.get_bpm_config = original_get_config
