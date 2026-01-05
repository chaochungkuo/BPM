---
title: Workflows vs Templates
parent: Concepts
nav_order: 7
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
- Descriptor: `workflows/<id>/workflow_config.yaml` (similar shape to templates for params/run).
- Capabilities: params, run entry, hooks; no built‑in `publish`.
- State: can record run history in `project.yaml` when `--project` is provided.
- CLI: `bpm workflow run <id>`.

## Defaults and paths
- `bpm workflow run` executes in the workflow folder; entry defaults to `run.sh` if not set.

## Minimal workflow example
```
# workflows/clean/workflow_config.yaml
id: clean
description: Remove intermediates
params:
  keep_logs: {type: bool, default: true}
run:
  entry: run.sh
```

When to choose
- Use templates for atomic, publishable units (e.g., “demux”, “align”, “multiqc”).
- Use workflows to wrap multiple steps or to add orchestration without introducing a new engine.
