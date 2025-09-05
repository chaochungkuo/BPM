---
title: Render and Run a Workflow
parent: How-To
nav_order: 6
has_toc: true
---

# Render and Run a Workflow

```
bpm workflow render <id> [--dir <project_dir>] [--dry] [--param KEY=VALUE]
bpm workflow run <id> [--dir <project_dir>]
```

Notes
- Renders into `${ctx.project.name}/${ctx.template.id}/` under the project.
- `run` executes the `run.entry` (default `run.sh`) in that folder.
- Workflows do not update `project.yaml` (no stored params/publish by default).

