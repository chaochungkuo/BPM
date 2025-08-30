from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class StoreRecord:
    id: str
    source: str
    cache_path: str
    version: str
    commit: Optional[str] = None
    last_updated: Optional[str] = None


@dataclass
class StoreIndex:
    schema_version: int = 1
    updated: Optional[str] = None
    active: Optional[str] = None
    stores: Dict[str, StoreRecord] = field(default_factory=dict)