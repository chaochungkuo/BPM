from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Sequence


class ProcessError(RuntimeError):
    """Raised when a subprocess returns non-zero."""


def run_process(cmd: Sequence[str], cwd: Path) -> None:
    """
    Run a command, streaming stdout/stderr live to the console.

    - No output is hidden. On failure, raise ProcessError with a terse message
      (the full output has already been printed to the console).

    Args:
        cmd: Command vector (e.g., ["./run.sh"]).
        cwd: Working directory to execute in.

    Raises:
        ProcessError: if the process exits with a non-zero status.
    """
    rc = subprocess.run(cmd, cwd=str(cwd)).returncode
    if rc != 0:
        raise ProcessError(f"Command failed with exit code {rc}: {' '.join(cmd)}")
