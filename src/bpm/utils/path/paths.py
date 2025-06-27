"""Path utilities for BPM.

This module provides path-related utilities for BPM, including:
- Basic path resolution
- Directory management
- Cache directory handling
- Host-aware path conversion
"""

import os
from pathlib import Path
from typing import Union, Dict, Optional
from ..ui.console import BPMConsole

console = BPMConsole()

class HostPathSolver:
    """Solver for host-aware paths.
    
    This class manages the conversion between physical paths and host:path format.
    It maintains a mapping of host names to their mount points and provides
    methods for path conversion.

    Attributes:
        host_mappings: Dictionary mapping host names to their mount points
    """
    __slots__ = ["host_mappings"]

    def __init__(self, host_mappings: Optional[Dict[str, str]] = None) -> None:
        """Initialize host path solver.
        
        Args:
            host_mappings: Optional dictionary of host mappings
        """
        self.host_mappings = host_mappings or {}

    def update_mappings(self, host_mappings: Dict[str, str]) -> None:
        """Update host mappings.
        
        Args:
            host_mappings: Dictionary mapping host names to their mount points
        """
        self.host_mappings = host_mappings

    def from_path_to_hostpathstr(self, path: Path) -> str:
        """Convert a path to host:path format.
        
        Args:
            path: Path to convert
            
        Returns:
            Path in format host:path or original path if no host match
        """
        path = path.absolute()
        # Try to match against host mappings
        for hostname, mount_point in self.host_mappings.items():
            # path has prefix of mount_point
            if mount_point != "":
                mount_point = str(mount_point)
                if str(path).startswith(mount_point):
                    # Remove mount point and return host:path format
                    relative_path = str(path)[len(mount_point):]
                    return f"{hostname}:{relative_path}"
            elif mount_point == "":
                return f"{hostname}:{str(path)}"

    def from_hostpathstr_to_path(self, host_path: str) -> Path:
        """Convert from host:path format to full path.
        
        Args:
            host_path: Path in format host:path
            
        Returns:
            Full Path object
            
        Raises:
            ValueError: If host is not found in mappings
        """
        if isinstance(host_path, str) and ":" in host_path:
            # host_path is a string in format host:path
            host, path = host_path.split(":", 1)
            if host not in self.host_mappings:
                raise ValueError(f"Unknown host: {host}")
            path = Path(path).resolve()
            mount_point = Path(self.host_mappings[host])
            if mount_point:
                return mount_point / path
            else:
                return path
        elif isinstance(host_path, str) and ":" not in host_path:
            # skip if host_path is a string and does not contain ":"
            absolute_path = Path(host_path).resolve()
            return absolute_path
        else:
            raise ValueError(f"Unknown host path: {host_path}")
                

    def get_host_mappings(self) -> Dict[str, str]:
        """Get current host mappings.
        
        Returns:
            Dictionary of host mappings
        """
        return self.host_mappings.copy()

def resolve(path: Union[str, Path]) -> Path:
    """Resolve a path to an absolute path.
    
    Args:
        path: Path to resolve
        
    Returns:
        Resolved absolute path
    """
    return Path(path).resolve()

def ensure_dir(path: Path) -> None:
    """Ensure a directory exists.
    
    Args:
        path: Directory path to ensure exists
    """
    path.mkdir(parents=True, exist_ok=True)

def ensure_parent_dir(path: Path) -> None:
    """Ensure parent directory of a path exists.
    
    Args:
        path: Path whose parent directory should exist
    """
    path.parent.mkdir(parents=True, exist_ok=True)

def get_cachedir() -> Path:
    """Get BPM cache directory.
    
    Returns:
        Path to cache directory
        
    Note:
        Checks BPM_CACHE environment variable first,
        falls back to ~/.cache/bpm if not set
    """
    cache_dir = os.environ.get("BPM_CACHE")
    if cache_dir:
        return Path(cache_dir)
    return Path.home() / ".cache" / "bpm"

# Create singleton instances for convenience
path = Path()
host_solver = HostPathSolver() 