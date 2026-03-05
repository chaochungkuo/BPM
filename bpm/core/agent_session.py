from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def get_session_root() -> Path:
    override = os.environ.get("BPM_AGENT_SESSION_DIR")
    if override:
        root = Path(override).expanduser().resolve()
    else:
        root = (Path.cwd() / ".bpm" / "agent" / "sessions").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def new_session_file(prefix: str = "session") -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    return get_session_root() / f"{prefix}-{ts}.jsonl"


def append_event(session_file: Path, event: dict[str, Any]) -> None:
    payload = dict(event)
    payload.setdefault("ts", datetime.now(timezone.utc).isoformat())
    with session_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=True) + "\n")


def list_session_files(prefix: str | None = None, limit: int = 20) -> list[Path]:
    root = get_session_root()
    pattern = f"{prefix}-*.jsonl" if prefix else "*.jsonl"
    files = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[: max(0, int(limit))]


def read_events(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            obj = json.loads(s)
        except Exception:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def summarize_session(path: Path) -> dict[str, Any]:
    events = read_events(path)
    if not events:
        return {
            "file": str(path),
            "kind": path.name.split("-", 1)[0] if "-" in path.name else "unknown",
            "event_count": 0,
            "last_event": None,
            "last_ts": None,
            "ok": None,
            "decision": None,
        }

    last = events[-1]
    ok_val = None
    for ev in reversed(events):
        if "ok" in ev:
            ok_val = ev.get("ok")
            break

    decision = None
    for ev in reversed(events):
        if ev.get("event") in ("start_decision", "start_end"):
            decision = ev.get("decision")
            if decision is not None:
                break

    return {
        "file": str(path),
        "kind": path.name.split("-", 1)[0] if "-" in path.name else "unknown",
        "event_count": len(events),
        "last_event": last.get("event"),
        "last_ts": last.get("ts"),
        "ok": ok_val,
        "decision": decision,
    }
