---
title: Templates & Rendering
parent: Concepts
nav_order: 2
render_with_liquid: false
has_toc: true
---

# Templates & Rendering

Keep templates declarative: list params, files, where to render, and what to run.

## Descriptor (template_config.yaml)
```
id: hello
description: Minimal demo
params:
  sample_id: {type: str, required: true}
render:
  into: "${ctx.project.name}/${ctx.template.id}/"  # default if omitted
  files:
    - run.sh.j2 -> run.sh
run:
  entry: run.sh
publish:
  sample_file:
    resolver: resolvers.files:find
    args: {pattern: "run.out"}
```

## Files section
- `src -> dst` mappings under `render.files`.
- `*.j2` sources render with Jinja and have access to `ctx`.
- Non‑Jinja files are copied as‑is.
- If `run.entry` is defined, BPM marks the destination as executable.

## Jinja basics
- Strict mode: undefined variables raise errors (helps catch typos).
- Access context as `{{ ctx.params.* }}`, `{{ ctx.project.name }}`, etc.

Examples
{% raw %}
```
{{ ctx.params.sample_id }}
${ctx.project.name}/${ctx.template.id}/
```
{% endraw %}

## Project vs Ad‑hoc
- Project mode: base is `ctx.project_dir` (materialized from `project.yaml`).
- Ad‑hoc mode: `bpm template render --out /tmp/out hello` renders into `/tmp/out` and ignores `render.into` (treated as `.`). Hooks are skipped; BPM writes `bpm.meta.yaml` with params and source info.
