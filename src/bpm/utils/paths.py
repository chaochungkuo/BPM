"""
Path resolution utilities
"""
from pathlib import Path
from typing import Dict, Optional
from bpm.core.config import get_bpm_config
import socket

HOST_PREFIXES = get_bpm_config("main.yaml", "host_paths")

def resolve_path(input_path: str, base_dir: Optional[str] = None) -> str:
    """
    Resolve a host-aware path string to a concrete filesystem path.
    
    Args:
        input_path: Path string that may include host prefix (e.g., "nextgen:/data/raw")
        base_dir: Optional base directory for relative paths
        
    Returns:
        str: Resolved absolute path as a string
        
    Examples:
        >>> resolve_path("nextgen:/data/raw/data1")
        '/mnt/nextgen/data/raw/data1'
        >>> resolve_path("nextgen:../data1", base_dir="/home/user/project")
        '/mnt/nextgen/data1'
    """
    local_host = socket.gethostname()
    
    # Detect and split host:path syntax
    if ":" in input_path and not Path(input_path).drive:  # skip Windows drive letters
        host, path_part = input_path.split(":", 1)
    else:
        host = local_host
        path_part = input_path

    path = Path(path_part)
    
    if host == local_host:
        # Local path resolution
        if path.is_absolute():
            return str(path.resolve())
        else:
            base = Path(base_dir or Path.cwd())
            return str((base / path).resolve())
    else:
        # Remote host, resolve with prefix
        if host not in HOST_PREFIXES:
            raise ValueError(f"Unknown host prefix for '{host}'")
        prefix = Path(HOST_PREFIXES[host])
        return str((prefix / path).resolve())