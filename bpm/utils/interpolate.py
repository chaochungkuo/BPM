from __future__ import annotations
import re
from typing import Any, Mapping

# Matches ${ctx.something.like.this}
_CTX_PATTERN = re.compile(r"\$\{ctx\.([^\}]+)\}")


def _get_attr_path(ctx: Any, path: str) -> Any:
    """
    Resolve a dotted path from a Python object or dict.

    Example:
      - ctx.project.name
      - ctx['project']['name']

    Args:
        ctx: The context object (can mix objects and dicts).
        path: Dotted path string after 'ctx.' (e.g. 'project.name').

    Returns:
        The resolved value at that dotted path.

    Raises:
        AttributeError / KeyError if the path is invalid.
    """
    cur = ctx
    for part in path.split("."):
        if isinstance(cur, Mapping):
            cur = cur[part]
        else:
            cur = getattr(cur, part)
    return cur


def interpolate_ctx_string(s: str, ctx: Any) -> str:
    """
    Replace all ${ctx.<path>} occurrences in a string using values from ctx.

    Example:
        s = "Out: ${ctx.project.name}/${ctx.template.id}"
        -> "Out: 250901_Demo_UKA/hello"

    Args:
        s: Input string potentially containing ${ctx.*} placeholders.
        ctx: Context object used to resolve paths.

    Returns:
        A new string with placeholders replaced (unmatched -> empty string).
    """
    def repl(m: re.Match[str]) -> str:
        path = m.group(1)
        val = _get_attr_path(ctx, path)
        return "" if val is None else str(val)

    return _CTX_PATTERN.sub(repl, s)