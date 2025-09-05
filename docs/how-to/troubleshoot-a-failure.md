---
title: Troubleshoot a Failure
parent: How-To
nav_order: 7
has_toc: true
---

# Troubleshoot a Failure

Render plan first
```
bpm template render <id> --dry
```

Provide params
```
bpm template render <id> --param KEY=VALUE --param threads=8
```

Read the error
- Undefined Jinja variable → add a param or fix the template.
- Entry not found or permission denied → ensure `run.sh` renders and is executable.
- Tool not found → load modules/conda/container in hooks or script.

Inspect outputs
- Check the rendered folder under `render.into`.
- In ad‑hoc mode, look in `--out` and `bpm.meta.yaml`.

See also
- Concepts → Error Handling & Diagnostics for more detail.

