---
title: bpm workflow
parent: CLI
nav_order: 5
has_toc: true
---

# bpm workflow

Run workflows from the active BRS and optionally record run history.

## list
```
bpm workflow list [--format table|plain|json]
```
- Lists all workflows in the active BRS.

## info
```
bpm workflow info <id> [--format table|plain|json]
```
- Shows params, run entry/args/env, hooks, and tools for a workflow.

## run
```
bpm workflow run <id> [--project /path/to/project.yaml] [--<param-flag> <value> ...]
```
- Executes the workflow `run.entry` from its workflow folder.
- `--project` loads project.yaml and exposes it via `ctx`.
- Workflow params are provided via CLI flags defined in `params.*.cli` (e.g., `--name Alice`).

Notes
- Use workflows to orchestrate tools without introducing a new engine.
