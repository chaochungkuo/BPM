---
title: Use Ad‑hoc Mode
parent: How-To
nav_order: 5
has_toc: true
---

# Use Ad‑hoc Mode

Render outside a project without touching `project.yaml`.

```
bpm template render <id> --out /tmp/out --param KEY=VALUE
```

Behavior
- Renders files directly into `/tmp/out` (treats `render.into` as `.`).
- Skips hooks and project updates; writes `bpm.meta.yaml` with params and source info.

When to use
- Quick utilities, scratch work, or testing templates.

