from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from bpm.core import brs_loader
from bpm.core.project_io import load as load_project, save as save_project, project_file_path
from bpm.utils.time import now_iso
from bpm.utils.table import kv_aligned


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


def init(
    cwd: Path,
    project_name: str,
    project_path: str,
    author_ids_csv: str,
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

    project_dir = cwd / project_name
    if project_file_path(project_dir).exists():
        raise ValueError(f"Project already exists: {project_dir}")

    # Expand authors
    author_ids = [s.strip() for s in (author_ids_csv or "").split(",") if s.strip()]
    authors = _expand_authors(author_ids, {"authors": brs_cfg.authors})

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
