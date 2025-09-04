---
title: Performance & Caching
parent: Concepts
nav_order: 14
has_toc: true
---

# Performance & Caching

Key points:
- Rendering: aim for minimal file generation and reuse immutable assets.
- Cache: leverage store cache; avoid large binary duplication inside templates.
- Incrementality: detect existing outputs when safe; document when to force rerun.
- Large data: stream where possible; avoid deep directory traversals in hooks.

TODO:
- Offer patterns for cache‑aware templates.
- Note environment variables or flags that control cache behavior.

