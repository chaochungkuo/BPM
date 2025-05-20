"""Unit tests for the config module."""
import pytest
from pathlib import Path
import yaml
import tempfile
import importlib.resources
from bpm.core.config import get_bpm_config, flatten_dict

@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory with test config files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create config directory
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        # Create test config file
        test_config = {
            "templates_dir": {
                "default": "templates",
                "user_only": False
            },
            "template_status": {
                "statuses": {
                    "completed": "completed",
                    "failed": "failed",
                    "running": "running"
                }
            },
            "template_files_rendered": {
                "formats": [".sh", ".yaml", ".json", ".txt"]
            },
            "nested": {
                "level1": {
                    "level2": {
                        "level3": "deep_value"
                    }
                }
            }
        }
        
        config_file = config_dir / "main.yaml"
        with open(config_file, "w") as f:
            yaml.dump(test_config, f)
        
        yield config_dir

def test_get_bpm_config_valid(temp_config_dir, monkeypatch):
    """Test getting valid config values."""
    # Mock importlib.resources.files to return our test config directory
    def mock_files(package):
        return temp_config_dir
    
    monkeypatch.setattr(importlib.resources, "files", mock_files)
    
    # Test simple key
    assert get_bpm_config("main.yaml", "templates_dir.default") == "templates"
    
    # Test boolean value
    assert get_bpm_config("main.yaml", "templates_dir.user_only") is False
    
    # Test nested key
    assert get_bpm_config("main.yaml", "template_status.statuses.completed") == "completed"
    
    # Test list value
    assert get_bpm_config("main.yaml", "template_files_rendered.formats") == [".sh", ".yaml", ".json", ".txt"]
    
    # Test deeply nested value
    assert get_bpm_config("main.yaml", "nested.level1.level2.level3") == "deep_value"

def test_get_bpm_config_invalid(temp_config_dir, monkeypatch):
    """Test getting invalid config values."""
    # Mock importlib.resources.files to return our test config directory
    def mock_files(package):
        return temp_config_dir
    
    monkeypatch.setattr(importlib.resources, "files", mock_files)
    
    # Test non-existent key
    with pytest.raises(KeyError, match="Config key not found: invalid.key"):
        get_bpm_config("main.yaml", "invalid.key")
    
    # Test non-existent nested key
    with pytest.raises(KeyError, match="Config key not found: templates_dir.missing"):
        get_bpm_config("main.yaml", "templates_dir.missing")
    
    # Test non-existent file
    with pytest.raises(FileNotFoundError, match="Config file not found: nonexistent.yaml"):
        get_bpm_config("nonexistent.yaml", "templates_dir.default")

def test_get_bpm_config_invalid_yaml(temp_config_dir, monkeypatch):
    """Test behavior with invalid YAML content."""
    # Mock importlib.resources.files to return our test config directory
    def mock_files(package):
        return temp_config_dir
    
    monkeypatch.setattr(importlib.resources, "files", mock_files)
    
    # Create a file with invalid YAML
    invalid_file = temp_config_dir / "invalid.yaml"
    with open(invalid_file, "w") as f:
        f.write("invalid: yaml: content: [")
    
    # Test invalid YAML
    with pytest.raises(yaml.YAMLError):
        get_bpm_config("invalid.yaml", "some.key")

def test_get_bpm_config_empty_file(temp_config_dir, monkeypatch):
    """Test behavior with empty config file."""
    # Mock importlib.resources.files to return our test config directory
    def mock_files(package):
        return temp_config_dir
    
    monkeypatch.setattr(importlib.resources, "files", mock_files)
    
    # Create an empty file
    empty_file = temp_config_dir / "empty.yaml"
    empty_file.touch()
    
    # Test empty file
    with pytest.raises(KeyError, match="Config key not found: some.key"):
        get_bpm_config("empty.yaml", "some.key")

def test_get_bpm_config_full(temp_config_dir, monkeypatch):
    """Test getting full config with nested structure."""
    # Mock importlib.resources.files to return our test config directory
    def mock_files(package):
        return temp_config_dir
    
    monkeypatch.setattr(importlib.resources, "files", mock_files)
    
    # Get full config
    config = get_bpm_config("main.yaml")
    
    # Test nested structure
    assert isinstance(config, dict)
    assert "templates_dir" in config
    assert "template_status" in config
    assert "nested" in config
    
    # Test nested values
    assert config["templates_dir"]["default"] == "templates"
    assert config["templates_dir"]["user_only"] is False
    assert config["template_status"]["statuses"]["completed"] == "completed"
    assert config["nested"]["level1"]["level2"]["level3"] == "deep_value"
    assert config["template_files_rendered"]["formats"] == [".sh", ".yaml", ".json", ".txt"]

def test_flatten_dict():
    """Test the flatten_dict function directly."""
    test_dict = {
        "a": {
            "b": {
                "c": "value1"
            },
            "d": "value2"
        },
        "e": "value3"
    }
    
    flattened = flatten_dict(test_dict)
    
    assert isinstance(flattened, dict)
    assert "a.b.c" in flattened
    assert "a.d" in flattened
    assert "e" in flattened
    assert flattened["a.b.c"] == "value1"
    assert flattened["a.d"] == "value2"
    assert flattened["e"] == "value3"
