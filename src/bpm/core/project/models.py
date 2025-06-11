"""Project data models for BPM.

This module defines the core data structures for project information and history.
"""

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

class ProjectStatus(StrEnum):
    """Enumeration of possible project statuses.
    
    Attributes:
        not_started: Project has been created but not started
        running: Project is currently being processed
        pending: Project is waiting for resources or dependencies
        completed: Project has finished successfully
        failed: Project encountered an error and failed
    """
    not_started = "not_started"
    running = "running"
    pending = "pending"
    completed = "completed"
    failed = "failed"


class BasicInfo(BaseModel):
    """Basic project information model.
    
    This model stores essential project metadata including directory, date,
    and authorship information. If the project directory name starts with
    YYMMDD, it will extract the date.

    Attributes:
        project_dir: Path to project directory
        project_date: Project start date (extracted if directory name starts with YYMMDD)
        authors: List of project authors
        created_at: Project creation timestamp
        retention_until: Project retention deadline
    """
    project_dir: Path
    project_name: str | None = None
    project_date: str | None = None
    authors: list[str] | None = None
    created_at: datetime = datetime.now()
    retention_until: datetime | None = None


class History(BaseModel):
    """Command history model.
    
    Tracks executed commands with timestamps.

    Attributes:
        command: Executed command string
        date: Command execution timestamp
    """
    entry: str