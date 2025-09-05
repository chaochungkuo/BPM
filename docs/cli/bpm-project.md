---
title: bpm project
parent: CLI
nav_order: 2
has_toc: true
---

# bpm project

Create a project and inspect its state.

## init
```
bpm project init <project_name> --outdir <dir> [--author ckuo,lgan] [--host nextgen]
```
- Writes `project.yaml` in `<dir>/<project_name>`.
- Records `name`, `project_path` (host-aware), optional authors, and sets `status: active`.

## info
```
bpm project info [--dir <project_dir>] [--format plain|table|json]
```
- Shows name, status, authors, and listed templates.

## status
```
bpm project status [--dir <project_dir>] [--format plain|table|json]
```
- Shows template ids with current statuses (e.g., `active`, `completed`).

Notes
- `--dir` defaults to `.` and must contain `project.yaml`.
- Use VCS to track `project.yaml` over time; avoid committing secrets.

