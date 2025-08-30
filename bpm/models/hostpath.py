from __future__ import annotations
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Dict, Optional


@dataclass(frozen=True)
class HostPath:
    """
    Canonical host-aware path form used by BPM.

    Stored form: "host:/abs/posix/path"
    - 'host' is a key from config/hosts.yaml
    - path is absolute POSIX

    Construction rules:
    - If given a local absolute path "/abs", we normalize to "<current_host>:/abs"
      (current_host must be provided by caller).
    - If given "host:/abs" we keep host and normalize slashes.
    """
    host: str
    abs_posix: str  # always starts with "/"

    def __str__(self) -> str:
        return f"{self.host}:{self.abs_posix}"

    @staticmethod
    def from_raw(raw: str, current_host: str) -> "HostPath":
        """
        Accepts:
          - 'host:/abs'
          - '/abs'
        Returns canonical HostPath.
        """
        if ":" in raw:
            host, rest = raw.split(":", 1)
            path = rest if rest.startswith("/") else f"/{rest}"
            return HostPath(host=host, abs_posix=str(PurePosixPath(path)))
        else:
            path = raw if raw.startswith("/") else f"/{raw}"
            return HostPath(host=current_host, abs_posix=str(PurePosixPath(path)))

    def materialize(self, hosts_cfg: Dict[str, Dict[str, str]], fallback_prefix: Optional[str] = None) -> str:
        """
        Convert to a local filesystem path using hosts.yaml mapping:
          hosts.<host>.mount_prefix + abs_posix (without double slashes)

        If host not in cfg and fallback_prefix is provided, uses it.
        Otherwise, returns abs_posix (bare) as a last resort.
        """
        entry = hosts_cfg.get(self.host)
        prefix = entry.get("mount_prefix") if entry else None
        if not prefix:
            prefix = fallback_prefix
        if not prefix:
            # last resort: return the absolute POSIX path (useful for tests)
            return self.abs_posix
        # Join cleanly
        p = PurePosixPath(prefix) / self.abs_posix.lstrip("/")
        return str(p)