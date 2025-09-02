from __future__ import annotations
from typing import Iterable, List, Sequence


def kv_aligned(pairs: Sequence[tuple[str, str]], width: int) -> List[str]:
    """
    Render key/value lines where keys are padded to 'width'.

    Example with width=7:
      ("Project", "Demo")  -> "Project: Demo"
      ("Status",  "init") -> "Status : init"
    """
    out: List[str] = []
    for k, v in pairs:
        out.append(f"{k:<{width}}: {v}")
    return out


def simple_table(headers: Sequence[str], rows: Iterable[Sequence[str]]) -> str:
    """
    Render a very small plain-text table with padded columns.
    Not used for tests yet; available for future UX polish.
    """
    widths = [len(h) for h in headers]
    # compute max width per column
    cache_rows: List[Sequence[str]] = []
    for r in rows:
        cache_rows.append(r)
        for i, cell in enumerate(r):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
            else:
                widths.append(len(str(cell)))
    def fmt_row(r: Sequence[str]) -> str:
        return "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r))

    lines: List[str] = [fmt_row(headers)]
    lines.append("  ".join("-" * w for w in widths))
    for r in cache_rows:
        lines.append(fmt_row(r))
    return "\n".join(lines)

