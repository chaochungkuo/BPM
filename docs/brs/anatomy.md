---
title: BRS Anatomy
parent: BRS
nav_order: 1
has_toc: true
---

# BRS Anatomy

Keep the layout flat and predictable.

## Recommended layout
```
UKA_GF_BRS/
  repo.yaml
  config/
    authors.yaml   (optional)
    hosts.yaml     (optional)
    settings.yaml  (optional)
  templates/
    hello/
      template_config.yaml   # or legacy: template.config.yaml
      run.sh.j2
      README.md              (optional)
  workflows/
    clean/
      workflow_config.yaml
      run.sh
  hooks/
    env.py
  resolvers/
    files.py
```

## Discovery rules
- Templates: `templates/<id>/template_config.yaml` (preferred) or `template.config.yaml` (legacy).
  - `render.parent_directory` (optional): inserts a folder above the template folder in project mode.
- Workflows: `workflows/<id>/workflow_config.yaml`.
- Hooks: importable Python modules under `hooks/`.
- Resolvers: importable Python modules under `resolvers/`.

## Metadata
- `repo.yaml` names the store, version, and optional compatibility notes.
