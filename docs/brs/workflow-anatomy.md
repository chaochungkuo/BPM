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
# workflows/clean/workflow_config.yaml
id: clean
description: Remove intermediates
params:
  keep_logs: {type: bool, default: true}
run:
  entry: run.sh
hooks:
  pre_run:
    - hooks.env:main
```

## Behavior
- Workflows execute entry scripts from their own folder (no render step).
- `pre_run`/`post_run` hooks run around the entry if defined.
- No built‑in `publish:` block; use templates to expose publishable outputs.
