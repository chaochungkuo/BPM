---
title: Create a Project
parent: How-To
nav_order: 1
has_toc: true
---

# Create a Project

```
bpm project init 250903_TEST --outdir /abs/path
```

What it does
- Creates `/abs/path/250903_TEST` and writes `project.yaml`.
- Records `name`, `project_path`, optional authors, and sets `status: active`.

Check info
```
bpm project info --dir /abs/path/250903_TEST
bpm project status --dir /abs/path/250903_TEST
```

Tip
- Commit `project.yaml` to version control; avoid committing secrets.

