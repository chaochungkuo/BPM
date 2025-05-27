"""Helper functions for testing hook functions."""
from pathlib import Path
from typing import Dict, Any

def create_test_directory(base_path: Path, files: Dict[str, Any]) -> Path:
    """Create files in a directory from a dictionary.
    
    Args:
        base_path: Base path to create files in
        files: Dictionary mapping file paths to content (None for empty files)
        
    Returns:
        Path to the created directory
        
    Example:
        files = {
            'file1.txt': None,  # Empty file
            'subdir/file2.txt': 'content'  # File with content
        }
    """
    for path, content in files.items():
        file_path = base_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if content is None:
            file_path.touch()
        else:
            file_path.write_text(str(content))
    
    return base_path
