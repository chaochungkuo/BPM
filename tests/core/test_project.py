"""Unit tests for the Project class."""
import pytest
from pathlib import Path
import tempfile
import yaml
from datetime import datetime, timedelta
from bpm.core.project import Project
from bpm.core.config import get_bpm_config

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory with test project files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test project file
        project_data = {
            'project': {
                'name': 'test_project',
                'date': '2024-03-15',
                'project_dir': '/path/to/project',
                'created_at': datetime.now().isoformat()
            },
            'demultiplexing': {
                'bclconvert': {
                    'status': 'completed',
                    'updated_at': datetime.now().isoformat(),
                    'fastq_dir': '/path/to/fastq'
                }
            },
            'history': [
                '240315 14:30 user@host bpm run bclconvert'
            ]
        }
        
        project_file = Path(temp_dir) / "project.yaml"
        with open(project_file, 'w') as f:
            yaml.dump(project_data, f)
        
        yield project_file

@pytest.fixture
def mock_config(monkeypatch):
    """Mock config values."""
    def mock_get_bpm_config(filename, key=None):
        if key == "project_base":
            return {
                'project': {
                    'name': '',
                    'date': '',
                    'project_dir': ''
                }
            }
        elif key == "template_status.statuses":
            return ['completed', 'running', 'failed']
        return None
    
    monkeypatch.setattr('bpm.core.project.get_bpm_config', mock_get_bpm_config)

def test_project_init_new(mock_config):
    """Test initializing a new project."""
    project = Project()
    assert 'project' in project.data
    assert 'created_at' in project.data['project']
    assert project.data['project']['name'] == ''

def test_project_init_existing(temp_project_dir):
    """Test initializing with existing project file."""
    project = Project(temp_project_dir)
    assert project.data['project']['name'] == 'test_project'
    assert 'demultiplexing' in project.data
    assert 'history' in project.data

def test_project_init_nonexistent():
    """Test initializing with nonexistent file."""
    with pytest.raises(FileNotFoundError):
        Project("nonexistent.yaml")

def test_project_save(temp_project_dir):
    """Test saving project file."""
    project = Project(temp_project_dir)
    project.update_value("project.name", "updated_name")
    
    # Save to new file
    new_file = temp_project_dir.parent / "new_project.yaml"
    project.save(new_file)
    
    # Load and verify
    new_project = Project(new_file)
    assert new_project.get_value("project.name") == "updated_name"

def test_template_status(temp_project_dir, mock_config):
    """Test template status management."""
    project = Project(temp_project_dir)
    
    # Get status
    status = project.get_template_status("demultiplexing", "bclconvert")
    assert status == "completed"
    
    # Update status
    project.update_template_status("demultiplexing", "bclconvert", "running")
    assert project.get_template_status("demultiplexing", "bclconvert") == "running"
    
    # Test invalid status
    with pytest.raises(ValueError):
        project.update_template_status("demultiplexing", "bclconvert", "invalid")

def test_value_management(temp_project_dir):
    """Test value get/set operations."""
    project = Project(temp_project_dir)
    
    # Get value
    fastq_dir = project.get_value("demultiplexing.bclconvert.fastq_dir")
    assert fastq_dir == "/path/to/fastq"
    
    # Update value
    project.update_value("demultiplexing.bclconvert.fastq_dir", "/new/path")
    assert project.get_value("demultiplexing.bclconvert.fastq_dir") == "/new/path"
    
    # Test nonexistent key
    with pytest.raises(KeyError):
        project.get_value("nonexistent.key")

def test_history_management(temp_project_dir):
    """Test history management."""
    project = Project(temp_project_dir)
    initial_history = len(project.data['history'])
    
    # Add history entry
    project.add_history("bpm run test")
    assert len(project.data['history']) == initial_history + 1
    
    # Verify history format
    last_entry = project.data['history'][-1]
    assert "bpm run test" in last_entry
    assert "@" in last_entry  # Contains user@host

def test_retention_management(temp_project_dir):
    """Test retention date management."""
    project = Project(temp_project_dir)
    
    # Set retention date
    future_date = (datetime.now() + timedelta(days=30)).isoformat()
    project.set_retention_until(future_date)
    assert project.get_value("project.retention_until") == future_date
    
    # Test invalid date
    with pytest.raises(ValueError):
        project.set_retention_until("invalid-date")
    
    # Test can_be_cleaned
    assert not project.can_be_cleaned()  # Future date
    
    # Test past date
    past_date = (datetime.now() - timedelta(days=1)).isoformat()
    project.set_retention_until(past_date)
    assert project.can_be_cleaned()


def test_section_management(temp_project_dir):
    """Test section management."""
    project = Project(temp_project_dir)
    
    # Get section
    demultiplexing = project.get_section("demultiplexing")
    assert "bclconvert" in demultiplexing
    
    # Update section
    project.update_section("demultiplexing", "bclconvert", {"new_key": "value"})
    assert project.get_value("demultiplexing.bclconvert.new_key") == "value"
    
    # Insert new section
    project.insert_section("new_section", {"key": "value"})
    assert "new_section" in project.data
    
    # Test duplicate section
    with pytest.raises(ValueError):
        project.insert_section("new_section", {"key": "value"})
