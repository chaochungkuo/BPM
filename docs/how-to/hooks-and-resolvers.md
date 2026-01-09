---
title: Hooks and Resolvers (How-to)
parent: How-to
nav_order: 99
---

# Hooks and Resolvers: Practical Guide

Use this to wire template defaults, environment prep, and publishing in a clean, repeatable way.

## Hooks
- Location: `hooks/` in the BRS; importable as `hooks.mod:func` (default `main`).
- Signature: `def func(ctx): ...` where `ctx` provides `project`, `template`, `params`, `cwd`, `brs`. Don’t assume extra fields.
- Reference in `template_config.yaml` or `workflow_config.yaml`:
  ```yaml
  hooks:
    pre_render:
      - hooks.prepare:main
    post_run:
      - hooks.collect:main
  ```
- Common patterns:
  - **Pre-render**: fill missing params from `project.yaml` or upstream template outputs; normalize inputs; validate paths. If you need other templates, read `project.yaml` via `Path(ctx.materialize(ctx.project.project_path)) / "project.yaml"`.
  - **Pre-run**: set env vars, activate conda/venv, module load, container args.
  - **Post-run**: summarize outputs, write auxiliary metadata (not publish).
- Tips:
  - Detect placeholders/empties before overwriting params.
  - Avoid writing to disk unless needed; never mutate `project.yaml` here.
  - Keep hooks small and deterministic.

## Resolvers
- Location: `resolvers/` in the BRS; importable as `resolvers.mod:func` (default `main`).
- Signature: `def func(ctx, **kwargs): ...` returning JSON-serializable values.
- Primary use: `publish:` in `template_config.yaml`:
  ```yaml
  publish:
    multiqc_report:
      resolver: resolvers.reports:find
      args:
        pattern: "**/multiqc_report.html"
  ```
- Secondary use: call from hooks to fetch upstream values.
- Not for `params.default`: `${resolvers.*}` is not expanded there—use hooks instead.
- Tips:
  - Keep logic small; raise clear errors if required data is missing; return `None` for optional values.
  - Use explicit names (`get_salmon_dir_any`, `get_author_names`) to convey intent.

## Pattern: Filling params from project.yaml in pre_render
```python
from pathlib import Path
import yaml

def populate(ctx):
    params = ctx.params
    proj_templates = []
    if ctx.project:
        pyaml = Path(ctx.materialize(ctx.project.project_path)) / "project.yaml"
        if pyaml.exists():
            data = yaml.safe_load(pyaml.read_text()) or {}
            proj_templates = data.get("templates") or []

    def first_available(key_path, template_ids=("nfcore_3mrnaseq","nfcore_rnaseq")):
        for tid in template_ids:
            entry = next((t for t in proj_templates if t.get("id") == tid), None)
            if not entry:
                continue
            node = entry
            for k in key_path:
                node = node.get(k) if isinstance(node, dict) else None
                if node is None:
                    break
            if node is not None:
                return node
        return None

    def needs_fill(val):
        return (val is None) or (isinstance(val, str) and val.startswith("${resolvers."))

    if needs_fill(params.get("salmon_dir")):
        params["salmon_dir"] = first_available(["published","salmon_dir"])
    # repeat for other params...
```

## Testing and debugging
- Run `bpm template render <id> --debug` to see params before/after hooks.
- Ensure hooks/resolvers import cleanly (`python -m hooks.foo`).
- Keep `params.required` false if hooks will populate them; document auto-populated behavior in the template README.
