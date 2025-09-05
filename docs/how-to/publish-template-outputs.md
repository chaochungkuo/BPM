---
title: Publish Template Outputs
parent: How-To
nav_order: 4
has_toc: true
---

# Publish Template Outputs

After a successful run, publish named outputs defined in `publish:`.

```
bpm template publish <id> [--dir <project_dir>]
```

What happens
- BPM imports resolver functions from the active BRS and calls them with `ctx`.
- Results are written to `project.yaml` under this template’s `published` map.

Why
- Downstream steps and teammates can discover outputs by key (e.g., `fastq_dir`, `multiqc_report`).

