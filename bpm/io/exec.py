from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Sequence


class ProcessError(RuntimeError):
    """Raised when a subprocess returns non-zero, with captured stdout/stderr."""


def run_process(cmd: Sequence[str], cwd: Path) -> None:
    """
    Run a command and fail with stdout/stderr if it exits non-zero.

    Args:
        cmd: Command vector (e.g., ["./run.sh"]).
        cwd: Working directory to execute in.

    Raises:
        ProcessError: if returncode != 0, includes stdout/stderr.
    """
    res = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    if res.returncode != 0:
        msg = f"Command failed: {' '.join(cmd)}\n--- stdout ---\n{res.stdout}\n--- stderr ---\n{res.stderr}"
        raise ProcessError(msg)