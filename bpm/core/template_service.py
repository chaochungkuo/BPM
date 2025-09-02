from __future__ import annotations
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple, Optional

from bpm.core import brs_loader
from bpm.core.context import build as build_ctx
from bpm.core.descriptor_loader import load as load_desc, Descriptor
from bpm.core.hooks_runner import run as run_hooks
from bpm.core.jinja_renderer import render as jinja_render
from bpm.core.param_resolver import resolve as resolve_params
from bpm.core.project_io import load as load_project, save as save_project
from bpm.core.publish_resolver import resolve_all as resolve_publish

from bpm.io.exec import run_process
from bpm.io.yamlio import safe_dump_yaml


# ----------------------------- helpers -----------------------------

def _ensure_template_entry(project: Dict[str, Any], tpl_id: str) -> Dict[str, Any]:
    """
    Find an existing template entry or create a new one with status 'active'.

    Returns:
        The template entry dict (mutates project if needed).
    """
    tlist = project.setdefault("templates", [])
    for t in tlist:
        if t.get("id") == tpl_id:
            return t
    entry = {"id": tpl_id, "status": "active", "params": {}, "published": {}}
    tlist.append(entry)
    return entry


def _check_dependencies(desc: Descriptor, project: Dict[str, Any]) -> List[str]:
    """
    Return a list of missing required template ids.

    A dependency is considered satisfied if it exists in project.templates
    (status may be 'active' or 'completed').
    """
    have = {t.get("id") for t in (project.get("templates") or [])}
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


# ----------------------------- service API -----------------------------

def render(
    project_dir: Path,
    template_id: str,
    *,
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
            "template": SimpleNamespace(id=template_id),
            "params": {},
        }
    else:
        # Ad-hoc: project is None; allow ctx interpolation for template id only
        ctx_like = {
            "project": SimpleNamespace(name=""),
            "template": SimpleNamespace(id=template_id),
            "params": {},
        }
    final_params = resolve_params(desc, cli_params, project, ctx_like)

    # 4) build ctx and render
    # In ad-hoc mode, render into the provided out directory directly, ignoring desc.render_into
    if adhoc_out:
        target_cwd = Path(adhoc_out).resolve()
        target_cwd.mkdir(parents=True, exist_ok=True)
        # Override render_into to "." so files render directly under adhoc_out
        desc_eff = replace(desc, render_into=".")
        ctx = build_ctx(None, template_id, final_params, {"repo": brs_cfg.repo, "authors": brs_cfg.authors, "hosts": brs_cfg.hosts, "settings": brs_cfg.settings}, target_cwd)
        plan = jinja_render(desc_eff, ctx, dry=dry)
    else:
        ctx = build_ctx(project, template_id, final_params, {"repo": brs_cfg.repo, "authors": brs_cfg.authors, "hosts": brs_cfg.hosts, "settings": brs_cfg.settings}, project_dir)
        plan = jinja_render(desc, ctx, dry=dry)

    if dry:
        return [(p.action, p.src, p.dst) for p in plan]

    # 5) hooks: post_render (skip in ad-hoc mode)
    if not adhoc_out:
        if desc.hooks and desc.hooks.get("post_render"):
            run_hooks(desc.hooks["post_render"], ctx)

    # 6) persist project state or write ad-hoc meta
    if adhoc_out:
        # Write bpm.meta.yaml in the output folder with params + source info
        meta = {
            "source": {
                "brs_id": brs_cfg.repo.get("id"),
                "brs_version": brs_cfg.repo.get("version"),
                "template_id": template_id,
            },
            "params": final_params,
        }
        safe_dump_yaml(Path(adhoc_out) / "bpm.meta.yaml", meta)
    else:
        entry = _ensure_template_entry(project, template_id)
        entry["params"] = final_params
        entry["status"] = "active"
        # track store meta if you want (optional)
        # entry["store_id"] = brs_cfg.repo.get("id")
        project["status"] = "active"
        save_project(project_dir, project)

    return [(p.action, p.src, p.dst) for p in plan]


def run(project_dir: Path, template_id: str) -> None:
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
    desc = load_desc(template_id)
    project = load_project(project_dir)

    # Build ctx with the stored params from project.yaml (if any)
    # If this template hasn't been rendered, params may be absent → {}
    params = {}
    for t in project.get("templates") or []:
        if t.get("id") == template_id:
            params = t.get("params") or {}
            break

    ctx = build_ctx(project, template_id, params, {"repo": brs_cfg.repo, "authors": brs_cfg.authors, "hosts": brs_cfg.hosts, "settings": brs_cfg.settings}, project_dir)

    # Hooks: pre_run
    if desc.hooks and desc.hooks.get("pre_run"):
        run_hooks(desc.hooks["pre_run"], ctx)

    # Execute run.sh (or the configured entry)
    out_dir = (project_dir / f"{project['name']}/{template_id}").resolve()
    entry = desc.run_entry or "run.sh"
    run_process([f"./{entry}"], cwd=out_dir)

    # Hooks: post_run
    if desc.hooks and desc.hooks.get("post_run"):
        run_hooks(desc.hooks["post_run"], ctx)

    # Update status
    entry_dict = _ensure_template_entry(project, template_id)
    entry_dict["status"] = "completed"
    save_project(project_dir, project)


def publish(project_dir: Path, template_id: str) -> Dict[str, Any]:
    """
    Execute all publish resolvers for a template and persist to project.yaml.

    Returns:
        The resulting 'published' dict for this template.
    """
    brs_cfg = brs_loader.load_config()
    desc = load_desc(template_id)
    project = load_project(project_dir)

    # Build ctx with stored params
    params = {}
    for t in project.get("templates") or []:
        if t.get("id") == template_id:
            params = t.get("params") or {}
            break

    ctx = build_ctx(project, template_id, params, {"repo": brs_cfg.repo, "authors": brs_cfg.authors, "hosts": brs_cfg.hosts, "settings": brs_cfg.settings}, project_dir)

    pub = resolve_publish(desc.publish, ctx, project)
    save_project(project_dir, project)
    return pub
