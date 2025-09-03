from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
import os
from typing import Optional
from bpm.core import env
from bpm.io.yamlio import safe_load_yaml
from bpm.models.store_index import StoreRecord, StoreIndex
from bpm.utils.time import now_iso

class StoreError(Exception):
    pass

def _read_repo_yaml(path: Path) -> dict:
    p = path / "repo.yaml"
    if not p.exists():
        raise StoreError(f"repo.yaml not found in {path}")
    data = safe_load_yaml(p)
    required = ["id", "name", "description", "version", "maintainer"]
    missing = [k for k in required if k not in data]
    if missing:
        raise StoreError(f"repo.yaml missing keys: {', '.join(missing)}")
    return data

def _detect_git_commit(path: Path) -> Optional[str]:
    if not (path / ".git").exists():
        return None
    try:
        out = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
        return out or None
    except Exception:
        return None

def _copy_brs_tree(src: Path, dest: Path) -> None:
    """
    Copy a BRS directory into the cache safely:
      - Do not traverse symlinks (copy links as links) to avoid recursion
      - Ignore VCS metadata and any nested 'brs' folder at the repo root
    """
    def _ignore(dirpath: str, names: list[str]):
        ignore: set[str] = set()
        # Ignore VCS folders everywhere
        for n in (".git", ".hg", ".svn", "__pycache__"):
            if n in names:
                ignore.add(n)
        # If the source contains its own cache folder (brs/), skip it at the repo root
        try:
            if Path(dirpath).resolve() == src.resolve() and "brs" in names:
                ignore.add("brs")
        except Exception:
            pass
        return list(ignore)

    shutil.copytree(src, dest, symlinks=True, ignore=_ignore)


def add(source: str, activate: bool = False) -> StoreRecord:
    """
    Add a BRS from local path or git URL (local path only in tests).
    Returns the StoreRecord written into stores.yaml.
    """
    idx = env.load_store_index()
    brs_cache = env.get_brs_cache_dir()

    # Determine source type
    if source.startswith("http://") or source.startswith("https://") or source.endswith(".git"):
        # For now (no network in tests), require local clone step by user.
        raise StoreError("Git URL support not implemented in Day 2 (use a local path).")

    src = Path(source).resolve()
    if not src.exists():
        raise StoreError(f"Source path not found: {src}")

    # Read repo.yaml to get id/version
    meta = _read_repo_yaml(src)
    brs_id = meta["id"]
    dest = brs_cache / brs_id

    # Safety guard: prevent copying the source into a subdirectory of itself
    # This happens if BPM_CACHE points inside the source tree, leading to recursive paths.
    try:
        # Path.is_relative_to is available in Python 3.9+
        if dest.resolve().is_relative_to(src):
            raise StoreError(
                "BPM cache directory is inside the BRS source. Set BPM_CACHE to a location "
                "outside the source (e.g., ~/.bpm_cache)."
            )
    except AttributeError:
        # Fallback for older Python: string prefix check
        if str(dest.resolve()).startswith(str(src) + os.sep):
            raise StoreError(
                "BPM cache directory is inside the BRS source. Set BPM_CACHE to a location "
                "outside the source (e.g., ~/.bpm_cache)."
            )

    # Copy or refresh
    if dest.exists():
        shutil.rmtree(dest)
    _copy_brs_tree(src, dest)

    commit = _detect_git_commit(dest)
    rec = StoreRecord(
        id=brs_id,
        source=str(src),
        cache_path=str(dest),
        version=str(meta["version"]),
        commit=commit,
        last_updated=now_iso(),
    )
    idx.stores[brs_id] = rec
    if activate:
        idx.active = brs_id
    env.save_store_index(idx)
    return rec

def activate(brs_id: str) -> None:
    idx = env.load_store_index()
    if brs_id not in idx.stores:
        raise StoreError(f"Unknown store id: {brs_id}")
    idx.active = brs_id
    env.save_store_index(idx)

def remove(brs_id: str) -> None:
    idx = env.load_store_index()
    rec = idx.stores.get(brs_id)
    if not rec:
        # idempotent
        return
    # remove cache folder
    d = Path(rec.cache_path)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
    # update index
    idx.stores.pop(brs_id, None)
    if idx.active == brs_id:
        idx.active = None
    env.save_store_index(idx)

def update(brs_id: str) -> StoreRecord:
    idx = env.load_store_index()
    rec = idx.stores.get(brs_id)
    if not rec:
        raise StoreError(f"Unknown store id: {brs_id}")
    # Re-read metadata from cache
    cache_path = Path(rec.cache_path)
    meta = _read_repo_yaml(cache_path)
    commit = _detect_git_commit(cache_path)
    rec.version = str(meta["version"])
    rec.commit = commit
    rec.last_updated = now_iso()
    idx.stores[brs_id] = rec
    env.save_store_index(idx)
    return rec

def list_ids() -> list[str]:
    idx = env.load_store_index()
    return sorted(idx.stores.keys())

def get_active_id() -> Optional[str]:
    return env.load_store_index().active

def info(brs_id: str) -> StoreRecord:
    idx = env.load_store_index()
    rec = idx.stores.get(brs_id)
    if not rec:
        raise StoreError(f"Unknown store id: {brs_id}")
    return rec
