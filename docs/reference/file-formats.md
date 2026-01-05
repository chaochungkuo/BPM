---
title: File Formats
parent: Reference
nav_order: 1
has_toc: true
---

# File Formats

## project.yaml
- name, project_path (host-aware), templates[] (id, status, params, published)
- workflows[] (id, status, params, started_at, finished_at, run_entry, args, error)

## stores.yaml
- schema_version, updated, active, stores{id, source, cache_path, version, commit, last_updated}

## template_config.yaml
- id, description, params, render.into, render.files, render.parent_directory, run.entry, publish, hooks
- tools: list or map of required/optional CLI tools to hint environment needs

## workflow_config.yaml
- id, description, params, run.entry, run.args, run.env, hooks
- tools: list or map of required/optional CLI tools to hint environment needs

Schema (minimal example):
```yaml
id: demo_workflow
description: Example workflow
params:
  name: {type: str, required: true, cli: --name}
  include_time: {type: bool, default: false, cli: --include-time}
run:
  entry: "run.sh"
  args:
    - "${ctx.params.name}"
    - "${ctx.params.include_time}"
  env:
    REPORT_DIR: "${ctx.project_dir}/reports"
hooks:
  pre_run: [hooks.env:main]
  post_run: [hooks.collect:main]
tools:
  required: [python]
  optional: [quarto]
```

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
