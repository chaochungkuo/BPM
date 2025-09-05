---
title: Render a Template
parent: How-To
nav_order: 1
has_toc: true
---

# Render a Template
Quickly render files from a template.

Project mode
```
cd /abs/path/250903_TEST
bpm template render --param KEY=VALUE <id>
```

Ad‑hoc mode
```
bpm template render --out /tmp/out --param KEY=VALUE <id>
```

Tips
- Use `--dry` to preview planned actions without writing files.
- Pass multiple `--param` flags as needed; types are coerced.
- In ad‑hoc, files are written directly to `--out` and hooks are skipped.
