from __future__ import annotations
import os
import shutil
from pathlib import Path


def mkdirp(path: str | Path) -> None:
    """
    Create a directory (and parents) if missing. No-op if it exists.
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def copy_file(src: str | Path, dst: str | Path) -> None:
    """
    Copy a file with metadata. Creates destination parent directories.
    """
    src = Path(src)
    dst = Path(dst)
    mkdirp(dst.parent)
    shutil.copy2(src, dst)


def write_text(path: str | Path, text: str) -> None:
    """
    Write text to a file, creating parent directories if needed.
    """
    path = Path(path)
    mkdirp(path.parent)
    path.write_text(text, encoding="utf-8", newline="\n")


def make_executable(path: str | Path) -> None:
    """
    Add execute bits (u/g/o) to a file if it exists.
    """
    p = Path(path)
    if not p.exists():
        return
    mode = p.stat().st_mode
    # add x for user/group/other
    p.chmod(mode | 0o111)