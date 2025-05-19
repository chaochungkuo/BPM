"""Unit tests for the Template class."""
import pytest
from pathlib import Path
import tempfile
import yaml
import shutil
from datetime import datetime
from bpm.core.template import (
    Template, TemplateError, TemplateValidationError,
    TemplateRenderError, TemplateNotFoundError
)
from bpm.core.config import get_bpm_config
from bpm.core.context import Context

@pytest.fixture
def temp_template_dir():
    """Create a temporary directory with test template files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create template directory structure
        template_dir = Path(temp_dir) / "demultiplexing" / "bclconvert"
        template_dir.mkdir(parents=True)
        
        # Create template_config.yaml
        config_data = {
            'inputs': {
                'fastq_dir': {
                    'path': 'demultiplexing.bclconvert.fastq_dir',
                    'required': True,
                    'type': 'string'
                },
                'threads': {
                    'path': 'demultiplexing.bclconvert.threads',
                    'required': False,
                    'type': 'integer'
                }
            },
            'outputs': {
                'report': {
                    'path': 'demultiplexing.bclconvert.report',
                    'value': '{{ output_dir }}/report.html',
                    'type': 'path'
                }
            },
            'required_programs': ['bcl-convert']
        }
        
        with open(template_dir / "template_config.yaml", 'w') as f:
            yaml.dump(config_data, f)
        
        # Create template files
        with open(template_dir / "script.sh", 'w') as f:
            f.write("""#!/bin/bash
# Process FASTQ files
input_dir="{{ fastq_dir }}"
threads="{{ threads | default(4) }}"
output_dir="{{ output_dir }}"
""")
        
        with open(template_dir / "config.json", 'w') as f:
            f.write("""{
    "input_dir": "{{ fastq_dir }}",
    "threads": {{ threads | default(4) }},
    "output_dir": "{{ output_dir }}"
}""")
        
        # Create a non-template file
        with open(template_dir / "README.md", 'w') as f:
            f.write("# BCL Convert Template\nThis is a test template.")
        
        yield template_dir

@pytest.fixture
def mock_config(monkeypatch):
    """Mock config values."""
    def mock_get_bpm_config(filename, key=None):
        if filename == "main.yaml":
            if key == "templates_dir":
                return {
                    "default": "bpm.templates",
                    "user": [],
                    "user_only": False
                }
            elif key == "template_files_rendered":
                return {
                    "formats": [".sh", ".json", ".yaml", ".yml"]
                }
            elif key == "environment":
                return {
                    "PATH": "/usr/bin:/bin",
                    "HOME": "/home/user",
                    "TEMP_DIR": "/tmp"
                }
        return None
    
    monkeypatch.setattr('bpm.core.template.get_bpm_config', mock_get_bpm_config)

@pytest.fixture
def mock_importlib(monkeypatch, temp_template_dir):
    """Mock importlib.resources.files."""
    def mock_files(package):
        class MockPath:
            def __init__(self, path):
                # Return the parent directory of the template directory
                # This simulates the base templates directory
                self._paths = [str(temp_template_dir.parent.parent)]
        return MockPath(str(package))
    
    monkeypatch.setattr('bpm.core.template.files', mock_files)

def test_template_init(temp_template_dir, mock_config, mock_importlib):
    """Test template initialization."""
    # Test successful initialization
    template = Template("demultiplexing.bclconvert")
    assert template.full_name == "demultiplexing.bclconvert"
    assert template.section == "demultiplexing"
    assert template.name == "bclconvert"
    assert template.template_dir == temp_template_dir
    
    # Test template not found
    with pytest.raises(TemplateNotFoundError):
        Template("nonexistent.template")

def test_template_config_loading(temp_template_dir, mock_config, mock_importlib):
    """Test template configuration loading."""
    template = Template("demultiplexing.bclconvert")
    
    # Check config structure
    assert "inputs" in template.config
    assert "outputs" in template.config
    assert "required_programs" in template.config
    
    # Check input configuration
    assert "fastq_dir" in template.config["inputs"]
    assert template.config["inputs"]["fastq_dir"]["required"]
    
    # Check output configuration
    assert "report" in template.config["outputs"]
    assert template.config["outputs"]["report"]["type"] == "path"

def test_template_input_loading(temp_template_dir, mock_config, mock_importlib):
    """Test template input loading."""
    template = Template("demultiplexing.bclconvert")
    
    # Create context with test values
    context = Context(environment=True)
    context.update({"fastq_dir": "/path/to/fastq", "threads": 8})
    
    # Test valid inputs
    template.load_inputs(context)
    assert template.inputs["fastq_dir"] == "/path/to/fastq"
    # assert template.inputs["threads"] == 8
    
    # Test missing required input
    context = Context(environment=True)  # Empty context
    context.update({"threads": 8})
    with pytest.raises(TemplateValidationError):
        template.load_inputs(context)
    
    # Test optional input
    context = Context(environment=True)
    context.update({"fastq_dir": "/path/to/fastq"})
    template.load_inputs(context)
    # assert "threads" not in template.inputs

def test_template_rendering(temp_template_dir, mock_config, mock_importlib):
    """Test template rendering."""
    template = Template("demultiplexing.bclconvert")
    
    # Create target directory
    with tempfile.TemporaryDirectory() as target_dir:
        target_path = Path(target_dir)
        
        # Create context with test values
        context = Context(environment=True)
        context.update({
            "fastq_dir": "/path/to/fastq",
            "threads": 8,
            "output_dir": "/path/to/output"
        })
        
        # Render template
        template.render(target_path, context.get_all())
        
        # Check rendered files
        assert (target_path / "script.sh").exists()
        assert (target_path / "config.json").exists()
        assert (target_path / "README.md").exists()
        
        # Check rendered content
        with open(target_path / "script.sh") as f:
            content = f.read()
            assert 'input_dir="/path/to/fastq"' in content
            assert 'threads="8"' in content
        
        with open(target_path / "config.json") as f:
            content = f.read()
            assert '"input_dir": "/path/to/fastq"' in content
            assert '"threads": 8' in content
        
        # Check non-template file
        with open(target_path / "README.md") as f:
            content = f.read()
            assert "# BCL Convert Template" in content


def test_template_error_handling(temp_template_dir, mock_config, mock_importlib):
    """Test template error handling."""
    # Test invalid template name
    with pytest.raises(ValueError):
        Template("invalid")
    
    # Test missing template config
    config_path = temp_template_dir / "template_config.yaml"
    config_path.unlink()  # Delete the file instead of using rmtree
    with pytest.raises(TemplateError):
        Template("demultiplexing.bclconvert")
    
    # Test invalid template config
    with open(temp_template_dir / "template_config.yaml", 'w') as f:
        f.write("invalid: yaml: content")
    with pytest.raises(TemplateError):
        Template("demultiplexing.bclconvert")
    
