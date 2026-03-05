from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bpm.core import brs_loader


@dataclass(frozen=True)
class TemplateEntry:
    template_id: str
    descriptor_path: Path


def list_templates() -> list[TemplateEntry]:
    root = brs_loader.get_paths().templates_dir
    out: list[TemplateEntry] = []
    for p in sorted(root.iterdir()):
        if not p.is_dir():
            continue
        desc = brs_loader.template_descriptor_path(p.name)
        if not desc.exists():
            continue
        out.append(TemplateEntry(template_id=p.name, descriptor_path=desc))
    return out
