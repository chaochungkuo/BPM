from pathlib import Path
from typing import Any, Dict

def get_cwd(inputs: Dict[str, Any]) -> Path:
    """Get the current working directory."""
    return Path.cwd()
