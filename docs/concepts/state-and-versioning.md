---
title: State & Versioning
parent: Concepts
nav_order: 9
has_toc: true
---

# State & Versioning

Keep project and store state small, explicit, and versioned.

## project.yaml (per project)
Holds project identity and template status.
```
name: 250903_TEST
project_path: /abs/path/250903_TEST
status: active
templates:
  - id: hello
    status: completed
    params: {sample_id: NA12878, threads: 16}
    published:
      fastq_dir: /abs/path/250903_TEST/250903_TEST/hello/fastq
```
- Render sets/updates the `params` and marks status `active`.
- Run sets template status to `completed`.
- Publish writes/updates the `published` map.

## stores.yaml (global cache)
Lives under `~/.bpm_cache/stores.yaml` (override with `BPM_CACHE`).
Tracks added stores, the active one, and cached version info.
```
schema_version: 1
updated: 2024-09-03T12:34:56Z
active: UKA_GF_BRS
stores:
  UKA_GF_BRS:
    id: UKA_GF_BRS
    source: /path/to/UKA_GF_BRS
    cache_path: /home/user/.bpm_cache/brs/UKA_GF_BRS
    version: 1.2.0
    commit: 1a2b3c4
    last_updated: 2024-09-03T12:34:56Z
```

## Versioning guidance
- Pin your store by tag/commit for shared/reproducible projects.
- Document store updates in change logs and rerun publishing if keys change.
- Commit `project.yaml` to your VCS; do not commit `stores.yaml` (it’s user‑local).
