---
title: Error Handling & Diagnostics
parent: Concepts
nav_order: 12
has_toc: true
---

# Error Handling & Diagnostics

Keep this simple: preview what will happen, fix inputs, and read the error.

## Quick Checklist
- Render dry‑run: `bpm template render --dry <id>` to preview actions and catch Jinja issues.
- Provide params: add `--param KEY=VALUE` (repeatable) for required inputs.
- Correct mode: use a project (`project.yaml`) or `--out /tmp/out` for ad‑hoc.
- Right template id: `bpm template list` to confirm available ids in the active BRS.

## Common Render Errors
- Undefined variable: Jinja error like “'x' is undefined”.
  - Fix: pass `--param x=...` or set a default in `template_config.yaml` under `params:`.
- Invalid `--param` format: “Invalid --param 'x' Expected KEY=VALUE.”
  - Fix: use `--param name=value` (no spaces around `=`).
- Missing dependencies: “Missing required templates: demux_bclconvert”.
  - Fix: render/run the listed templates first, or remove the dependency.
- Missing source file: “Template not found: run.sh.j2”.
  - Fix: ensure the file exists in the template folder and mapping is correct.
- Jinja syntax error: “Jinja syntax error in run.sh.j2:12: unexpected …”.
  - Fix: correct the template syntax; keep `{{ ctx.* }}` for values.

Tip: Use placeholders in `render.into` like `${ctx.project.name}/${ctx.template.id}/` to avoid hard‑coding paths.

## Common Run Errors
- Entry not found: “Command failed: ./run.sh … No such file or directory”.
  - Fix: ensure you rendered first; mapping `run.sh.j2 -> run.sh` must exist.
- Permission denied: “./run.sh: Permission denied”.
  - Fix: BPM auto‑chmods the `run.entry`. Make sure `run.entry` is set (e.g., `run.sh`) and the file renders.
- Tool not found: errors from your script (e.g., “nextflow: command not found”).
  - Fix: load modules/conda/container in hooks or at script start.
- Non‑zero exit: BPM prints stdout/stderr from the script when it fails.
  - Fix: read the printed sections; re‑run after addressing the root cause.

## Publish Errors
- Bad resolver spec: “Publish entry 'X' missing 'resolver' key”.
  - Fix: add `resolver:` to each publish item in `template_config.yaml`.
- Resolver import/function missing: “Function 'main' not found …”.
  - Fix: check the dotted path (e.g., `resolvers.fastq_dir:main`) exists in the active BRS.

## Where To Look
- Render folder: under `render.into` resolved in project/ad‑hoc mode. Check generated files and outputs.
- Console output: on failures, BPM prints a clear “Error: …” with stdout/stderr for `run`.
- Project state: `project.yaml` shows saved params, template status, and published results.
- Ad‑hoc meta: `bpm.meta.yaml` is written in `--out` for provenance.

## Reproduce Minimally
- Show plan only: `bpm template render --dry <id>`
- Use a clean out dir: `bpm template render --out /tmp/out <id>` then inspect files in `/tmp/out`.
- Add one param at a time: `--param key=value` to pinpoint the offending variable.

## How CLI, project.yaml, and template_config.yaml interact
- `template_config.yaml`: defines defaults (`params`), where files go (`render.into`), what to render (`render.files`), and what to run (`run.entry`).
- `project.yaml`: defines project identity (`name`, `project_path`) and stores last params and published outputs.
- CLI: `--param` overrides values for the current render/run; `--dry` previews; `--out` switches to ad‑hoc mode (no project changes, writes `bpm.meta.yaml`).

Simple rule: if render fails, fix parameters or templates; if run fails, read stdout/stderr and fix your script or environment.
