---
title: Run Lifecycle & Hooks
parent: Concepts
nav_order: 5
has_toc: true
---

# Run Lifecycle & Hooks

Keep the lifecycle simple and predictable.

## Lifecycle (templates)
1) Hooks: optional `pre_render` runs before any files are written. Runs in both project and ad‑hoc modes.
2) Render: Jinja renders files to the folder resolved from `render.into`.
3) Hooks: optional `post_render` runs (project and ad‑hoc modes).
4) Run: BPM executes `run.entry` (default `run.sh`) in that folder.
5) Hooks: optional `pre_run` and `post_run` run around the entry (project and ad‑hoc modes).
6) Status: on success, template status becomes `completed` in `project.yaml` (project mode) or in `bpm.meta.yaml` (ad‑hoc mode).

Notes
- Hooks are Python callables in the active BRS, referenced as dotted paths.
- Ad‑hoc mode stores state in `bpm.meta.yaml` inside the ad‑hoc folder.

## Hook config (template_config.yaml)
```
hooks:
  pre_render:
    - hooks.prepare_env:main
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

## Ad‑hoc metadata (bpm.meta.yaml)
Created at render time in ad‑hoc (`--out`) mode and updated by run/publish when executed from the ad‑hoc folder.

Example:
```
source:
  brs_id: UKA_GF_BRS
  brs_version: 0.1.1
  template_id: demux_bclconvert
params:
  bcl_dir: /path/to/run
  use_api_samplesheet: true
  reserve_cores: 10
status: completed
published:
  FASTQ_dir: host:/abs/path/to/FASTQs
  multiqc_report: host:/abs/path/to/multiqc/multiqc_report.html
```
