---
title: Distribution Models
parent: BRS
nav_order: 7
has_toc: true
---

# Distribution Models

Choose a local folder for development, use Git for sharing, and pin versions for stability.

## Local directory
```
bpm resource add ./UKA_GF_BRS --activate
bpm resource list
```

## Git repository
```
bpm resource add https://github.com/your-org/UKA_GF_BRS.git --activate
# Or SSH
bpm resource add git@github.com:your-org/UKA_GF_BRS.git --activate
```

## Pinning versions
- Prefer tags or commit SHAs in your workflow docs or environment bootstrap.
- After updates, BPM records `version` and `commit` in `stores.yaml`.

## Multi‑store setups
- Add multiple stores and switch the active one per need.
- Keep ids short and unique.
