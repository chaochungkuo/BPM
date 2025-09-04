---
title: Project vs Ad‑hoc
parent: Concepts
nav_order: 7
has_toc: true
---

# Project vs Ad‑hoc

Key points:
- Base directory: project mode uses `ctx.project_dir`; ad‑hoc uses `--out`.
- Render paths: in ad‑hoc, treat `render.into` as `.` unless overridden.
- State: project mode persists params and published outputs; ad‑hoc is ephemeral.
- Use cases: projects for tracked studies; ad‑hoc for quick utilities and one‑offs.

TODO:
- Show equivalent render commands in both modes.
- Clarify how published keys behave in ad‑hoc runs.

