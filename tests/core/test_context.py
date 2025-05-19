"""Unit tests for the Context class."""
import pytest
from pathlib import Path
import tempfile
import yaml
from datetime import datetime
from bpm.core.context import Context, ContextError
from bpm.core.project import Project

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
            }
        }
        
        project_file = Path(temp_dir) / "project.yaml"
        with open(project_file, 'w') as f:
            yaml.dump(project_data, f)
        
        yield project_file

@pytest.fixture
def mock_config(monkeypatch):
    """Mock config values."""
    def mock_get_bpm_config(filename, key=None):
        if filename == "environment.yaml":
            return {
                'PATH': '/usr/bin:/bin',
                'HOME': '/home/user',
                'TEMP_DIR': '/tmp'
            }
        elif filename == "main.yaml":
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
    
    monkeypatch.setattr('bpm.core.context.get_bpm_config', mock_get_bpm_config)
    monkeypatch.setattr('bpm.core.project.get_bpm_config', mock_get_bpm_config)

def test_context_init(mock_config):
    """Test context initialization."""
    # Test with no parameters
    context = Context()
    assert context.cli_params == {}
    assert context.project is None
    assert context.environment == {}
    
    # Test with CLI parameters
    cli_params = {'output_dir': 'results', 'threads': 4}
    context = Context(cli_params=cli_params)
    assert context.cli_params == cli_params
    
    # Test with project
    project = Project()
    context = Context(project=project)
    assert context.project == project
    
    # Test with environment
    context = Context(environment=True)
    assert hasattr(context, 'environment')

def test_context_access(temp_project_dir, mock_config):
    """Test parameter access methods."""
    project = Project(temp_project_dir)
    cli_params = {'output_dir': 'results', 'threads': 4}
    context = Context(cli_params=cli_params, project=project, environment=True)
    
    # Test CLI parameter access
    assert context['output_dir'] == 'results'
    assert context['threads'] == 4
    
    # Test project parameter access
    assert context['project.name'] == 'test_project'
    assert context['demultiplexing.bclconvert.status'] == 'completed'
    
    # Test environment variable access
    assert context['PATH'] == '/usr/bin:/bin'
    assert context['HOME'] == '/home/user'
    
    # Test parameter precedence (CLI > Project > Environment)
    context.cli_params['PATH'] = '/custom/path'
    assert context['PATH'] == '/custom/path'
    
    # Test nonexistent parameter
    with pytest.raises(ContextError):
        _ = context['nonexistent']

def test_context_get(temp_project_dir, mock_config):
    """Test get method with default values."""
    project = Project(temp_project_dir)
    context = Context(project=project, environment=True)
    
    # Test existing parameter
    assert context.get('project.name') == 'test_project'
    
    # Test nonexistent parameter with default
    assert context.get('nonexistent', 'default') == 'default'
    
    # Test None default
    assert context.get('nonexistent') is None

def test_context_update():
    """Test parameter updates."""
    context = Context()
    
    # Test initial update
    context.update({'key1': 'value1', 'key2': 'value2'})
    assert context['key1'] == 'value1'
    assert context['key2'] == 'value2'
    
    # Test update with existing keys
    context.update({'key1': 'new_value'})
    assert context['key1'] == 'new_value'
    assert context['key2'] == 'value2'

def test_context_get_all(temp_project_dir, mock_config):
    """Test getting all parameters."""
    project = Project(temp_project_dir)
    cli_params = {'output_dir': 'results'}
    context = Context(cli_params=cli_params, project=project, environment=True)
    
    all_params = context.get_all()
    
    # Check CLI parameters
    assert all_params['output_dir'] == 'results'
    
    # Check project parameters
    assert all_params['project.name'] == 'test_project'
    assert all_params['demultiplexing.bclconvert.status'] == 'completed'
    
    # Check environment variables
    assert all_params['PATH'] == '/usr/bin:/bin'
    assert all_params['HOME'] == '/home/user'

def test_context_validate_required(temp_project_dir, mock_config):
    """Test required parameter validation."""
    project = Project(temp_project_dir)
    context = Context(project=project, environment=True)
    
    # Test all required parameters present
    is_valid, missing = context.validate_required(['project.name', 'PATH'])
    assert is_valid
    assert len(missing) == 0
    
    # Test missing parameters
    is_valid, missing = context.validate_required(['nonexistent1', 'nonexistent2'])
    assert not is_valid
    assert len(missing) == 2
    assert 'nonexistent1' in missing
    assert 'nonexistent2' in missing
    
    # Test mixed case
    is_valid, missing = context.validate_required(['project.name', 'nonexistent'])
    assert not is_valid
    assert len(missing) == 1
    assert 'nonexistent' in missing
