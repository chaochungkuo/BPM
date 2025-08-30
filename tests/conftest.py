import os
import shutil
import tempfile
from pathlib import Path
import pytest

@pytest.fixture()
def tmpdir():
    d = Path(tempfile.mkdtemp(prefix="bpm-day1-"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)

@pytest.fixture()
def hosts_cfg():
    # minimal hosts mapping for HostPath.materialize
    return {
        "nextgen": {"mount_prefix": "/mnt/nextgen"},
        "web": {"mount_prefix": "/mnt/web"},
    }