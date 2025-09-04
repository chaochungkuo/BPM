---
title: Stores & Cache
parent: Concepts
nav_order: 8
has_toc: true
---

# Stores & Cache

Add, activate, and update BRS catalogs; BPM caches them locally.

## Cache location
- Default root: `~/.bpm_cache` (override with `BPM_CACHE=/path/to/cache`).
- Cache layout: `stores.yaml` + `brs/<id>/` directories.

## Managing stores (CLI)
```
bpm resource add ./UKA_GF_BRS --activate
bpm resource list
bpm resource info
bpm resource update --all
bpm resource remove <id>
```

## How activation works
- The active store id is recorded in `stores.yaml`.
- BPM resolves the active BRS cache path and loads templates/workflows from there.

## Updates and pinning
- `bpm resource update` refreshes cache content and records `version` and `commit`.
- For reproducibility, use tagged releases or commits; avoid auto‑updating mid‑project.

## Offline behavior
- Once cached, templates and metadata load from the cache even without network access.
