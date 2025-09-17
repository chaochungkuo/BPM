from __future__ import annotations
import re
from pathlib import Path
import socket
from typing import Any, Dict, Iterable, List, Optional

from bpm.core import brs_loader
from bpm.core.project_io import load as load_project, save as save_project, project_file_path
from bpm.utils.time import now_iso
from bpm.utils.table import kv_aligned
from bpm.io.yamlio import safe_load_yaml


def _policy_regex_and_message(settings: Dict[str, Any]) -> tuple[Optional[re.Pattern[str]], Optional[str]]:
    """
    Extract (compiled_regex, message) from BRS settings policy.
    Returns (None, None) if not configured.
    """
    policy = (settings or {}).get("policy", {})
    pn = policy.get("project_name", {}) if isinstance(policy, dict) else {}
    regex = pn.get("regex")
    message = pn.get("message")
    return (re.compile(regex) if regex else None, message)


def _load_authors_map(brs_config: Dict[str, Any]) -> dict:
    """
    Build an id->author map from config/authors.yaml.

    Expected structure:
      authors:
        - id: ckuo
          name: "Chao-Chung Kuo"
          email: "..."
    """
    authors_cfg = (brs_config.get("authors") or {}).get("authors") or []
    return {a.get("id"): a for a in authors_cfg if isinstance(a, dict) and a.get("id")}


