from __future__ import annotations
from typing import Any, Dict
from bpm.utils.interpolate import interpolate_ctx_string


def _coerce(val: Any, typ: str) -> Any:
    """
    Coerce a raw value to the declared ParamSpec type.

    Args:
        val: Original value (str/bool/int/etc.).
        typ: One of 'str'|'int'|'float'|'bool'.

    Returns:
        Value converted to the target type (or unchanged for 'str').
    """
    if val is None:
        return None
    if typ == "int":
        return int(val)
    if typ == "float":
        return float(val)
    if typ == "bool":
        if isinstance(val, bool):
            return val
        return str(val).lower() in ("1", "true", "yes", "y", "on")
    return val  # 'str' or unknown -> leave as-is


def _project_authors_as_string(project: dict | None) -> str | None:
    """
    Convert project-level authors into a display string.

    Supports project.yaml authors as:
      - list[dict]: prefers "name", falls back to "id"
      - list[str]
      - comma-separated string
    """
    if not project:
        return None
    raw = project.get("authors")
    if isinstance(raw, str):
        val = raw.strip()
        return val or None
    if not isinstance(raw, list):
        return None
    parts: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            aid = str(item.get("id") or "").strip()
            if name:
                parts.append(name)
            elif aid:
                parts.append(aid)
        elif isinstance(item, str) and item.strip():
            parts.append(item.strip())
    if not parts:
        return None
    return ", ".join(parts)


def resolve(desc, cli_params: Dict[str, Any], project: dict | None, ctx_like: dict) -> Dict[str, Any]:
    """
    Compute final parameter values for a template, with precedence and interpolation.

    Precedence (highest last → wins):
      1) Descriptor defaults
      2) Project-stored params (if the template already exists in project.yaml)
      3) CLI-provided params

    After merging, any string containing ${ctx.*} is interpolated using ctx_like.

    Args:
        desc: A Descriptor (or duck-typed with .id and .params).
        cli_params: Dict of CLI args parsed already (keys match param names).
        project: Loaded project dict or None (ad-hoc mode).
        ctx_like: A simple object/dict tree with keys: project, template, params.
                  Used only for `${ctx.…}` placeholder interpolation.

    Returns:
        Dict of final parameter values.

    Raises:
        ValueError: If required parameters are missing after precedence resolution.
    """
    base: Dict[str, Any] = {}

    # 1) defaults
    for k, spec in desc.params.items():
        if spec.default is not None:
            base[k] = spec.default

    # 2) project-stored values
    if project:
        for t in project.get("templates", []):
            if t.get("id") == desc.id or t.get("source_template") == desc.id:
                for k, v in (t.get("params") or {}).items():
                    base[k] = v

    # 3) CLI overrides
    for k, v in (cli_params or {}).items():
        if k in desc.params:
            base[k] = v

    # 4) type coercion
    for k, spec in desc.params.items():
        if k in base:
            base[k] = _coerce(base[k], spec.type)

    # 4b) project-level authors fallback for common placeholder values.
    # This avoids persisting "unknown" when project.yaml already has authors.
    if "authors" in desc.params and "authors" not in (cli_params or {}):
        av = base.get("authors")
        if av is None or (isinstance(av, str) and av.strip().lower() in ("", "unknown", "na", "n/a")):
            p_auth = _project_authors_as_string(project)
            if p_auth:
                base["authors"] = p_auth

    # 5) interpolate ${ctx.*} strings
    # The ctx_like can be a minimal object/dict graph, just needs attributes/keys.
    for k, v in list(base.items()):
        if isinstance(v, str) and "${ctx." in v:
            base[k] = interpolate_ctx_string(v, ctx_like)

    # 6) required check
    missing = [k for k, s in desc.params.items() if s.required and k not in base]
    if missing:
        raise ValueError(f"Missing required parameters: {', '.join(missing)}")

    return base
