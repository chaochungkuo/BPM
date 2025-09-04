---
title: Path Resolution Rules
parent: Concepts
nav_order: 11
has_toc: true
---

# Path Resolution Rules

Keep paths predictable and portable by using placeholders and letting BPM resolve them.

## Base Directory
- Project mode: base is `ctx.project_dir` (from `project.yaml:project_path`).
- Ad‑hoc mode: base is `--out` (no project changes; writes `bpm.meta.yaml`).

All renders go to: `target = base / render.into` after placeholder expansion, then normalized to an absolute path.

## Placeholders in `render.into`
- Use `${ctx.project.name}`, `${ctx.template.id}` and other `ctx.*` values.
- Default pattern (if omitted): `${ctx.project.name}/${ctx.template.id}/`.
- Examples:
  - `${ctx.project.name}/${ctx.template.id}/` → `250903_TEST/hello/`
  - `results/${ctx.template.id}` → `results/hello`

## Examples (project mode)
Assume `project_path=/abs/250903_TEST`, `name=250903_TEST`, and template id `hello`.
- `render.into: "${ctx.project.name}/${ctx.template.id}/"`
  - Resolves to `/abs/250903_TEST/250903_TEST/hello/`
- `render.into: "results/${ctx.template.id}"`
  - Resolves to `/abs/250903_TEST/results/hello`
- `render.into: "."`
  - Resolves to `/abs/250903_TEST`

Ad‑hoc mode (`--out /tmp/out`): treat paths relative to `/tmp/out` unless you use an absolute path.

## Relative vs Absolute
- Prefer relative `render.into` paths so templates work everywhere.
- Absolute paths (e.g., `/scratch/run1`) are respected but reduce portability.
- Avoid `..` segments; BPM resolves the path, but leaving the project/out directory is discouraged.

## Cross‑platform Tips
- Use forward slashes in templates; Python normalizes them on Windows/Unix.
- Don’t hard‑code drive letters or home shortcuts; prefer placeholders and relative paths.

## Run Working Directory
- `bpm template run` changes into the resolved `render.into` directory and executes `run.entry` there.
- Inside scripts, prefer relative paths to the working directory, or use `{{ ctx.project_dir }}` for absolute project references.

## Quick Checklist
- Keep `render.into` relative; rely on placeholders.
- Include `${ctx.template.id}` to avoid collisions between templates.
- Use stable, filesystem‑safe names (see Naming & IDs).
- In ad‑hoc mode, pass `--out` instead of embedding absolute locations.
