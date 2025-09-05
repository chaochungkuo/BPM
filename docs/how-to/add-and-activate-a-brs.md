---
title: Add and Activate a BRS
parent: How-To
nav_order: 2
has_toc: true
---

# Add and Activate a BRS

Add a local folder
```
bpm resource add ./UKA_GF_BRS --activate
bpm resource list
```

Add a Git repo
```
bpm resource add https://github.com/your-org/UKA_GF_BRS.git --activate
```

Inspect
```
bpm resource info
```

Update cache
```
bpm resource update --all
```

Notes
- The active store determines which templates/workflows you can render.
- Cache root defaults to `~/.bpm_cache` (override with `BPM_CACHE`).

