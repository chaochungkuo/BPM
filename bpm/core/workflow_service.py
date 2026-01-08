from __future__ import annotations
from dataclasses import dataclass
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
from typing import Any, Dict, List, Optional

from bpm.core import brs_loader
from bpm.core.context import build as build_ctx
from bpm.core.descriptor_loader import ParamSpec
from bpm.core.hooks_runner import run as run_hooks
from bpm.core.param_resolver import resolve as resolve_params
from bpm.core.project_io import load as load_project, save as save_project, project_file_path
from bpm.io.exec import run_process
from bpm.io.yamlio import safe_load_yaml
from bpm.utils.interpolate import interpolate_ctx_string
from bpm.utils.time import now_iso


@dataclass(frozen=True)
class WorkflowDescriptor:
    id: str
    description: str | None
    params: Dict[str, ParamSpec]
    run_entry: str | None
    run_args: List[str]
    run_env: Dict[str, str]
    hooks: Dict[str, List[str]]
    tools_required: List[str]
    tools_optional: List[str]


def load_descriptor(workflow_id: str) -> WorkflowDescriptor:
    """
    Load workflows/<id>/workflow_config.yaml (preferred) or workflow.yaml.
    """
    paths = brs_loader.get_paths()
    wf_dir = paths.workflows_dir / workflow_id
    p = wf_dir / "workflow_config.yaml"
    if not p.exists():
        raise FileNotFoundError(
            f"Workflow '{workflow_id}' not found in active BRS. "
            f"Expected descriptor at {p}."
        )
    data = safe_load_yaml(p)

    if data.get("id") != workflow_id:
        raise ValueError(f"Workflow id mismatch: expected {workflow_id}, got {data.get('id')}")

    params: Dict[str, ParamSpec] = {}
    for k, v in (data.get("params") or {}).items():
        params[k] = ParamSpec(
            name=k,
            type=str(v.get("type", "str")),
            cli=v.get("cli"),
            required=bool(v.get("required", False)),
            default=v.get("default"),
            description=v.get("description"),
        )

    run = data.get("run") or {}
    run_entry = run.get("entry")
    run_args = run.get("args") or []
    if not isinstance(run_args, list):
        raise ValueError("run.args must be a list")
    run_env = run.get("env") or {}
    if not isinstance(run_env, dict):
        raise ValueError("run.env must be a mapping")

    hooks = data.get("hooks") or {}
    if not isinstance(hooks, dict):
        raise ValueError("hooks must be a mapping")

    tools_required: List[str] = []
    tools_optional: List[str] = []
    tools_sec = data.get("tools")
    if isinstance(tools_sec, list):
        tools_required = [str(x) for x in tools_sec]
    elif isinstance(tools_sec, dict):
        req = tools_sec.get("required") or []
        opt = tools_sec.get("optional") or []
        if isinstance(req, list):
            tools_required = [str(x) for x in req]
        if isinstance(opt, list):
            tools_optional = [str(x) for x in opt]

    return WorkflowDescriptor(
        id=workflow_id,
        description=data.get("description"),
        params=params,
        run_entry=run_entry,
        run_args=[str(x) for x in run_args],
        run_env={str(k): str(v) for k, v in run_env.items()},
        hooks=hooks,
        tools_required=tools_required,
        tools_optional=tools_optional,
    )


def _load_project_from_path(project_path: Optional[Path]) -> tuple[Optional[Dict[str, Any]], Optional[Path]]:
    if project_path is None:
        return None, None
    p = project_path.resolve()
    project_dir = p if p.is_dir() else p.parent
    project_file = p if p.is_file() else project_file_path(project_dir)
    if not project_file.exists():
        raise FileNotFoundError(f"project.yaml not found at {project_file}")
    return load_project(project_dir), project_dir


