---
title: Hooks & Adapters
parent: BRS
nav_order: 5
has_toc: true
---

# Hooks & Adapters

Small Python functions that prepare the environment or collect results.

## Where they live
- Under `hooks/` in your BRS, importable as modules.

## Referencing hooks
- In `template_config.yaml` or `workflow.yaml`:
```
hooks:
  post_render:
    - hooks.prepare:main
  pre_run:
    - hooks.env:init
  post_run:
    - hooks.collect:main
```
- Use `module:function` or just `module` (defaults to `main`).

## Hook signature
```
# hooks/env.py
def main(ctx):
    # set up environment, validate inputs, etc.
    return None
```

## Common patterns
- Modules: load cluster modules or set PATHs.
- Conda/venv: activate environments before running tools.
- Containers: prepare `singularity/docker` invocations.
- Collection: summarize outputs or write auxiliary metadata files.
