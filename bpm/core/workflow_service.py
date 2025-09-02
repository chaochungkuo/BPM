from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple

from bpm.core import brs_loader
from bpm.core.context import build as build_ctx
from bpm.core.descriptor_loader import load as load_template_desc, Descriptor
from bpm.core.jinja_renderer import render as jinja_render
from bpm.core.param_resolver import resolve as resolve_params
from bpm.core.project_io import load as load_project
from bpm.io.exec import run_process
from bpm.io.yamlio import safe_load_yaml


def _load_workflow_descriptor(workflow_id: str) -> Descriptor:
    """
    Load workflows/<id>/workflow.yaml and map it to the template Descriptor shape
    so we can reuse renderer/param resolution.
    """
    paths = brs_loader.get_paths()
    p = paths.workflows_dir / workflow_id / "workflow.yaml"
    data = safe_load_yaml(p)

    # Coerce into Descriptor-compatible dict
    # Accept similar shape as template.config.yaml
    t_like = {
        "id": data.get("id", workflow_id),
        "description": data.get("description"),
        "params": data.get("params") or {},
        "render": (data.get("render") or {}),
        "run": (data.get("run") or {}),
        "hooks": data.get("hooks") or {},
    }
    # Reuse template descriptor loader to normalize
    return load_template_desc(t_like["id"]) if False else _to_descriptor(workflow_id, t_like)


def _to_descriptor(workflow_id: str, raw: Dict[str, Any]) -> Descriptor:
    """
    Convert a workflow raw dict into a Descriptor instance (copy of rules
    from descriptor_loader.load without re-reading from disk).
    """
    from bpm.core.descriptor_loader import ParamSpec

    # Validate id
    if raw.get("id") != workflow_id:
        raise ValueError(f"Workflow id mismatch: expected {workflow_id}, got {raw.get('id')}")

    params: Dict[str, ParamSpec] = {}
    for k, v in (raw.get("params") or {}).items():
        params[k] = ParamSpec(
            name=k,
            type=str(v.get("type", "str")),
            cli=v.get("cli"),
            required=bool(v.get("required", False)),
            default=v.get("default"),
        )

    render = raw.get("render") or {}
    into = render.get("into") or "${ctx.project.name}/${ctx.template.id}/"
    files_spec = render.get("files") or []
    render_files: List[tuple[str, str]] = []
    for item in files_spec:
        if isinstance(item, str) and "->" in item:
            src, dst = [x.strip() for x in item.split("->", 1)]
        elif isinstance(item, dict):
            src = item.get("src")
            dst = item.get("dst")
        else:
            raise ValueError(f"Invalid render.files entry: {item}")
        render_files.append((src, dst))

    run_entry = None
    if "run" in raw and raw["run"] is not None:
        run_entry = raw["run"].get("entry")

    return Descriptor(
        id=workflow_id,
        description=raw.get("description"),
        params=params,
        render_into=into,
        render_files=render_files,
        run_entry=run_entry,
        required_templates=[],
        publish={},
        hooks=raw.get("hooks") or {},
    )


def render(project_dir: Path, workflow_id: str, *, params_kv: List[str] | None = None, dry: bool = False) -> List[Tuple[str, str | None, str]]:
    """
    Render a workflow's files into the project. Does not touch project.yaml.
    """
    brs_cfg = brs_loader.load_config()
    desc = _load_workflow_descriptor(workflow_id)

    project = load_project(project_dir)

    cli_params = {}
    for pair in params_kv or []:
        if "=" not in pair:
            raise ValueError(f"Invalid --param '{pair}'. Expected KEY=VALUE.")
        k, v = pair.split("=", 1)
        cli_params[k.strip()] = v.strip()

    ctx_like = {
        "project": SimpleNamespace(name=project["name"]),
        "template": SimpleNamespace(id=workflow_id),
        "params": {},
    }
    final_params = resolve_params(desc, cli_params, project, ctx_like)

    ctx = build_ctx(project, workflow_id, final_params, {"repo": brs_cfg.repo, "authors": brs_cfg.authors, "hosts": brs_cfg.hosts, "settings": brs_cfg.settings}, project_dir)
    plan = jinja_render(desc, ctx, dry=dry)
    return [(p.action, p.src, p.dst) for p in plan]


def run(project_dir: Path, workflow_id: str) -> None:
    """
    Execute the workflow's run entry in its rendered directory.
    """
    brs_cfg = brs_loader.load_config()
    desc = _load_workflow_descriptor(workflow_id)
    project = load_project(project_dir)

    # No stored params for workflows in Day-12; use empty
    ctx = build_ctx(project, workflow_id, {}, {"repo": brs_cfg.repo, "authors": brs_cfg.authors, "hosts": brs_cfg.hosts, "settings": brs_cfg.settings}, project_dir)

    out_dir = (project_dir / f"{project['name']}/{workflow_id}").resolve()
    entry = desc.run_entry or "run.sh"
    run_process([f"./{entry}"], cwd=out_dir)

