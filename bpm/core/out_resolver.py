from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Dict

from bpm.core.publish_resolver import _import_resolver


logger = logging.getLogger("bpm.resolvers")


def _normalize(spec: Any) -> Dict[str, Any] | None:
    """
    Accepts a string or mapping and returns a normalized resolver spec.
    """
    if spec is None:
        return None
    if isinstance(spec, str):
        return {"resolver": spec, "args": {}}
    if isinstance(spec, dict):
        if "resolver" not in spec:
            raise KeyError("adhoc_out_resolver requires a 'resolver' key")
        return {"resolver": spec.get("resolver"), "args": spec.get("args") or {}}
    raise TypeError("adhoc_out_resolver must be a string or mapping")


def resolve(spec: Any, ctx: Any, base_dir: Path) -> Path | None:
    """
    Resolve the ad-hoc output directory using a resolver defined in the template.

    Returns:
        Absolute Path or None if no resolver is defined.
    Raises:
        ValueError/TypeError/KeyError on invalid spec or resolver return.
    """
    norm = _normalize(spec)
    if norm is None:
        return None

    fn = _import_resolver(norm["resolver"])
    logger.info("[resolver] start %s", norm["resolver"])
    value = fn(ctx, **norm["args"]) if norm["args"] else fn(ctx)
    logger.info("[resolver] done %s -> %s", norm["resolver"], value)

    if value is None:
        raise ValueError("adhoc_out_resolver returned None")
    path = Path(value)
    if not str(path).strip():
        raise ValueError("adhoc_out_resolver returned an empty path")
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path
