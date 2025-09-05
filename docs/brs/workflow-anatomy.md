---
title: Workflow Anatomy
parent: BRS
nav_order: 4
has_toc: true
---

# Workflow Anatomy

Workflows wrap multiple steps or tools without forcing a specific engine.

## Descriptor example
```
# workflows/clean/workflow.yaml
id: clean
description: Remove intermediates
params:
  keep_logs: {type: bool, default: true}
render:
  into: "${ctx.project.name}/${ctx.template.id}/"
  files:
    - run.sh.j2 -> run.sh
run:
  entry: run.sh
hooks:
  pre_run:
    - hooks.env:main
```

## Behavior
- Render and run mirror templates: files are generated, then `run.entry` executes in that folder.
- No built‑in `publish:` block; use templates to expose publishable outputs.
