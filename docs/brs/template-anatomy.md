---
title: Template Anatomy
parent: BRS
nav_order: 3
has_toc: true
---

# Template Anatomy

Define params, files to render, what to run, and what to publish.

## Descriptor example
```
# templates/hello/template_config.yaml
id: hello
description: Minimal demo template
params:
  sample_id: {type: str, required: true}
  threads:   {type: int, default: 8}
  input_dir: {type: str, required: true, exists: dir}
render:
  into: "${ctx.project.name}/${ctx.template.id}/"
  files:
    - run.sh.j2 -> run.sh
run:
  entry: run.sh
publish:
  sample_file:
    resolver: resolvers.files:find
    args: {pattern: "run.out"}
hooks:
  pre_run:
    - hooks.env:main
```

## File mapping
- `*.j2` files render with Jinja and can access `ctx`.
- Non‑Jinja files are copied as‑is.
- If `run.entry` is present, BPM marks it executable after render.

## Minimal run script
```
# templates/hello/run.sh.j2
#!/usr/bin/env bash
set -euo pipefail
echo "Sample: {{ ctx.params.sample_id }}" > run.out
```

Legacy note: `template.config.yaml` is still supported, but prefer `template_config.yaml`.
