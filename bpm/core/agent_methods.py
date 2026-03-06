from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

from bpm.core import brs_loader
from bpm.core.project_io import load as load_project
from bpm.io.yamlio import safe_load_yaml


@dataclass(frozen=True)
class MethodsOutput:
    markdown: str
    citation_count: int
    templates_count: int


def generate_methods_markdown(project_dir: Path, style: str = "full") -> MethodsOutput:
    pdir = Path(project_dir).resolve()
    project = load_project(pdir)
    templates = list(project.get("templates") or [])
    if not templates:
        raise ValueError("No template history found in project.yaml")

    style_norm = (style or "full").strip().lower()
    if style_norm not in ("full", "concise"):
        raise ValueError("style must be one of: full, concise")

    brs_templates_dir = None
    try:
        brs_templates_dir = brs_loader.get_paths().templates_dir
    except Exception:
        brs_templates_dir = None

    citations: list[str] = []
    citation_seen: set[str] = set()
    versions: dict[str, str] = {}
    lines: list[str] = []

    project_name = str(project.get("name") or pdir.name)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines.append("# Methods Draft")
    lines.append("")
    lines.append(f"Project: **{project_name}**")
    lines.append(f"Generated: **{generated_at}**")
    lines.append("")
    lines.append("## Analysis History")
    lines.append("")

    for idx, entry in enumerate(templates, start=1):
        instance_id = str(entry.get("id") or f"template_{idx}")
        source_id = _resolve_source_template_id(entry, instance_id)
        params = entry.get("params") or {}

        lines.append(f"### {idx}. {instance_id}")
        lines.append("")
        lines.append(f"- Source template: `{source_id}`")
        lines.append(f"- Status: `{entry.get('status', 'unknown')}`")

        if isinstance(params, dict) and params:
            param_preview = ", ".join([f"`{k}`={_as_str(v)}" for k, v in sorted(params.items())[:10]])
            lines.append(f"- Key parameters: {param_preview}")

        methods_text = _load_methods_text(brs_templates_dir, source_id, style_norm)
        if methods_text:
            lines.append("")
            lines.append(methods_text)

        run_info = _load_run_info(pdir / instance_id / "results" / "run_info.yaml")
        if run_info:
            when = run_info.get("timestamp")
            cmd = run_info.get("command")
            if when:
                lines.append("")
                lines.append(f"- Run timestamp: `{_as_str(when)}`")
            if cmd:
                lines.append(f"- Run command: `{_as_str(cmd)}`")

            vmap = run_info.get("versions")
            if isinstance(vmap, dict):
                for k, v in vmap.items():
                    kk = str(k).strip()
                    vv = _as_str(v).strip()
                    if kk and vv:
                        versions.setdefault(kk, vv)
        # Fallback for tools executed from run.sh but not persisted in run_info.yaml
        # (for example Nextflow or bcl-convert).
        inferred = _infer_versions_from_artifacts(pdir / instance_id)
        for k, v in inferred.items():
            versions.setdefault(k, v)

        cits = _load_citations(brs_templates_dir, source_id)
        for c in cits:
            norm = c.lower().strip()
            if norm and norm not in citation_seen:
                citations.append(c)
                citation_seen.add(norm)

        lines.append("")

    lines.append("## Software and Package Versions")
    lines.append("")
    if versions:
        lines.append("| Software/Package | Version |")
        lines.append("|---|---|")
        for k in sorted(versions.keys()):
            lines.append(f"| {k} | {versions[k]} |")
    else:
        lines.append("No run-time version artifact found (`results/run_info.yaml`).")
        lines.append("Add version capture in each template `run.sh` to populate this table.")

    lines.append("")
    lines.append("## Citations")
    lines.append("")
    if citations:
        for c in citations:
            lines.append(f"- {c}")
    else:
        lines.append("No `citations.yaml` found in active BRS templates used by this project.")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This draft is generated from `project.yaml` history + BRS metadata.")
    lines.append("- Verify scientific wording and journal-specific formatting before submission.")

    return MethodsOutput(
        markdown="\n".join(lines).rstrip() + "\n",
        citation_count=len(citations),
        templates_count=len(templates),
    )


def _resolve_source_template_id(entry: dict[str, Any], instance_id: str) -> str:
    src = entry.get("source") or {}
    if isinstance(src, dict):
        tid = src.get("template_id")
        if tid:
            return str(tid)
    st = entry.get("source_template")
    return str(st or instance_id)


def _load_methods_text(brs_templates_dir: Path | None, source_id: str, style: str) -> str:
    if brs_templates_dir is None:
        return ""
    p = brs_templates_dir / source_id / "METHODS.md"
    if not p.exists():
        return ""
    txt = p.read_text(encoding="utf-8", errors="replace").strip()
    if not txt:
        return ""
    if style == "full":
        return txt
    # concise: keep first paragraph only
    paras = [x.strip() for x in txt.split("\n\n") if x.strip()]
    return paras[0] if paras else txt


