"""Integration tests for the bclconvert template."""
import pytest
from pathlib import Path
import subprocess
from .conftest import verify_file_content, verify_directory_structure

def test_bclconvert_success(temp_project_dir, temp_output_dir):
    """Test successful bclconvert template execution."""
    # Prepare test data
    fastq_dir = temp_project_dir / "fastq"
    fastq_dir.mkdir()
    
    # Create test FASTQ files
    (fastq_dir / "test_R1.fastq.gz").touch()
    (fastq_dir / "test_R2.fastq.gz").touch()
    
    # Run template command
    cmd = [
        "bpm", "generate", "demultiplexing.bclconvert",
        "--project-yaml", str(temp_project_dir / "project.yaml"),
        "--fastq-dir", str(fastq_dir),
        "--output-dir", str(temp_output_dir),
        "--threads", "4"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    # Verify outputs
    expected_files = [
        "script.sh",
        "config.json",
        "README.md"
    ]
    verify_directory_structure(temp_output_dir, expected_files)
    
    # Verify script content
    verify_file_content(
        temp_output_dir / "script.sh",
        {
            "input_dir": str(fastq_dir),
            "threads": "4",
            "output_dir": str(temp_output_dir)
        }
    )
    
    # Verify config content
    verify_file_content(
        temp_output_dir / "config.json",
        {
            "input_dir": str(fastq_dir),
            "threads": 4,
            "output_dir": str(temp_output_dir)
        }
    )

def test_bclconvert_missing_input(temp_project_dir, temp_output_dir):
    """Test bclconvert template with missing required input."""
    cmd = [
        "bpm", "generate", "demultiplexing.bclconvert",
        "--project-yaml", str(temp_project_dir / "project.yaml"),
        "--output-dir", str(temp_output_dir)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode != 0
    assert "Required input not found: fastq_dir" in result.stderr

def test_bclconvert_invalid_input(temp_project_dir, temp_output_dir):
    """Test bclconvert template with invalid input."""
    cmd = [
        "bpm", "generate", "demultiplexing.bclconvert",
        "--project-yaml", str(temp_project_dir / "project.yaml"),
        "--fastq-dir", "nonexistent/dir",
        "--output-dir", str(temp_output_dir)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode != 0
    assert "Directory not found" in result.stderr 