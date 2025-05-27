"""Unit tests for the Context class."""
import pytest
from pathlib import Path
import tempfile
import yaml
from datetime import datetime
from bpm.core.context import Context, ContextError
from bpm.core.project_bk import Project

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
    """Mock config values for main.yaml."""
    def mock_get_bpm_config(filename, key=None):
        if filename == "main.yaml":
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

class TestContextInitialization:
    """Test Context class initialization."""
    
    def test_empty_initialization(self):
        """Test initialization with no parameters."""
        context = Context()
        assert context.cli_params == {}
        assert context.project is None
        assert context.environment == {}
    
    def test_cli_params_initialization(self):
        """Test initialization with CLI parameters."""
        cli_params = {'output_dir': 'results', 'threads': 4}
        context = Context(cli_params=cli_params)
        assert context.cli_params == cli_params
    
    def test_project_initialization(self, temp_project_dir):
        """Test initialization with project."""
        project = Project(temp_project_dir)
        context = Context(project=project)
        assert context.project == project
    
    def test_environment_initialization(self):
        """Test initialization with environment loading."""
        context = Context(environment=True)
        assert hasattr(context, 'environment')
        assert 'tool_paths' in context.environment
        assert 'system' in context.environment

class TestContextAccess:
    """Test parameter access methods."""
    
    def test_cli_param_access(self):
        """Test accessing CLI parameters."""
        cli_params = {'output_dir': 'results', 'threads': 4}
        context = Context(cli_params=cli_params)
        
        # Test direct access
        assert context['output_dir'] == 'results'
        assert context['threads'] == 4
        
        # Test get with default
        assert context.get('nonexistent', 'default') == 'default'
    
    def test_project_param_access(self, temp_project_dir):
        """Test accessing project parameters."""
        project = Project(temp_project_dir)
        context = Context(project=project)
        
        # Test nested access
        assert context['project']['name'] == 'test_project'
        assert context['demultiplexing']['bclconvert']['status'] == 'completed'
        
        # Test dot notation
        assert context['project.name'] == 'test_project'
        assert context['demultiplexing.bclconvert.status'] == 'completed'
    
    def test_environment_access(self):
        """Test accessing environment variables."""
        context = Context(environment=True)
        
        # Test structure
        assert 'tool_paths' in context.environment
        assert 'system' in context.environment
        
        # Test nested access
        assert isinstance(context['tool_paths'], dict)
        assert isinstance(context['system'], dict)
    
    def test_parameter_precedence(self, temp_project_dir):
        """Test parameter precedence (CLI > Project > Environment)."""
        project = Project(temp_project_dir)
        cli_params = {'project.name': 'cli_name'}
        context = Context(cli_params=cli_params, project=project)
        
        assert context['project.name'] == 'cli_name'  # CLI overrides project

class TestContextOperations:
    """Test Context operations."""
    
    def test_update_operation(self):
        """Test updating CLI parameters."""
        context = Context()
        
        # Initial update
        context.update({'key1': 'value1', 'key2': 'value2'})
        assert context['key1'] == 'value1'
        assert context['key2'] == 'value2'
        
        # Update existing key
        context.update({'key1': 'new_value'})
        assert context['key1'] == 'new_value'
        assert context['key2'] == 'value2'
    
    def test_get_all_operation(self, temp_project_dir):
        """Test getting all parameters."""
        project = Project(temp_project_dir)
        cli_params = {'output_dir': 'results'}
        context = Context(cli_params=cli_params, project=project, environment=True)
        
        all_params = context.get_all()
        
        # Check all sources are included
        assert 'output_dir' in all_params  # CLI
        assert 'project' in all_params     # Project
        assert 'tool_paths' in all_params       # Environment
        assert 'system' in all_params      # Environment

class TestContextValidation:
    """Test parameter validation."""
    
    def test_validate_required(self, temp_project_dir):
        """Test required parameter validation."""
        project = Project(temp_project_dir)
        context = Context(project=project, environment=True)
        
        # Test all required parameters present
        is_valid, missing = context.validate_required(['project.name'])
        assert is_valid
        assert len(missing) == 0
        
        # Test missing parameters
        is_valid, missing = context.validate_required(['nonexistent1', 'nonexistent2'])
        assert not is_valid
        assert len(missing) == 2
        assert 'nonexistent1' in missing
        assert 'nonexistent2' in missing
    
    def test_error_handling(self):
        """Test error handling for invalid access."""
        context = Context()
        
        # Test nonexistent parameter
        with pytest.raises(ContextError):
            _ = context['nonexistent']
        
        # Test invalid nested access
        with pytest.raises(ContextError):
            _ = context['invalid.nested.key']

class TestContextEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_dict_access(self):
        """Test accessing empty dictionaries."""
        context = Context(cli_params={})
        with pytest.raises(ContextError):
            _ = context['any_key']
    
    def test_none_values(self):
        """Test handling of None values."""
        context = Context(cli_params={'key': None})
        assert context['key'] is None
    
    def test_complex_nested_access(self, temp_project_dir):
        """Test complex nested dictionary access."""
        project = Project(temp_project_dir)
        context = Context(project=project)
        
        # Test deep nesting
        assert context['demultiplexing.bclconvert.status'] == 'completed'
        assert context['demultiplexing']['bclconvert']['status'] == 'completed'
    
    def test_mixed_access_patterns(self):
        """Test mixing different access patterns."""
        cli_params = {
            'simple': 'value',
            'nested': {'key': 'value'},
            'deep.nested.key': 'value'
        }
        context = Context(cli_params=cli_params)
        
        assert context['simple'] == 'value'
        assert context['nested']['key'] == 'value'
        assert context['deep.nested.key'] == 'value'