def _expand_authors(author_ids: Iterable[str], brs_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert a list of author ids into full author dicts using BRS authors.yaml.

    Unknown ids are kept as {id: "<id>"} with no name/email, so information isn't lost.
    """
    ids = [a.strip() for a in author_ids if a and str(a).strip()]
    amap = _load_authors_map(brs_config)
    expanded: List[Dict[str, Any]] = []
    for aid in ids:
        expanded.append(amap.get(aid, {"id": aid}))
    return expanded


def _resolve_host_key(hosts_cfg: dict, settings_cfg: dict) -> str:
    """
    Determine the host key to use for host-aware paths.

    Order:
      1) Match system short hostname against hosts.<key> or hosts.<key>.aliases
      2) settings.default_host if present in hosts
      3) 'local'
    """
    short = socket.gethostname().split(".")[0]
    hosts_map = (hosts_cfg or {}).get("hosts") or {}
    # direct match on key
    if short in hosts_map:
        return short
    # match in aliases
    for key, entry in hosts_map.items():
        aliases = (entry or {}).get("aliases") or []
        if isinstance(aliases, list) and short in aliases:
            return key
    # settings.default_host
    default_host = (settings_cfg or {}).get("default_host")
    if default_host and default_host in hosts_map:
        return default_host
    return "local"


def init(
    outdir: Path,
    project_name: str,
    author_ids_csv: str,
    host_key: str | None = None,
) -> Path:
    """
    Initialize a new project folder and write project.yaml.

    Steps:
      - Validate project_name against BRS policy (if provided).
      - Create <cwd>/<project_name> directory.
      - Expand authors from BRS config.
      - Write project.yaml with schema_version=1, status=initiated.

    Args:
      cwd: Working directory to create the project folder in.
      project_name: Name of the new project (policy may enforce a regex).
      project_path: Host-aware path string to persist, e.g. "nextgen:/projects/250901_Demo_UKA".
      author_ids_csv: Comma-separated list of author ids to include.

    Returns:
      The project directory path that was created.

    Raises:
      ValueError: if name policy fails or a project with same name already exists.
    """
    # Load BRS settings for name policy
    brs_cfg = brs_loader.load_config()
    regex, message = _policy_regex_and_message(brs_cfg.settings)
    if regex and not regex.match(project_name):
        hint = message or "Project name violates policy regex."
        raise ValueError(f"Invalid project name '{project_name}'. {hint}")

    project_dir = outdir / project_name
    if project_file_path(project_dir).exists():
        raise ValueError(f"Project already exists: {project_dir}")

    # Expand authors
    author_ids = [s.strip() for s in (author_ids_csv or "").split(",") if s.strip()]
    authors = _expand_authors(author_ids, {"authors": brs_cfg.authors})

    # Determine host-aware project_path from local absolute path
    abs_posix = project_dir.resolve().as_posix()
    hk = host_key or _resolve_host_key({"hosts": brs_cfg.hosts.get("hosts") if isinstance(brs_cfg.hosts, dict) else {}}, brs_cfg.settings)
    project_path = f"{hk}:{abs_posix}"

    # Minimal project dictionary
    project = {
        "schema_version": 1,
        "name": project_name,
        "created": now_iso(),
        "project_path": project_path,  # stored as host-aware string
        "authors": authors,
        "status": "initiated",
        "templates": [],
    }

    save_project(project_dir, project)
    return project_dir


def info(project_dir: Path) -> Dict[str, Any]:
    """
    Load project.yaml and return the dictionary unchanged.
    """
    return load_project(project_dir)


def status_table(project_dir: Path) -> str:
    """
    Produce a simple status representation as plain text.

    Fields:
      - Project name, status
      - Count of templates
      - Each template id + status line

    Returns:
      A multi-line string. Future Day-11 can replace with a nice table helper.
    """
    p = load_project(project_dir)
    lines: List[str] = []
    # Keep alignment consistent with tests: width equals len('Project') == 7
    lines.extend(kv_aligned([
        ("Project", str(p.get('name'))),
        ("Status", str(p.get('status'))),
    ], width=7))
    # Keep exact literal form for Templates line to avoid snapshot drift
    lines.append(f"Templates: {len(p.get('templates') or [])}")
    for t in p.get("templates") or []:
        lines.append(f"- {t.get('id')}  [{t.get('status')}]")
    return "\n".join(lines)


# ----------------------------- adoption -----------------------------

def _load_meta(adhoc_dir: Path) -> Dict[str, Any]:
    p = adhoc_dir / "bpm.meta.yaml"
    if not p.exists():
        raise FileNotFoundError(f"bpm.meta.yaml not found in {adhoc_dir}")
    return safe_load_yaml(p)


def _entry_from_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    src = meta.get("source") or {}
    tid = str(src.get("template_id") or "").strip()
    if not tid:
        raise ValueError("Invalid bpm.meta.yaml: missing source.template_id")
    params = meta.get("params") or {}
    published = meta.get("published") or {}
    status = meta.get("status") or ("completed" if published else "active")
    return {
        "id": tid,
        "params": params,
        "published": published,
        "status": status,
        "source": src,
    }


def _merge_entries(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(existing)
    # Params: incoming wins
    out["params"] = {**(existing.get("params") or {}), **(incoming.get("params") or {})}
    # Published: incoming wins
    out["published"] = {**(existing.get("published") or {}), **(incoming.get("published") or {})}
    # Status: take incoming
    out["status"] = incoming.get("status") or existing.get("status")
    # Source: keep both (existing under source_prev)
    if existing.get("source") and incoming.get("source") != existing.get("source"):
        out["source_prev"] = existing.get("source")
    out["source"] = incoming.get("source") or existing.get("source")
    return out


def adopt(
    project_dir: Path,
    adhoc_dirs: list[Path],
    *,
    on_exists: str = "merge",  # one of: skip|merge|overwrite
) -> Path:
    """
    Insert one or more ad-hoc bpm.meta.yaml records into an existing project.yaml.

    Args:
      project_dir: Project directory containing project.yaml
      adhoc_dirs: List of ad-hoc directories to adopt (each must contain bpm.meta.yaml)
      on_exists: Collision policy for template ids: skip|merge|overwrite

    Returns: project_dir (for convenience)
    """
    if on_exists not in ("skip", "merge", "overwrite"):
        raise ValueError("on_exists must be one of: skip|merge|overwrite")

    project = load_project(project_dir)
    tlist: list[Dict[str, Any]] = project.setdefault("templates", [])

    for d in adhoc_dirs or []:
        meta = _load_meta(Path(d).resolve())
        entry_in = _entry_from_meta(meta)
        tid = entry_in.get("id")
        # Find existing entry
        idx = next((i for i, t in enumerate(tlist) if t.get("id") == tid), None)
        if idx is None:
            tlist.append(entry_in)
        else:
            if on_exists == "skip":
                continue
            if on_exists == "overwrite":
                tlist[idx] = entry_in
            elif on_exists == "merge":
                tlist[idx] = _merge_entries(tlist[idx], entry_in)

    save_project(project_dir, project)
    return project_dir
