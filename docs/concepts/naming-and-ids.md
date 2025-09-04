---
title: Naming & IDs
parent: Concepts
nav_order: 13
has_toc: true
---

# Naming & IDs

Clear, stable names keep projects reproducible and easy to automate.

## Why It Matters
- Used in commands: `bpm template render <id>` and `bpm workflow run <id>`.
- Used in paths: many templates use `${ctx.project.name}/${ctx.template.id}/`.
- Used in lookups: publish keys become stable handles to outputs.

## Types of Names
- Projects (`project.yaml:name`): human label for the project; often appears in paths.
- Stores (BRS id): the catalog identifier you add/activate.
- Templates/Workflows (`id`): folder name under `templates/` or `workflows/` and the descriptor `id`.
- Publish keys: names under `publish:` in `template_config.yaml`.

## Simple Rules
- Be filesystem‑safe: letters, numbers, `-` and `_`. No spaces or slashes.
- Keep it short and stable: avoid frequent renames once shared/used.
- Prefer lowercase for template/workflow ids: e.g., `demux_bclconvert`, `nf_align`.
- Project names: allow digits/uppercase if you like (`250903_TEST`), but avoid spaces.
- Publish keys: use `snake_case` and describe the artifact, e.g., `fastq_dir`, `multiqc_report`.

## Template/Workflow IDs
- Must match the folder and descriptor exactly.
  - Folder: `templates/hello/`
  - Descriptor: `templates/hello/template_config.yaml` with `id: hello`
- Used by the CLI and context: `ctx.template.id == 'hello'`.
- Changing an id requires renaming the folder and updating `id` in the descriptor (and any references).

Good ids
- `hello`, `demux_bclconvert`, `qc-multiqc`, `nf_align`

Avoid
- `Demux BCL Convert` (spaces)
- `align#1` (symbols)
- `../../weird` (path segments)
- Extremely long names

## Project Names
- Set in `project.yaml` as `name:` and used in path templates by convention.
- Examples: `250903_TEST`, `rna_seq_2024q3`.
- Avoid spaces; prefer `_` or `-` as separators.

## Store (BRS) IDs
- Shown in `bpm resource list` and used for activation.
- Keep short and unique, e.g., `uka_gf_brs` or `UKA_GF_BRS` (pick a style and stick to it).

## Publish Keys
- Keys under `publish:` identify outputs other steps/users will consume.
- Make them short, stable, and specific; document their type/shape.
- Examples: `fastq_dir` (dir), `multiqc_report` (file), `samples_table` (tsv).

## Validation in BPM
- BPM requires the descriptor `id` to equal the folder name; it does not impose a regex.
- Filesystem‑unsafe characters may still break paths — follow the simple rules above.

## Quick Checklist
- No spaces; only letters, numbers, `-` and `_`.
- Template/workflow `id` equals folder name and stays lowercase.
- Publish keys are `snake_case` and documented.
- Avoid renaming once published/used.
