from __future__ import annotations
import io
import os
from pathlib import Path
from typing import Any
import yaml
from bpm.utils.errors import YamlError


def safe_load_yaml(path: str | Path) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        raise YamlError(f"Failed to read YAML: {path}: {e}") from e


def safe_dump_yaml(path: str | Path, data: Any) -> None:
    """Atomic write to prevent partial files."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            yaml.safe_dump(data, f, sort_keys=False)
        os.replace(tmp, path)  # atomic on POSIX
    except Exception as e:
        # try to clean temp
        try:
            if tmp.exists():
                tmp.unlink()
        finally:
            raise YamlError(f"Failed to write YAML: {path}: {e}") from e