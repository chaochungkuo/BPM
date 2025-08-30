from __future__ import annotations
import os
from pathlib import Path
from typing import Tuple
from bpm.io.yamlio import safe_load_yaml, safe_dump_yaml
from bpm.models.store_index import StoreIndex, StoreRecord
from bpm.utils.time import now_iso

DEFAULT_CACHE_DIRNAME = ".bpm_cache"

def get_cache_root() -> Path:
    """Return the BPM cache root (creates it if missing)."""
    cache = os.environ.get("BPM_CACHE")
    root = Path(cache).expanduser().resolve() if cache else Path.home() / DEFAULT_CACHE_DIRNAME
    root.mkdir(parents=True, exist_ok=True)
    (root / "brs").mkdir(parents=True, exist_ok=True)
    return root

def get_stores_yaml_path() -> Path:
    return get_cache_root() / "stores.yaml"

def load_store_index() -> StoreIndex:
    p = get_stores_yaml_path()
    if not p.exists():
        idx = StoreIndex(schema_version=1, updated=now_iso(), active=None, stores={})
        safe_dump_yaml(p, {
            "schema_version": idx.schema_version,
            "updated": idx.updated,
            "active": idx.active,
            "stores": {},
        })
        return idx
    raw = safe_load_yaml(p)
    stores = {}
    for sid, rec in (raw.get("stores") or {}).items():
        stores[sid] = StoreRecord(
            id=rec["id"],
            source=rec["source"],
            cache_path=rec["cache_path"],
            version=rec.get("version", ""),
            commit=rec.get("commit"),
            last_updated=rec.get("last_updated"),
        )
    return StoreIndex(
        schema_version=raw.get("schema_version", 1),
        updated=raw.get("updated"),
        active=raw.get("active"),
        stores=stores,
    )

def save_store_index(idx: StoreIndex) -> None:
    p = get_stores_yaml_path()
    data = {
        "schema_version": idx.schema_version,
        "updated": now_iso(),
        "active": idx.active,
        "stores": {
            k: {
                "id": v.id,
                "source": v.source,
                "cache_path": v.cache_path,
                "version": v.version,
                "commit": v.commit,
                "last_updated": v.last_updated or now_iso(),
            } for k, v in (idx.stores or {}).items()
        },
    }
    safe_dump_yaml(p, data)

def get_brs_cache_dir() -> Path:
    return get_cache_root() / "brs"