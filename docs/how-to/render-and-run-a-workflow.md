---
title: Run a Workflow
parent: How-To
nav_order: 6
has_toc: true
---

# Run a Workflow

```
bpm workflow run <id> [--project /path/to/project.yaml] [--<param-flag> <value>]
```

Notes
- `run` executes the workflow entry script from its workflow folder.
- If `--project` is provided, BPM loads that `project.yaml` and makes it available via `ctx`.
- Workflow runs can be recorded in `project.yaml` under a `workflows` list.
