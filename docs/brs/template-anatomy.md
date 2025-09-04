---
title: Template Anatomy
parent: BRS
nav_order: 3
has_toc: true
---

# Template Anatomy

Key points:
- Descriptor: `template_config.yaml` defines id, description, params, `render.into`, `render.files`, `run.entry`, `publish`, `hooks`.
- Files: templates typically include `run.sh.j2` mapped to `run.sh` and any auxiliary files.
- Behavior: strict Jinja rendering; entry executes in the rendered folder.

TODO:
- Add a full `template_config.yaml` example with comments.
- Show a simple `run.sh.j2` → `run.sh` mapping.

