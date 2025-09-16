import os
from pathlib import Path
import pytest

from bpm.io.exec import run_process, ProcessError


def test_run_process_raises_on_nonzero(tmpdir, monkeypatch):
    # Create a tiny shell script that fails
    p = Path(tmpdir) / "fail.sh"
    p.write_text("#!/usr/bin/env bash\nexit 3\n")
    os.chmod(p, 0o755)

    with pytest.raises(ProcessError):
        run_process(["./fail.sh"], cwd=Path(tmpdir))

