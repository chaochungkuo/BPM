"""Path utilities for BPM.

This module provides path-related utilities for BPM, including:
- Basic path resolution
- Directory management
- Cache directory handling
- Host-aware path conversion
"""

from .paths import (
    resolve,
    ensure_dir,
    ensure_parent_dir,
    get_cachedir,
    path,
    HostPathSolver,
    host_solver,
)

__all__ = [
    "resolve",
    "ensure_dir",
    "ensure_parent_dir",
    "get_cachedir",
    "path",
    "HostPathSolver",
    "host_solver",
] 