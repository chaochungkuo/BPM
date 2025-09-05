---
title: repo.yaml Metadata
parent: BRS
nav_order: 2
has_toc: true
---

# repo.yaml Metadata

Identify your store and communicate its purpose and version.

## Minimal example
```
id: UKA_GF_BRS
name: UKA Genomics Facility Store
description: Common genomics templates and workflows
version: 1.2.0
compatibility: BPM>=0.1
```

Notes
- `id`: short, stable identifier used in `bpm resource` commands.
- `version`: bump when you change templates in a way users should notice.
- `compatibility`: optional note to signal expected BPM versions.
