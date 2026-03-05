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
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return get_session_root() / f"{prefix}-{ts}.jsonl"


def append_event(session_file: Path, event: dict[str, Any]) -> None:
    payload = dict(event)
    payload.setdefault("ts", datetime.now(timezone.utc).isoformat())
    with session_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=True) + "\n")
