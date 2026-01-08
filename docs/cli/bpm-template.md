---
title: bpm template
parent: CLI
nav_order: 3
has_toc: true
---

# bpm template

Render, run, and publish templates from the active BRS.

## render
```
bpm template render <id> [--dir <project_dir>] [--dry] [--param KEY=VALUE ...] [--out <adhoc_dir>]
```
- Project mode: renders into `${ctx.project.name}/${ctx.template.id}/` under `--dir` (default `.`), updates `project.yaml`.
- Ad‑hoc mode: with `--out`, renders into that directory (treats `render.into` as `.`) and writes `bpm.meta.yaml`; skips hooks and project updates.
- `--dry` prints the plan only; no file changes.
- Tip: discover template parameters with `bpm template info <id>`.
- If the template declares `tools:` in its descriptor, render prints a non-fatal warning for tools not found on `PATH` so you can activate the right environment before `run`.

## run
```
bpm template run <id> [--dir <project_dir>]
```
- Runs the `run.entry` (default `run.sh`) in the rendered folder. Executes hooks if configured.

## publish
```
bpm template publish <id> [--dir <project_dir>]
```
- Executes all resolvers in `publish:` and persists results to `project.yaml` under this template’s `published` map.

## list
```
bpm template list [--format table|plain|json]
```
- Shows available templates in the active BRS with their descriptions.

## info
```
bpm template info <id> [--format table|plain|json]
```
- Shows detailed info for a template: params (type/required/default/cli), render target and files, hooks, dependencies, tools, and publish resolvers.

## readme
```
bpm template readme <id>
```
- Prints the template README.md from the active BRS (if present).

Tips
- Use `--param` to override descriptor defaults; types are coerced (`int`, `float`, `bool`, `str`).
- Missing required params cause render to fail early with a clear error.
 - Default output format is `table` (use `--format plain|json` to override).
