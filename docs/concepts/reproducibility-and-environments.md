---
title: Reproducibility & Environments
parent: Concepts
nav_order: 11
has_toc: true
---

# Reproducibility & Environments

Make results repeatable by fixing parameters, paths, tools, and store versions.

## What BPM gives you
- Fixed params: precedence and `project.yaml` storage avoid hidden changes.
- Stable paths: `render.into` keeps outputs predictable across runs and hosts.
- Store versioning: the active BRS records `version` and `commit` in `stores.yaml`.

## Your part (inside templates/hooks)
- Pin tools: use modules/conda/container with explicit versions in `pre_run` hooks.
- Capture metadata: write tool versions and command lines to files next to outputs.
- Publish pointers: expose key outputs via `publish` so downstream steps don’t guess paths.

## Simple patterns
```
# hooks/env.py
def main(ctx):
    # Example: activate conda or module; keep it simple in your environment
    # os.environ["PATH"] = f"/opt/toolX-1.2/bin:" + os.environ["PATH"]
    return None
```

```
# template_config.yaml
hooks:
  pre_run:
    - hooks.env:main
```

## Recording context
- Include a small `RUN_INFO.txt` from `run.sh` with key versions and `ctx.params`.
- Consider adding a `publish` key like `run_info` pointing to that file.

## When to pin the store
- For regulated or shared work, use a tagged release of your BRS and avoid auto‑updates.
- `bpm resource update` refreshes the cache; record the resulting `version/commit` in change logs when you update.
