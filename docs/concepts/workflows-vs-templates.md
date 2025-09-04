---
title: Workflows vs Templates
parent: Concepts
nav_order: 6
has_toc: true
---

# Workflows vs Templates

Pick the right abstraction for your job: single tool (template) or orchestration (workflow).

## Templates
- Descriptor: `templates/<id>/template_config.yaml`.
- Capabilities: params, render files, run entry, hooks, publish.
- State: params and published values persist in `project.yaml`.
- CLI: `bpm template render/run/publish <id>`.

## Workflows
- Descriptor: `workflows/<id>/workflow.yaml` (similar shape to templates for params/render/run).
- Capabilities: params, render files, run entry, hooks; no built‑in `publish`.
- State: render/run do not persist params into `project.yaml` (day‑1 behavior).
- CLI: `bpm workflow render/run <id>`.

## Defaults and paths
- Both use the same default `render.into`: `${ctx.project.name}/${ctx.template.id}/`.
- `bpm workflow run` executes in that folder; entry defaults to `run.sh` if not set.

## Minimal workflow example
```
# workflows/clean/workflow.yaml
id: clean
description: Remove intermediates
params:
  keep_logs: {type: bool, default: true}
render:
  files:
    - run.sh.j2 -> run.sh
run:
  entry: run.sh
```

When to choose
- Use templates for atomic, publishable units (e.g., “demux”, “align”, “multiqc”).
- Use workflows to wrap multiple steps or to add orchestration without introducing a new engine.
