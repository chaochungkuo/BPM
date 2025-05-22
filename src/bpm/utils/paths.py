"""
Path resolution utilities
"""
from pathlib import Path
from typing import Dict, Optional
from rich import print
from bpm.core.config import get_bpm_config
import socket
import warnings

HOST_PREFIXES = get_bpm_config("main.yaml", "host_paths")

def to_host_path(input_path: str, host: Optional[str] = None) -> str:
    """
    Convert a simple path to host-aware format using current hostname.
    
    Args:
        input_path: Simple path string (e.g., "/data/raw/data1")
        host: Optional host name to override current hostname
        
    Returns:
        str: Host-aware path string (e.g., "nextgen:/data/raw/data1")
        
    Examples:
        >>> to_host_path("/data/raw/data1")
        'current-host:/data/raw/data1'
        >>> to_host_path("data1", host="nextgen")
        'nextgen:data1'
    """
    # Use provided host or current hostname
    host = host or socket.gethostname()
    
    # Warn if host not in known prefixes
    if host not in HOST_PREFIXES:
        print(f"[bright_red]Warning: Host '{host}' not found in known hosts: {list(HOST_PREFIXES.keys())}. Path resolution might fail.[/bright_red]")
    
    # Normalize path
    path = Path(input_path)
    path_str = str(path)
        
    return f"{host}:{path_str}"

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