def _load_citations(brs_templates_dir: Path | None, source_id: str) -> list[str]:
    if brs_templates_dir is None:
        return []
    p = brs_templates_dir / source_id / "citations.yaml"
    if not p.exists():
        return []
    raw = safe_load_yaml(p)

    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = raw.get("citations") or []
    else:
        items = []

    out: list[str] = []
    for it in items:
        if isinstance(it, str):
            s = it.strip()
            if s:
                out.append(s)
            continue
        if isinstance(it, dict):
            out.append(_format_citation_entry(it))
    return [x for x in out if x.strip()]


def _format_citation_entry(it: dict[str, Any]) -> str:
    cid = _as_str(it.get("id")).strip()
    text = _as_str(it.get("text") or it.get("citation") or it.get("title")).strip()
    doi = _as_str(it.get("doi")).strip()
    url = _as_str(it.get("url")).strip()

    parts: list[str] = []
    if cid:
        parts.append(f"[{cid}]")
    if text:
        parts.append(text)
    if doi:
        parts.append(f"DOI: {doi}")
    if url:
        parts.append(url)
    return " ".join(parts).strip()


def _load_run_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = safe_load_yaml(path)
    return raw if isinstance(raw, dict) else {}


def _infer_versions_from_artifacts(instance_dir: Path) -> dict[str, str]:
    out: dict[str, str] = {}

    text_files = [
        instance_dir / ".nextflow.log",
        instance_dir / "results" / ".nextflow.log",
        instance_dir / "nextflow.log",
        instance_dir / "results" / "nextflow.log",
    ]
    for p in text_files:
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        nf = _extract_nextflow_version(txt)
        if nf:
            out.setdefault("nextflow", nf)
        bcl = _extract_bcl_convert_version(txt)
        if bcl:
            out.setdefault("bcl-convert", bcl)

    yml_files = [
        instance_dir / "pipeline_info" / "software_versions.yml",
        instance_dir / "results" / "pipeline_info" / "software_versions.yml",
        instance_dir / "results" / "software_versions.yml",
        instance_dir / "software_versions.yml",
    ]
    for p in yml_files:
        if not p.exists():
            continue
        raw = safe_load_yaml(p)
        if not isinstance(raw, (dict, list)):
            continue
        ymap = _extract_versions_from_yaml(raw)
        if "nextflow" in ymap:
            out.setdefault("nextflow", ymap["nextflow"])
        if "bcl-convert" in ymap:
            out.setdefault("bcl-convert", ymap["bcl-convert"])
        flat = _flatten_strings(raw)
        for s in flat:
            nf = _extract_nextflow_version(s)
            if nf:
                out.setdefault("nextflow", nf)
            bcl = _extract_bcl_convert_version(s)
            if bcl:
                out.setdefault("bcl-convert", bcl)

    return out


def _extract_nextflow_version(text: str) -> str:
    patterns = [
        r"(?i)nextflow(?:\s+version|\s*:\s*version)?\s*v?([0-9]+(?:\.[0-9]+){1,3}(?:[-+._a-zA-Z0-9]*)?)",
        r"(?i)\bversion\s+([0-9]+(?:\.[0-9]+){1,3}(?:[-+._a-zA-Z0-9]*)?)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return ""


def _extract_bcl_convert_version(text: str) -> str:
    patterns = [
        r"(?i)bcl[- ]?convert(?:\s+version|\s*[:=])\s*v?([0-9]+(?:\.[0-9]+){1,3}(?:[-+._a-zA-Z0-9]*)?)",
        r"(?i)bcl[- ]?convert[^0-9]*v?([0-9]+(?:\.[0-9]+){1,3}(?:[-+._a-zA-Z0-9]*)?)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return ""


def _flatten_strings(v: Any) -> list[str]:
    out: list[str] = []
    if isinstance(v, dict):
        for k, vv in v.items():
            out.append(str(k))
            out.extend(_flatten_strings(vv))
    elif isinstance(v, list):
        for it in v:
            out.extend(_flatten_strings(it))
    elif v is not None:
        out.append(str(v))
    return out


def _extract_versions_from_yaml(v: Any) -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(v, dict):
        for k, vv in v.items():
            ks = str(k).strip().lower()
            if "nextflow" in ks:
                ver = _extract_version_scalar(vv)
                if ver:
                    out.setdefault("nextflow", ver)
            if "bcl-convert" in ks or "bcl_convert" in ks or "bclconvert" in ks:
                ver = _extract_version_scalar(vv)
                if ver:
                    out.setdefault("bcl-convert", ver)
            child = _extract_versions_from_yaml(vv)
            for ck, cv in child.items():
                out.setdefault(ck, cv)
    elif isinstance(v, list):
        for it in v:
            child = _extract_versions_from_yaml(it)
            for ck, cv in child.items():
                out.setdefault(ck, cv)
    return out


def _extract_version_scalar(v: Any) -> str:
    if isinstance(v, (str, int, float)):
        s = str(v).strip()
        if re.match(r"^[0-9]+(?:\.[0-9]+){1,3}(?:[-+._a-zA-Z0-9]*)?$", s):
            return s
    return ""


def _as_str(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)
