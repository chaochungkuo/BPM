from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Tuple

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound

from bpm.core import brs_loader
from bpm.core.descriptor_loader import Descriptor
from bpm.core.context import Ctx
from bpm.io.fs import mkdirp, copy_file, write_text, make_executable
from bpm.utils.interpolate import interpolate_ctx_string


Action = Literal["mkdir", "render", "copy", "chmod"]


@dataclass(frozen=True)
class PlanItem:
    """
    One step in the rendering plan.

    Attributes:
        action: "mkdir" | "render" | "copy" | "chmod"
        src:    Source path (for render/copy), else None
        dst:    Destination path (for all but chmod may also use it)
    """
    action: Action
    src: str | None
    dst: str


def _jinja_env(template_root: Path) -> Environment:
    """
    Build a Jinja2 environment rooted at the template folder.

    We use StrictUndefined so missing variables fail fast during tests.
    """
    loader = FileSystemLoader(str(template_root))
    env = Environment(
        loader=loader,
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env


def _expand_render_into(desc: Descriptor, ctx: Ctx) -> Path:
    """
    Expand the 'render.into' string using ${ctx.*} placeholders and
    return an absolute path under ctx.cwd.
    """
    into = interpolate_ctx_string(desc.render_into, ctx)
    # Keep simple, relative to cwd
    target = (ctx.cwd / into).resolve()
    return target


def _build_plan(desc: Descriptor, ctx: Ctx) -> Tuple[List[PlanItem], Path, Path]:
    """
    Compute the list of steps (PlanItem) needed to render/copy all files.

    Returns:
        (plan, template_root, target_dir)
    """
    paths = brs_loader.get_paths()
    tpl_root = paths.templates_dir / desc.id
    if not tpl_root.exists():
        # Support workflows by falling back to workflows/<id>
        wf_root = paths.workflows_dir / desc.id
        if wf_root.exists():
            tpl_root = wf_root
    target_dir = _expand_render_into(desc, ctx)
    plan: List[PlanItem] = [PlanItem("mkdir", None, str(target_dir))]

    for src, dst in desc.render_files:
        src_path = tpl_root / src
        dst_path = target_dir / dst

        if src.endswith(".j2"):
            plan.append(PlanItem("render", str(src_path), str(dst_path)))
        else:
            plan.append(PlanItem("copy", str(src_path), str(dst_path)))

    # If run_entry is defined, ensure it will be executable
    if desc.run_entry:
        run_dst = target_dir / desc.run_entry
        plan.append(PlanItem("chmod", None, str(run_dst)))

    return plan, tpl_root, target_dir


def render(desc: Descriptor, ctx: Ctx, *, dry: bool = False) -> List[PlanItem]:
    """
    Render a template to disk (or return a plan in dry mode).

    Steps:
      1) Expand render.into → absolute path under ctx.cwd
      2) For each file mapping:
         - "*.j2" → Jinja render with 'ctx' available
         - other  → copy as-is
      3) 'run_entry' (if present) → chmod +x

    Args:
        desc: Loaded descriptor for the template.
        ctx: Runtime context (project/template/params/brs/cwd).
        dry: If True, do not write files; just return the plan.

    Returns:
        List[PlanItem] in the order they would be executed.

    Raises:
        FileNotFoundError: If a source file is missing.
        jinja2.exceptions.UndefinedError: If Jinja uses an undefined variable.
    """
    plan, tpl_root, target_dir = _build_plan(desc, ctx)
    if dry:
        return plan

    # Prepare Jinja environment
    env = _jinja_env(tpl_root)

    # Execute plan
    for step in plan:
        if step.action == "mkdir":
            mkdirp(step.dst)

        elif step.action == "render":
            src_rel = Path(step.src).relative_to(tpl_root)
            try:
                template = env.get_template(str(src_rel))
            except TemplateNotFound as e:
                raise FileNotFoundError(f"Template not found: {src_rel}") from e
            # Render with ctx exposed
            content = template.render(ctx=ctx)
            write_text(step.dst, content)

        elif step.action == "copy":
            copy_file(step.src, step.dst)

        elif step.action == "chmod":
            make_executable(step.dst)

    return plan
