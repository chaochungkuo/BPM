---
title: Run Lifecycle & Hooks
parent: Concepts
nav_order: 5
has_toc: true
---

# Run Lifecycle & Hooks

Keep the lifecycle simple and predictable.

## Lifecycle (templates)
1) Render: Jinja renders files to the folder resolved from `render.into`.
2) Hooks: optional `post_render` runs (project mode only).
3) Run: BPM executes `run.entry` (default `run.sh`) in that folder.
4) Hooks: optional `pre_run` and `post_run` run around the entry.
5) Status: on success, template status becomes `completed` in `project.yaml`.

Notes
- Hooks are Python callables in the active BRS, referenced as dotted paths.
- Ad‑hoc mode (`--out`) skips hooks and does not touch `project.yaml`.

## Hook config (template_config.yaml)
```
hooks:
  post_render:
    - hooks.prepare_env:main
  pre_run:
    - hooks.shell:init
  post_run:
    - hooks.collect:main
```

## Hook signature
- A hook is `module:function` or just `module` (uses `main`).
- BPM imports from the active BRS and calls `fn(ctx)`.

## Minimal run.sh
```
# run.sh.j2
#!/usr/bin/env bash
set -euo pipefail
echo "Running {{ ctx.template.id }} for {{ ctx.params.sample_id }}" > run.log
```

## Failures
- Non‑zero exit from the entry or an exception in hooks fails the command; BPM prints stdout/stderr.
- Use idempotent runs when possible (check for existing outputs or a completion marker).
