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
- id, description, params, render.into, render.files, render.parent_directory, run.entry, publish, hooks
- tools: list or map of required/optional CLI tools to hint environment needs

Param fields:
- name (map key), type, required, default, cli, exists, description

Examples:
- Simple list (treated as required):
  tools: [fastqc, multiqc]
- Explicit groups:
  tools:
    required: [fastqc, multiqc]
    optional: [bcl-convert]

Notes:
- render.parent_directory: Optional extra folder inserted above the rendered template folder in project mode. For example, with `render.into: "${ctx.project.name}/${ctx.template.id}/"` and `render.parent_directory: analysis`, files render into `<project_dir>/<project.name>/analysis/<template.id>/`. Ad-hoc mode ignores this and renders directly into the provided output directory.
