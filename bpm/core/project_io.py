from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional

from bpm.io.yamlio import safe_dump_yaml, safe_load_yaml


PROJECT_FILENAME = "project.yaml"


def project_file_path(project_dir: Path) -> Path:
    """
    Path helper: points to <project_dir>/project.yaml
    """
    return project_dir / PROJECT_FILENAME


def load(project_dir: Path) -> Dict[str, Any]:
    """
    Load an existing project.yaml from a directory.

    Args:
        project_dir: Folder containing project.yaml

    Returns:
        Parsed dict (never None).

    Raises:
        FileNotFoundError: if project.yaml is absent.
    """
    p = project_file_path(project_dir)
    if not p.exists():
        raise FileNotFoundError(f"project.yaml not found in {project_dir}")
    return safe_load_yaml(p)


def save(project_dir: Path, data: Dict[str, Any]) -> None:
    """
    Write (or overwrite) project.yaml to a directory.

    Args:
        project_dir: Project directory (created if missing).
        data: The project dictionary to serialize.

    Behavior:
        - Creates directory if needed.
        - Writes human-readable YAML with stable key order (PyYAML default).
    """
    project_dir.mkdir(parents=True, exist_ok=True)
    safe_dump_yaml(project_file_path(project_dir), data)