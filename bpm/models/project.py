from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from .hostpath import HostPath


class ProjectState(str, Enum):
    initiated = "initiated"
    active = "active"
    closed = "closed"


class TemplateStatus(str, Enum):
    active = "active"
    completed = "completed"


@dataclass
class TemplateEntry:
    id: str
    source: Optional[str] = None         # "<brs_id>:<template_id>" later
    brs_commit: Optional[str] = None
    rendered_at: Optional[str] = None    # iso8601
    run_entry: Optional[str] = None
    status: TemplateStatus = TemplateStatus.active
    params: Dict[str, object] = field(default_factory=dict)
    published: Dict[str, object] = field(default_factory=dict)


@dataclass
class Author:
    id: str
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None


@dataclass
class Project:
    schema_version: int
    name: str
    created: str                 # iso8601
    project_path: str            # store as host-aware string in YAML
    authors: List[Author] = field(default_factory=list)
    status: ProjectState = ProjectState.initiated
    templates: List[TemplateEntry] = field(default_factory=list)

    # Convenience helpers for code (not serialized if you handle YAML manually)
    def get_hostpath(self, current_host: str) -> HostPath:
        return HostPath.from_raw(self.project_path, current_host)