def _ctx_to_dict(ctx: Any) -> Dict[str, Any]:
    project = None
    if ctx.project:
        project = {
            "name": ctx.project.name,
            "project_path": ctx.project.project_path,
        }
    return {
        "project": project,
        "template": {"id": ctx.template.id, "published": ctx.template.published},
        "params": ctx.params,
        "brs": ctx.brs,
        "cwd": str(ctx.cwd),
        "project_dir": ctx.project_dir,
    }


def _write_ctx_json(ctx: Any) -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False, prefix="bpm-ctx-", suffix=".json")
    try:
        payload = _ctx_to_dict(ctx)
        tmp.write(json.dumps(payload, indent=2).encode("utf-8"))
        tmp.flush()
    finally:
        tmp.close()
    return Path(tmp.name)


def run(workflow_id: str, *, project_path: Optional[Path] = None, params_kv: List[str] | None = None) -> None:
    """
    Execute the workflow's entry script from its workflow folder.
    """
    brs_cfg = brs_loader.load_config()
    desc = load_descriptor(workflow_id)
    project, project_dir = _load_project_from_path(project_path)

    cli_params = {}
    for pair in params_kv or []:
        if "=" not in pair:
            raise ValueError(f"Invalid --param '{pair}'. Expected KEY=VALUE.")
        k, v = pair.split("=", 1)
        cli_params[k.strip()] = v.strip()

    ctx_like = {
        "project": SimpleNamespace(name=project["name"], project_path=project["project_path"]) if project else None,
        "template": SimpleNamespace(id=workflow_id),
        "params": {},
    }
    final_params = resolve_params(desc, cli_params, project, ctx_like)

    wf_dir = brs_loader.get_paths().workflows_dir / workflow_id
    ctx = build_ctx(project, workflow_id, final_params, {"repo": brs_cfg.repo, "authors": brs_cfg.authors, "hosts": brs_cfg.hosts, "settings": brs_cfg.settings}, wf_dir)

    entry = desc.run_entry or "run.sh"
    entry_path = (wf_dir / entry).resolve()
    if not entry_path.exists():
        raise FileNotFoundError(f"Workflow entry not found: {entry_path}")
    entry_path.chmod(entry_path.stat().st_mode | 0o111)

    def _normalize_bool_str(val: str) -> str:
        if val == "True":
            return "true"
        if val == "False":
            return "false"
        return val

    args = [
        _normalize_bool_str(interpolate_ctx_string(a, ctx)) if "${ctx." in a else a
        for a in desc.run_args
    ]
    env = os.environ.copy()
    for k, v in desc.run_env.items():
        env[k] = (
            _normalize_bool_str(interpolate_ctx_string(v, ctx)) if "${ctx." in v else v
        )

    ctx_path = _write_ctx_json(ctx)
    env["BPM_CTX_PATH"] = str(ctx_path)
    env["BPM_WORKFLOW_ID"] = workflow_id
    env["BPM_PROJECT_DIR"] = ctx.project_dir
    if project:
        env["BPM_PROJECT_PATH"] = project["project_path"]

    run_record = None
    if project and project_dir:
        run_record = {
            "id": workflow_id,
            "run_entry": entry,
            "args": args,
            "params": final_params,
            "started_at": now_iso(),
            "status": "running",
        }

    try:
        if desc.hooks and desc.hooks.get("pre_run"):
            run_hooks(desc.hooks["pre_run"], ctx)
        run_process([str(entry_path)] + args, cwd=wf_dir, env=env)
        if desc.hooks and desc.hooks.get("post_run"):
            run_hooks(desc.hooks["post_run"], ctx)
        status = "completed"
        error_msg = None
    except Exception as e:
        status = "failed"
        error_msg = str(e)
        raise
    finally:
        try:
            ctx_path.unlink(missing_ok=True)
        except Exception:
            pass
        if run_record is not None and project and project_dir:
            run_record["status"] = status
            run_record["finished_at"] = now_iso()
            if error_msg:
                run_record["error"] = error_msg
            project.setdefault("workflows", []).append(run_record)
            save_project(project_dir, project)
