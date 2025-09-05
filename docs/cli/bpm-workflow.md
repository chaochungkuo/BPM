---
title: bpm workflow
parent: CLI
nav_order: 5
has_toc: true
---

# bpm workflow

Render and run workflows from the active BRS. Workflows do not modify `project.yaml`.

## render
```
bpm workflow render <id> [--dir <project_dir>] [--dry] [--param KEY=VALUE ...]
```
- Renders workflow files into `${ctx.project.name}/${ctx.template.id}/` under the project.
- `--dry` prints a plan of actions without writing files.
- `--param` overrides descriptor defaults for this invocation.

## run
```
bpm workflow run <id> [--dir <project_dir>]
```
- Executes the `run.entry` (default `run.sh`) in the rendered folder.

Notes
- Use workflows to orchestrate multiple tools without introducing a new engine.
- Hooks in `workflow.yaml` run around the entry similar to templates.

