"""Integration tests for the bclconvert template."""
import pytest
from pathlib import Path
import subprocess
from .conftest import verify_file_content, verify_directory_structure

def test_bclconvert_without_project_yaml(temp_project_dir, temp_output_dir):
    """Test successful bclconvert template execution."""
    
    # Run template command
    cmd = [
        "bpm", "generate", "demultiplexing.bclconvert",
        # "--project-yaml", str(temp_project_dir / "project.yaml"),
        "--bcl-path", "PATH_TO_BCL_FILE"
        # "--output-dir", str(temp_output_dir),
        # "--threads", "4"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(temp_project_dir))
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    # # Verify outputs
    # expected_files = [
    #     "run.sh",
    #     "samplesheet.csv"
    # ]
    # verify_directory_structure(temp_project_dir / "PATH_TO_BCL_FILE",
    #                            expected_files)
    

def test_bclconvert_missing_input(temp_project_dir):
    """Test bclconvert template with missing required input."""
    cmd = [
        "bpm", "generate", "demultiplexing.bclconvert"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(temp_project_dir))
    assert result.returncode != 0
    # assert "Required input not found: bcl-path" in result.stderr

# def test_bclconvert_invalid_input(temp_project_dir, temp_output_dir):
#     """Test bclconvert template with invalid input."""
#     cmd = [
#         "bpm", "generate", "demultiplexing.bclconvert",
#         "--project-yaml", str(temp_project_dir / "project.yaml"),
#         "--fastq-dir", "nonexistent/dir",
#         "--output-dir", str(temp_output_dir)
#     ]
    
#     result = subprocess.run(cmd, capture_output=True, text=True)
#     assert result.returncode != 0
#     assert "Directory not found" in result.stderr 