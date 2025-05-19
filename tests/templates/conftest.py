"""Common fixtures for template integration tests."""
import pytest
import tempfile
from pathlib import Path
import shutil
import yaml
from datetime import datetime

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory with a test project."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        
        # Create project.yaml
        project_data = {
            'project': {
                'name': 'test_project',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'project_dir': str(project_dir),
                'created_at': datetime.now().isoformat()
            }
        }
        
        project_file = project_dir / "project.yaml"
        with open(project_file, 'w') as f:
            yaml.dump(project_data, f)
        
        yield project_dir

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for template outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

def verify_file_content(file_path: Path, expected_content: dict):
    """Verify file content matches expected values.
    
    Args:
        file_path: Path to the file to verify
        expected_content: Dictionary of expected content
    """
    assert file_path.exists(), f"File not found: {file_path}"
    
    with open(file_path) as f:
        content = f.read()
        
    for key, value in expected_content.items():
        assert str(value) in content, f"Expected {value} not found in {file_path}"

def verify_directory_structure(dir_path: Path, expected_files: list):
    """Verify directory contains expected files.
    
    Args:
        dir_path: Path to the directory to verify
        expected_files: List of expected file paths relative to dir_path
    """
    assert dir_path.exists(), f"Directory not found: {dir_path}"
    
    for file_path in expected_files:
        full_path = dir_path / file_path
        assert full_path.exists(), f"Expected file not found: {file_path}" 