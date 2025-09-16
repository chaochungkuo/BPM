"""BPM package metadata and version helper.

Single source of truth for the version lives in bpm/_version.py.
pyproject.toml reads it via [tool.setuptools.dynamic].
"""

from __future__ import annotations

from ._version import __version__  # re-export for consumers
