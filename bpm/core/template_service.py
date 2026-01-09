from __future__ import annotations
import socket
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple, Optional

from bpm.core import brs_loader
from bpm.core.context import build as build_ctx
from bpm.core.descriptor_loader import load as load_desc, Descriptor
from bpm.utils.interpolate import interpolate_ctx_string
from bpm.core.hooks_runner import run as run_hooks
from bpm.core.jinja_renderer import render as jinja_render
from bpm.core.param_resolver import resolve as resolve_params
from bpm.core.project_io import load as load_project, save as save_project
from bpm.core.publish_resolver import resolve_all as resolve_publish

from bpm.io.exec import run_process
from bpm.io.yamlio import safe_dump_yaml, safe_load_yaml
from bpm.models.hostpath import HostPath


# ----------------------------- helpers -----------------------------

def _ensure_template_entry(project: Dict[str, Any], tpl_id: str, *, source_id: str | None = None) -> Dict[str, Any]:
    """
    Find an existing template entry or create a new one with status 'active'.

    Returns:
        The template entry dict (mutates project if needed).
    """
    tlist = project.setdefault("templates", [])
    for t in tlist:
        if t.get("id") == tpl_id:
            return t
    entry = {"id": tpl_id, "source_template": source_id or tpl_id, "status": "active", "params": {}, "published": {}}
    tlist.append(entry)
    return entry


def _check_dependencies(desc: Descriptor, project: Dict[str, Any]) -> List[str]:
    """
    Return a list of missing required template ids.

    A dependency is considered satisfied if it exists in project.templates
    (status may be 'active' or 'completed').
    """
    have = {t.get("source_template") or t.get("id") for t in (project.get("templates") or [])}
    missing = [dep for dep in (desc.required_templates or []) if dep not in have]
    return missing


def _parse_cli_params(param_pairs: List[str]) -> Dict[str, str]:
    """
    Parse --param KEY=VALUE pairs into a dict.

    Example: ["name=Alice", "threads=8"] -> {"name": "Alice", "threads": "8"}
    """
    out: Dict[str, str] = {}
    for pair in param_pairs or []:
        if "=" not in pair:
            raise ValueError(f"Invalid --param '{pair}'. Expected KEY=VALUE.")
        k, v = pair.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _hostname() -> str:
    return socket.gethostname().split(".")[0]


def _determine_host_key(project: Optional[Dict[str, Any]], hosts_cfg: Dict[str, Any], settings_cfg: Dict[str, Any]) -> str:
    """
    Prefer the project's recorded host if present; otherwise derive from hosts config or fall back to the current host/local.
    """
    if project:
        ppath = str(project.get("project_path") or "")
        if ":" in ppath:
            host = ppath.split(":", 1)[0]
            if host:
                return host
    hosts_map = (hosts_cfg or {}).get("hosts") if isinstance(hosts_cfg, dict) else {}
    short = _hostname()
    if short in (hosts_map or {}):
        return short
    for key, entry in (hosts_map or {}).items():
        aliases = (entry or {}).get("aliases") or []
        if short in aliases:
            return key
    default_host = (settings_cfg or {}).get("default_host")
    if default_host and default_host in (hosts_map or {}):
        return default_host
    return short or "local"


def _is_hostpath_string(val: str) -> bool:
    if ":" not in val:
        return False
    host, rest = val.split(":", 1)
    return bool(host) and rest.startswith("/")


def _hostify_params(params: Dict[str, Any], desc: Descriptor, host_key: str, base_dir: Path) -> Dict[str, Any]:
    """
    Convert path-like params (declared with 'exists') to host-aware strings for persistence.
    """
    if not desc.params:
        return dict(params)
    out = dict(params)
    for pname, pspec in desc.params.items():
        if not getattr(pspec, "exists", None):
            continue
        val = out.get(pname)
        if not isinstance(val, str) or not val.strip():
            continue
        if _is_hostpath_string(val):
            continue
        raw = Path(val).expanduser()
        if raw.is_absolute():
            resolved = raw.resolve()
        else:
            resolved = (base_dir / raw).resolve()
        out[pname] = f"{host_key}:{resolved.as_posix()}"
    return out


