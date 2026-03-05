#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "bpm" / "_version.py"
PIXI_FILE = ROOT / "pixi.toml"


_VERSION_RE = re.compile(r'^__version__\s*=\s*"([^"]+)"\s*$', re.MULTILINE)
_PACKAGE_BLOCK_RE = re.compile(r"(\[package\][\s\S]*?)(\n\[|\Z)", re.MULTILINE)
_PACKAGE_VERSION_RE = re.compile(r'^(version\s*=\s*")([^"]+)("\s*)$', re.MULTILINE)


def read_source_version() -> str:
    text = VERSION_FILE.read_text(encoding="utf-8")
    m = _VERSION_RE.search(text)
    if not m:
        raise RuntimeError(f"Could not parse __version__ from {VERSION_FILE}")
    return m.group(1)


def read_pixi_version() -> str:
    text = PIXI_FILE.read_text(encoding="utf-8")
    block_match = _PACKAGE_BLOCK_RE.search(text)
    if not block_match:
        raise RuntimeError(f"Could not find [package] section in {PIXI_FILE}")

    package_block = block_match.group(1)
    m = _PACKAGE_VERSION_RE.search(package_block)
    if not m:
        raise RuntimeError(f"Could not find package version in {PIXI_FILE}")
    return m.group(2)


def write_pixi_version(new_version: str) -> None:
    text = PIXI_FILE.read_text(encoding="utf-8")
    block_match = _PACKAGE_BLOCK_RE.search(text)
    if not block_match:
        raise RuntimeError(f"Could not find [package] section in {PIXI_FILE}")

    package_block = block_match.group(1)
    updated_block, count = _PACKAGE_VERSION_RE.subn(rf'\g<1>{new_version}\g<3>', package_block, count=1)
    if count != 1:
        raise RuntimeError(f"Could not update package version in {PIXI_FILE}")

    updated_text = text[: block_match.start(1)] + updated_block + text[block_match.end(1) :]
    PIXI_FILE.write_text(updated_text, encoding="utf-8")


def cmd_show() -> int:
    src = read_source_version()
    pixi = read_pixi_version()
    status = "ok" if src == pixi else "mismatch"
    print(f"source_version={src}")
    print(f"pixi_version={pixi}")
    print(f"status={status}")
    return 0 if status == "ok" else 1


def cmd_check() -> int:
    src = read_source_version()
    pixi = read_pixi_version()
    if src != pixi:
        print(
            "Version mismatch detected: "
            f"bpm/_version.py={src} vs pixi.toml[package].version={pixi}",
            file=sys.stderr,
        )
        print("Run: python scripts/version_guard.py sync", file=sys.stderr)
        return 1
    print(f"Version check passed: {src}")
    return 0


def cmd_sync() -> int:
    src = read_source_version()
    pixi = read_pixi_version()
    if src == pixi:
        print(f"Already in sync: {src}")
        return 0
    write_pixi_version(src)
    print(f"Updated pixi.toml package version: {pixi} -> {src}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce single-source BPM version policy.")
    parser.add_argument("command", choices=["show", "check", "sync"], help="Action to perform")
    args = parser.parse_args()

    if args.command == "show":
        return cmd_show()
    if args.command == "check":
        return cmd_check()
    if args.command == "sync":
        return cmd_sync()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
