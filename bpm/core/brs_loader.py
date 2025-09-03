from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from bpm.core import env
from bpm.io.yamlio import safe_load_yaml


@dataclass(frozen=True)
class BrsPaths:
    root: Path
    config_dir: Path
    templates_dir: Path
    workflows_dir: Path
    hooks_dir: Path
    resolvers_dir: Path


@dataclass(frozen=True)
class BrsConfig:
    repo: Dict[str, Any]
    authors: Dict[str, Any]
    hosts: Dict[str, Any]
    settings: Dict[str, Any]


def get_active_brs_path() -> Path:
    """Return the active BRS cache path (raises if none active)."""
    idx = env.load_store_index()
    if not idx.active:
        raise RuntimeError("No active BRS. Use `bpm resource activate <id>` first.")
    rec = idx.stores.get(idx.active)
    if not rec:
        raise RuntimeError(f"Active BRS '{idx.active}' not found in stores.yaml.")
    p = Path(rec.cache_path)
    if not p.exists():
        raise RuntimeError(f"Active BRS path does not exist: {p}")
    return p


def get_paths(root: Optional[Path] = None) -> BrsPaths:
    """Return standard folders in the BRS (flat layout)."""
    root = root or get_active_brs_path()
    return BrsPaths(
        root=root,
        config_dir=root / "config",
        templates_dir=root / "templates",
        workflows_dir=root / "workflows",
        hooks_dir=root / "hooks",
        resolvers_dir=root / "resolvers",
    )


def load_repo_meta(root: Optional[Path] = None) -> Dict[str, Any]:
    """Load repo.yaml from the BRS root."""
    root = root or get_active_brs_path()
    meta = safe_load_yaml(root / "repo.yaml")
    # minimal validation here; store_registry already validates on add
    if "id" not in meta or "version" not in meta:
        raise RuntimeError(f"Invalid repo.yaml in {root}")
    return meta


def _load_if_exists(path: Path) -> Dict[str, Any]:
    return safe_load_yaml(path) if path.exists() else {}


def load_config(root: Optional[Path] = None) -> BrsConfig:
    """Load config/authors.yaml, hosts.yaml, settings.yaml (missing files -> {})."""
    paths = get_paths(root)
    repo = load_repo_meta(paths.root)
    authors = _load_if_exists(paths.config_dir / "authors.yaml")
    hosts = _load_if_exists(paths.config_dir / "hosts.yaml")
    settings = _load_if_exists(paths.config_dir / "settings.yaml")
    return BrsConfig(repo=repo, authors=authors, hosts=hosts, settings=settings)


def template_descriptor_path(template_id: str, root: Optional[Path] = None) -> Path:
    """
    Path to the template descriptor file.

    Supports both names for compatibility:
      - templates/<id>/template_config.yaml (preferred)
      - templates/<id>/template.config.yaml (legacy)
    """
    base = get_paths(root).templates_dir / template_id
    preferred = base / "template_config.yaml"
    legacy = base / "template.config.yaml"
    return preferred if preferred.exists() else legacy


def template_exists(template_id: str, root: Optional[Path] = None) -> bool:
    """Whether a template folder + descriptor exist."""
    p = template_descriptor_path(template_id, root)
    return p.exists()