def _materialize_params(params: Dict[str, Any], desc: Descriptor, hosts_cfg: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
    """
    Convert persisted host-aware params back into local paths for execution time.
    """
    if not desc.params:
        return dict(params)
    out = dict(params)
    hosts_map = (hosts_cfg or {}).get("hosts") if isinstance(hosts_cfg, dict) else {}
    current_host = _hostname()
    for pname, pspec in desc.params.items():
        if not getattr(pspec, "exists", None):
            continue
        val = out.get(pname)
        if not isinstance(val, str) or not val.strip():
            continue
        if _is_hostpath_string(val):
            hp = HostPath.from_raw(val, current_host=current_host)
            out[pname] = hp.materialize(hosts_map or {}, fallback_prefix=None)
            continue
        raw = Path(val).expanduser()
        if raw.is_absolute():
            out[pname] = str(raw.resolve())
        else:
            out[pname] = str((base_dir / raw).resolve())
    return out


# ----------------------------- service API -----------------------------

def render(
    project_dir: Path,
    template_id: str,
    *,
    alias: str | None = None,
    params_kv: List[str] | None = None,
    dry: bool = False,
    adhoc_out: Optional[Path] = None,
) -> List[Tuple[str, str | None, str]]:
    """
    Render a template into the project.

    Steps:
      1) Load active BRS config and template descriptor.
      2) Load project.yaml; check dependencies; parse CLI params.
      3) Resolve parameters (defaults → project → CLI; with ${ctx.*} interpolation).
      4) Build ctx and Jinja-render the template into the project.
      5) Run 'post_render' hooks if declared.
      6) Update project.yaml: ensure template entry, write params, set project status to 'active'.

    Args:
        project_dir: Path containing project.yaml.
        template_id: Template folder/id within active BRS.
        params_kv: List of "KEY=VALUE" CLI parameters (generic).
        dry: If True, do not write files; just return the plan (list of PlanItems).

    Returns:
        The rendering plan (list of PlanItems) for inspection/testing (each is (action, src, dst)).

    Raises:
        ValueError if dependencies missing or required params not provided.
    """
    # 1) load BRS + descriptor
    brs_cfg = brs_loader.load_config()
    desc = load_desc(template_id)
    instance_id = alias.strip() if alias else template_id

    # 2) load project; deps (skip deps in ad-hoc mode)
    project = None if adhoc_out else load_project(project_dir)
    if not adhoc_out:
        missing = _check_dependencies(desc, project)
        if missing:
            raise ValueError(f"Missing required templates: {', '.join(missing)}")

    # 3) param resolution
    cli_params = _parse_cli_params(params_kv or [])
    # minimal ctx-like for interpolation during resolution
    if project:
        ctx_like = {
            "project": SimpleNamespace(name=project["name"]),
            "template": SimpleNamespace(id=instance_id),
            "params": {},
        }
    else:
        # Ad-hoc: project is None; allow ctx interpolation for template id only
        ctx_like = {
            "project": SimpleNamespace(name=""),
            "template": SimpleNamespace(id=instance_id),
            "params": {},
        }
    final_params = resolve_params(desc, cli_params, project, ctx_like)

    # 3b) optional param existence validation (paths)
    missing_paths: list[str] = []
    for pname, pspec in (desc.params or {}).items():
        kind = getattr(pspec, "exists", None)
        if not kind:
            continue
        val = final_params.get(pname)
        # Only validate string-like values
        if not isinstance(val, (str,)) or val.strip() == "":
            continue
        raw = Path(val).expanduser()
        if raw.is_absolute():
            p = raw.resolve()
        else:
            base = Path.cwd() if adhoc_out else project_dir
            p = (base / raw).resolve()
        if kind == "file" and not p.is_file():
            missing_paths.append(f"{pname} -> {p}")
        elif kind == "dir" and not p.is_dir():
            missing_paths.append(f"{pname} -> {p}")
        elif kind == "any" and not p.exists():
            missing_paths.append(f"{pname} -> {p}")
    if missing_paths:
        raise ValueError(
            "Input path(s) not found or wrong type: " + ", ".join(missing_paths)
        )

    # 4) build ctx and run pre_render hooks (if any), then render
    # In ad-hoc mode, render into the provided out directory directly, ignoring desc.render_into
    if adhoc_out:
        target_cwd = Path(adhoc_out).resolve()
        target_cwd.mkdir(parents=True, exist_ok=True)
        # Override render_into to "." so files render directly under adhoc_out
        desc_eff = replace(desc, render_into=".", parent_directory=None)
        ctx = build_ctx(None, instance_id, final_params, {"repo": brs_cfg.repo, "authors": brs_cfg.authors, "hosts": brs_cfg.hosts, "settings": brs_cfg.settings}, target_cwd, source_id=template_id)
        # Hooks: pre_render (run in both project and ad-hoc modes)
        if desc.hooks and desc.hooks.get("pre_render"):
            run_hooks(desc.hooks["pre_render"], ctx)
        plan = jinja_render(desc_eff, ctx, dry=dry)
    else:
        ctx = build_ctx(project, instance_id, final_params, {"repo": brs_cfg.repo, "authors": brs_cfg.authors, "hosts": brs_cfg.hosts, "settings": brs_cfg.settings}, project_dir, source_id=template_id)
        # Hooks: pre_render (project mode)
        if desc.hooks and desc.hooks.get("pre_render"):
            run_hooks(desc.hooks["pre_render"], ctx)
        plan = jinja_render(desc, ctx, dry=dry)

    if dry:
        return [(p.action, p.src, p.dst) for p in plan]

    # 5) hooks: post_render (now runs in both project and ad-hoc modes)
    if desc.hooks and desc.hooks.get("post_render"):
        run_hooks(desc.hooks["post_render"], ctx)

    base_for_paths = Path.cwd() if adhoc_out else project_dir
    host_key = _determine_host_key(project, brs_cfg.hosts, brs_cfg.settings)
    stored_params = _hostify_params(final_params, desc, host_key, base_for_paths)

    # 6) persist project state or write ad-hoc meta
    if adhoc_out:
        # Write bpm.meta.yaml in the output folder with params + source info
        meta = {
            "source": {
                "brs_id": brs_cfg.repo.get("id"),
                "brs_version": brs_cfg.repo.get("version"),
                "template_id": template_id,
            },
            "params": stored_params,
        }
        safe_dump_yaml(Path(adhoc_out) / "bpm.meta.yaml", meta)
    else:
        entry = _ensure_template_entry(project, instance_id, source_id=template_id)
        entry["params"] = stored_params
        entry["status"] = "active"
        entry["source_template"] = template_id
        project["status"] = "active"
        save_project(project_dir, project)

    return [(p.action, p.src, p.dst) for p in plan]


def _meta_path(out_dir: Path) -> Path:
    return out_dir / "bpm.meta.yaml"


def _load_meta(out_dir: Path) -> Dict[str, Any]:
    p = _meta_path(out_dir)
    if not p.exists():
        raise FileNotFoundError(f"bpm.meta.yaml not found in {out_dir}")
    return safe_load_yaml(p)


def _save_meta(out_dir: Path, meta: Dict[str, Any]) -> None:
    safe_dump_yaml(_meta_path(out_dir), meta)


def run(project_dir: Path, template_id: str, *, adhoc_out: Optional[Path] = None) -> None:
    """
    Execute the template's run entry (e.g., ./run.sh) with hooks.

    Steps:
      1) Load descriptor + project.
      2) Build ctx and run 'pre_run' hooks.
      3) Execute the run entry in the rendered folder.
      4) Run 'post_run' hooks.
      5) On success, set template status='completed' and save project.yaml.
    """
    brs_cfg = brs_loader.load_config()
    # For ad-hoc mode, template_id is the descriptor id
    if adhoc_out:
        desc = load_desc(template_id)
        # Ad-hoc mode: read params from bpm.meta.yaml, run hooks + entry, persist status
        out_dir = Path(adhoc_out).resolve()
        meta = _load_meta(out_dir)
        params_raw = meta.get("params") or {}
        params = _materialize_params(params_raw, desc, brs_cfg.hosts, out_dir)
        ctx = build_ctx(None, template_id, params, {"repo": brs_cfg.repo, "authors": brs_cfg.authors, "hosts": brs_cfg.hosts, "settings": brs_cfg.settings}, out_dir, source_id=template_id)

        # Hooks: pre_run (enabled in ad-hoc)
        if desc.hooks and desc.hooks.get("pre_run"):
            run_hooks(desc.hooks["pre_run"], ctx)

        entry = desc.run_entry or "run.sh"
        run_process([f"./{entry}"], cwd=out_dir)

        # Hooks: post_run (enabled in ad-hoc)
        if desc.hooks and desc.hooks.get("post_run"):
            run_hooks(desc.hooks["post_run"], ctx)

        # Persist status to meta
        meta["status"] = "completed"
        _save_meta(out_dir, meta)
    else:
        # Project mode
        project = load_project(project_dir)
        entry = next((t for t in (project.get("templates") or []) if t.get("id") == template_id), None)
        if entry is None:
            raise ValueError(f"Template '{template_id}' not found in project.yaml")
        source_id = entry.get("source_template") or template_id
        desc = load_desc(source_id)

        params = entry.get("params") or {}
        params_local = _materialize_params(params, desc, brs_cfg.hosts, project_dir)
        ctx = build_ctx(project, template_id, params_local, {"repo": brs_cfg.repo, "authors": brs_cfg.authors, "hosts": brs_cfg.hosts, "settings": brs_cfg.settings}, project_dir, source_id=source_id)

        # Hooks: pre_run
        if desc.hooks and desc.hooks.get("pre_run"):
            run_hooks(desc.hooks["pre_run"], ctx)

        # Execute run.sh (or the configured entry) in the same folder as render.into
        into = interpolate_ctx_string(desc.render_into, ctx)
        out_dir = (project_dir / into).resolve()
        # Insert optional parent_directory between the project folder and template folder
        if getattr(desc, "parent_directory", None):
            out_dir = (out_dir.parent / desc.parent_directory / out_dir.name).resolve()
        entry = desc.run_entry or "run.sh"
        run_process([f"./{entry}"], cwd=out_dir)

        # Hooks: post_run
        if desc.hooks and desc.hooks.get("post_run"):
            run_hooks(desc.hooks["post_run"], ctx)

        # Reload project.yaml to pick up any changes made by the run script (e.g., publish data)
        project = load_project(project_dir)
        entry_dict = _ensure_template_entry(project, template_id)
        entry_dict["status"] = "completed"
        save_project(project_dir, project)


def publish(project_dir: Path, template_id: str, *, adhoc_out: Optional[Path] = None) -> Dict[str, Any]:
    """
    Execute all publish resolvers for a template and persist to project.yaml.

    Returns:
        The resulting 'published' dict for this template.
    """
    brs_cfg = brs_loader.load_config()

    if adhoc_out:
        desc = load_desc(template_id)
        out_dir = Path(adhoc_out).resolve()
        meta = _load_meta(out_dir)
        params_raw = meta.get("params") or {}
        params = _materialize_params(params_raw, desc, brs_cfg.hosts, out_dir)
        ctx = build_ctx(None, template_id, params, {"repo": brs_cfg.repo, "authors": brs_cfg.authors, "hosts": brs_cfg.hosts, "settings": brs_cfg.settings}, out_dir, source_id=template_id)
        pub = resolve_publish(desc.publish, ctx, {})
        # Persist published to meta
        meta["published"] = pub
        _save_meta(out_dir, meta)
        return pub
    else:
        project = load_project(project_dir)
        entry = next((t for t in (project.get("templates") or []) if t.get("id") == template_id), None)
        if entry is None:
            raise ValueError(f"Template '{template_id}' not found in project.yaml")
        source_id = entry.get("source_template") or template_id
        desc = load_desc(source_id)
        # Build ctx with stored params
        params = entry.get("params") or {}

        params_local = _materialize_params(params, desc, brs_cfg.hosts, project_dir)
        ctx = build_ctx(project, template_id, params_local, {"repo": brs_cfg.repo, "authors": brs_cfg.authors, "hosts": brs_cfg.hosts, "settings": brs_cfg.settings}, project_dir, source_id=source_id)

        pub = resolve_publish(desc.publish, ctx, project)
        save_project(project_dir, project)
        return pub
