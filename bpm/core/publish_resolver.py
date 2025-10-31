from __future__ import annotations
import importlib
import sys
import logging
from typing import Any, Dict

from bpm.core import brs_loader


logger = logging.getLogger("bpm.resolvers")


def _purge_module_prefix(prefix: str) -> None:
    """
    Remove any sys.modules entries that match a top-level prefix
    ('resolvers' or 'hooks') so that imports bind to the active BRS root.
    """
    to_delete = [k for k in sys.modules.keys() if k == prefix or k.startswith(prefix + ".")]
    for k in to_delete:
        sys.modules.pop(k, None)


def _import_resolver(dotted: str):
    """
    Import a resolver from the active BRS root.

    Supported forms:
      - 'resolvers.my_pub'         -> calls 'main'
      - 'resolvers.my_pub:compute' -> calls 'compute'
    """
    dotted = dotted.strip()
    brs_root = brs_loader.get_paths().root
    top_pkg = dotted.split(".", 1)[0]
    _purge_module_prefix(top_pkg)

    sys_path_added = False
    if str(brs_root) not in sys.path:
        sys.path.insert(0, str(brs_root))
        sys_path_added = True
    try:
        # Case 1: explicit module:function via colon
        if ":" in dotted:
            module, func = [s.strip() for s in dotted.split(":", 1)]
            mod = importlib.import_module(module)
            fn = getattr(mod, func, None)
            if fn is None:
                raise AttributeError(f"Function '{func}' not found in module '{module}'")
            return fn

        # Case 2: try import dotted as a module and use main
        try:
            mod = importlib.import_module(dotted)
            fn = getattr(mod, "main", None)
            if fn is not None:
                return fn
        except Exception:
            pass

        # Case 3: treat last component as function name
        if "." in dotted:
            module, func = dotted.rsplit(".", 1)
            mod = importlib.import_module(module)
            fn = getattr(mod, func, None)
            if fn is None:
                raise AttributeError(f"Function '{func}' not found in module '{module}'")
            return fn

        # Case 4: bare module name → main
        mod = importlib.import_module(dotted)
        fn = getattr(mod, "main", None)
        if fn is None:
            raise AttributeError(f"Function 'main' not found in module '{dotted}'")
        return fn
    finally:
        if sys_path_added:
            try:
                sys.path.remove(str(brs_root))
            except ValueError:
                pass


def _find_or_create_template_entry(project: Dict[str, Any], tpl_id: str) -> Dict[str, Any]:
    tlist = project.setdefault("templates", [])
    for t in tlist:
        if t.get("id") == tpl_id:
            return t
    entry = {"id": tpl_id, "status": "active", "params": {}, "published": {}}
    tlist.append(entry)
    return entry


def resolve_all(publish_cfg: Dict[str, Dict[str, Any]], ctx: Any, project: Dict[str, Any]) -> Dict[str, Any]:
    if not publish_cfg:
        return {}

    tpl_id = ctx.template.id
    entry = _find_or_create_template_entry(project, tpl_id)
    pub = entry.setdefault("published", {})

    for key, spec in publish_cfg.items():
        if not isinstance(spec, dict) or "resolver" not in spec:
            raise KeyError(f"Publish entry '{key}' missing 'resolver' key")
        dotted = spec["resolver"]
        args = spec.get("args") or {}

        fn = _import_resolver(dotted)
        logger.info("[resolver] start %s", dotted)
        value = fn(ctx, **args) if args else fn(ctx)
        logger.info("[resolver] done %s -> %s", dotted, value)
        pub[key] = value

    return pub
