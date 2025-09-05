---
title: Project vs Ad‑hoc
parent: Concepts
nav_order: 8
has_toc: true
---

# Project vs Ad‑hoc

Two ways to use BPM depending on how much state you want.

## Project mode (stateful)
- Base directory: `ctx.project_dir` (materialized from `project.yaml:project_path`).
- Render path: `${ctx.project.name}/${ctx.template.id}/` by default (or your `render.into`).
- State: persists final params and published outputs in `project.yaml`.
- Hooks: runs `post_render`, `pre_run`, `post_run` if configured.
- Commands: `bpm template render`, `bpm template run`, `bpm template publish`.

Example
```
cd /abs/path/250903_TEST
bpm template render --param sample_id=NA12878 hello
bpm template run hello
bpm template publish hello
```

## Ad‑hoc mode (stateless)
- Base directory: `--out <dir>`.
- Render path: treats `render.into` as `.` (files land directly in `--out`).
- State: does not modify `project.yaml`; writes `bpm.meta.yaml` into `--out` with params and source info.
- Hooks: skipped (no post_render/pre_run/post_run).
- Commands: `bpm template render --out <dir> …` (no BPM `run`/`publish` in ad‑hoc).

Example
```
bpm template render --out /tmp/out --param sample_id=NA12878 hello
# Then, if needed, run manually:
cd /tmp/out && ./run.sh
```

## Pick the right mode
- Use Project mode for tracked studies, sharing results, and repeatability.
- Use Ad‑hoc mode for quick utilities, testing, scratch work, or when no project is needed.

## Differences at a glance
- Paths: Project uses `${ctx.project.name}/${ctx.template.id}/`; Ad‑hoc writes into `--out`.
- Params: Both honor precedence (descriptor < project < CLI), but Ad‑hoc has no project layer and no persistence.
- Publish: Project writes publish keys to `project.yaml`; Ad‑hoc does not publish.
- Hooks: Project runs hooks; Ad‑hoc skips them.

Tip
- Keep `render.into` relative and placeholder‑based for project mode. In ad‑hoc, BPM ignores it and writes directly to `--out`.
- Avoid relying on `ctx.project.*` inside parameter defaults if you plan to use ad‑hoc; the project is not present there.
