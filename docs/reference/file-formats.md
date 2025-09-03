---
title: File Formats
parent: Reference
nav_order: 1
has_toc: true
---

# File Formats

## project.yaml
- name, project_path (host-aware), templates[] (id, status, params, published)

## stores.yaml
- schema_version, updated, active, stores{id, source, cache_path, version, commit, last_updated}

## template_config.yaml
- id, description, params, render.into, render.files, run.entry, publish, hooks
