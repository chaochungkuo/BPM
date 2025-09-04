---
title: Context (ctx) Model
parent: Concepts
nav_order: 2
has_toc: true
---

# Context (ctx) Model

The context is a simple, read‑only bundle of values available when BPM renders files and runs your entry script. You reference it inside templates to keep paths and parameters consistent.

## What’s In The Context
- `ctx.project`: project information (e.g., `name`).
- `ctx.project_dir`: absolute path to the project root (project mode) or `None` (ad‑hoc mode).
- `ctx.template`: template information (e.g., `id`, `render.into`, `run.entry`).
- `ctx.params`: all parameters resolved for this render/run.

## Where Context Comes From
- Template defaults: from `template_config.yaml` under `params:`.
- Project state: from `project.yaml` (project name/path and any saved params for prior runs).
- CLI overrides: from flags like `--param key=value` on `bpm template render/run`.

Parameter precedence (lowest → highest):
- Defaults in `template_config.yaml` → values saved in `project.yaml` → CLI `--param` flags.

## How You Use It
You can access context values in two places:
- In rendered files (Jinja): `{{ ctx.params.sample_id }}`, `{{ ctx.project.name }}`.
- In path templates (placeholders): `${ctx.project.name}/${ctx.template.id}/` for `render.into`.

Strict rendering: if a referenced value is missing, rendering fails with a clear error. This helps catch typos and missing params early.

## Minimal End‑to‑End Example

1) `project.yaml` (created with `bpm project init`)
```
name: 250903_TEST
project_path: /abs/path/250903_TEST
```

2) `templates/hello/template_config.yaml` in your BRS
```
id: hello
description: Minimal demo template
params:
  sample_id: "demo"   # default; can be overridden
render:
  into: "${ctx.project.name}/${ctx.template.id}/"  # resolves under the project
  files:
    - run.sh.j2 -> run.sh
run:
  entry: "run.sh"
publish:
  sample_file: run.out
```

3) `templates/hello/run.sh.j2` (Jinja)
```
#!/usr/bin/env bash
set -euo pipefail
echo "Sample: {{ ctx.params.sample_id }}" > run.out
```

4) CLI (project mode)
```
cd /abs/path/250903_TEST
# Render with an override (CLI > project > defaults)
bpm template render --param "sample_id=NA12878" hello

# Run entry script in the rendered folder
bpm template run hello

# Optionally publish named outputs
bpm template publish hello
```

Results:
- Files render to `/abs/path/250903_TEST/250903_TEST/hello/` (because `render.into` uses `${ctx.project.name}/${ctx.template.id}/`).
- `run.sh` prints with the resolved parameter and writes `run.out`.
- `publish` can record `sample_file: <path-to-run.out>` back to project state for discovery.

## Communicating Via CLI, project.yaml, template_config.yaml
- CLI → Context: use `--param key=value` to set `ctx.params.key` for this invocation. Use the active store and template id to pick which template to render/run.
- `project.yaml` → Context: sets `ctx.project.name` and materializes `ctx.project_dir` from `project_path`. It may store prior params and published outputs for repeatability.
- `template_config.yaml` → Context: defines defaults (`params`), where to render (`render.into`), which files to render (`render.files`), and what to run (`run.entry`).

Tip: In ad‑hoc mode (`bpm template render --out /tmp/out hello`), `ctx.project_dir` is not used; the base becomes `--out`, and `render.into` is treated as `.` unless you explicitly change it.

That’s it: set params with the CLI, keep project identity in `project.yaml`, and author templates with `template_config.yaml` that read from `ctx` for reliable, repeatable runs.
