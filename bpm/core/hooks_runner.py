from __future__ import annotations
import importlib
import sys
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Iterable, List, Tuple
import logging

from bpm.core import brs_loader


@dataclass(frozen=True)
class HookCall:
    module: str
    func: str = "main"


def _parse_hook_path(path: str) -> HookCall:
    if ":" in path:
        mod, fn = path.split(":", 1)
        return HookCall(module=mod.strip(), func=fn.strip())
    return HookCall(module=path.strip(), func="main")


def _purge_module_prefix(prefix: str) -> None:
    """
    Remove any sys.modules entries that match the top-level prefix
    (e.g., 'hooks' or 'resolvers') to avoid reusing an old package
    whose __path__ points at a previous BRS root.
    """
    to_delete = [k for k in sys.modules.keys() if k == prefix or k.startswith(prefix + ".")]
    for k in to_delete:
        sys.modules.pop(k, None)


def _import_callable(call: HookCall) -> Any:
    """
    Import the callable from the active BRS.

    Steps:
      - Purge cached 'hooks' package (and submodules) from sys.modules
      - Prepend active BRS root to sys.path
      - importlib.import_module(module) and getattr(func)
      - Remove BRS root from sys.path
    """
    brs_root = brs_loader.get_paths().root
    top_pkg = call.module.split(".", 1)[0] if "." in call.module else call.module
    _purge_module_prefix(top_pkg)

    sys_path_added = False
    if str(brs_root) not in sys.path:
        sys.path.insert(0, str(brs_root))
        sys_path_added = True
    try:
        mod = importlib.import_module(call.module)  # type: ModuleType
        fn = getattr(mod, call.func, None)
        if fn is None:
            raise AttributeError(f"Function '{call.func}' not found in module '{call.module}'")
        return fn
    finally:
        if sys_path_added:
            try:
                sys.path.remove(str(brs_root))
            except ValueError:
                pass


logger = logging.getLogger("bpm.hooks")


def run(hooks: Iterable[str], ctx: Any) -> List[Tuple[str, Any]]:
    results: List[Tuple[str, Any]] = []
    for spec in hooks or []:
        logger.info("[hook] start %s", spec)
        call = _parse_hook_path(spec)
        fn = _import_callable(call)
        rv = fn(ctx)
        logger.info("[hook] done %s", spec)
        results.append((spec, rv))
    return results
