from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
from bpm.core import brs_loader
from bpm.io.yamlio import safe_load_yaml


@dataclass
class ParamSpec:
    """
    Shape of a single parameter in the template descriptor.

    Attributes:
        name: Param name (key in 'params' map).
        type: 'str'|'int'|'float'|'bool' (coercion happens later).
        cli: CLI flag for this param (e.g., "--name").
        required: Whether this param must be provided.
        default: Default value if not provided by project or CLI.
    """
    name: str
    type: str = "str"
    cli: str | None = None
    required: bool = False
    default: Any = None


@dataclass
class Descriptor:
    """
    In-memory representation of template.config.yaml.

    Attributes:
        id: Template id.
        description: Human-friendly description.
        params: Dict[str, ParamSpec] for all declared params.
        render_into: Target directory pattern (may include ${ctx.*}).
        render_files: List of (src, dst) copy/render rules.
        run_entry: Optional entry script (e.g., "run.sh").
        required_templates: Dependencies that must exist in project.
        publish: Map of publish keys -> {resolver: "...", args: {...}}.
        hooks: Map of lifecycle stages -> [dotted hook paths].
    """
    id: str
    description: str | None
    params: Dict[str, ParamSpec]
    render_into: str
    render_files: List[tuple[str, str]]
    run_entry: str | None
    required_templates: List[str] = field(default_factory=list)
    publish: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    hooks: Dict[str, List[str]] = field(default_factory=dict)


def load(template_id: str) -> Descriptor:
    """
    Load and minimally validate a template descriptor for a given template id.

    Steps:
      1) Locate templates/<template_id>/template.config.yaml in the active BRS.
      2) Parse YAML into Python dict.
      3) Validate critical keys (id match).
      4) Normalize params and render.files entries.

    Args:
        template_id: Template folder name (and descriptor 'id').

    Returns:
        A Descriptor instance ready for param resolution and rendering.

    Raises:
        ValueError: If the descriptor is missing/invalid (e.g., id mismatch).
    """
    p = brs_loader.template_descriptor_path(template_id)
    data = safe_load_yaml(p)

    # Validate id
    if data.get("id") != template_id:
        raise ValueError(f"Descriptor id mismatch: expected {template_id}, got {data.get('id')}")

    # Parse params into ParamSpec objects
    params: Dict[str, ParamSpec] = {}
    for k, v in (data.get("params") or {}).items():
        params[k] = ParamSpec(
            name=k,
            type=str(v.get("type", "str")),
            cli=v.get("cli"),
            required=bool(v.get("required", False)),
            default=v.get("default"),
        )

    # Render section
    render = data.get("render") or {}
    into = render.get("into") or "${ctx.project.name}/${ctx.template.id}/"

    files_spec = render.get("files") or []
    render_files: List[tuple[str, str]] = []
    for item in files_spec:
        # Common form: "src.j2 -> dst"
        if isinstance(item, str) and "->" in item:
            src, dst = [x.strip() for x in item.split("->", 1)]
        elif isinstance(item, dict):  # alternative explicit form
            src = item.get("src")
            dst = item.get("dst")
        else:
            raise ValueError(f"Invalid render.files entry: {item}")
        render_files.append((src, dst))

    # Optional run entry
    run_entry = None
    if "run" in data and data["run"] is not None:
        run_entry = data["run"].get("entry")

    # Dependencies can appear as 'required_templates' or legacy 'requires'
    req = data.get("required_templates") or data.get("requires") or []

    return Descriptor(
        id=template_id,
        description=data.get("description"),
        params=params,
        render_into=into,
        render_files=render_files,
        run_entry=run_entry,
        required_templates=list(req),
        publish=data.get("publish") or {},
        hooks=data.get("hooks") or {},
    )