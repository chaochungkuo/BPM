"""Project management for BPM.

This package provides functionality for managing bioinformatics projects.
"""

from bpm.core.project.models import BasicInfo, History, ProjectStatus
from bpm.core.project.operations import Project, ProjectNameValidator, ProjectNameExtractor

__all__ = [
    "BasicInfo",
    "History",
    "ProjectStatus",
    "Project",
    "ProjectNameValidator",
    "ProjectNameExtractor",
] 