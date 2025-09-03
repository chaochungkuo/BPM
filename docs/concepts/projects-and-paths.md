---
title: Projects & Paths
parent: Concepts
nav_order: 1
has_toc: true
---

# Projects & Paths

- project.yaml holds project name and project_path (host-aware), used as the base for rendered paths in project mode.
- ctx.project_dir materializes project_path to a local absolute path.
- Ad‑hoc rendering uses `--out` as the base directory instead.

Key files:
- `project.yaml` (in project directory)
- `stores.yaml` (in cache: ~/.bpm_cache/stores.yaml)
