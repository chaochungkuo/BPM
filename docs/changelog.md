---
title: Changelog
nav_order: 9
has_toc: true
---

# Changelog

High-level, user-facing changes by release.

- Unreleased
  - Initial docs with Just‑the‑Docs.
  - Resource update command and template/run path fixes.
  - Descriptor discovery now prefers `template_config.yaml` / `workflow_config.yaml` and returns clearer missing-descriptor errors (legacy `template.config.yaml` remains supported).
  - Templates can be rendered with an `--alias`; project entries store `id=<alias>` and `source_template=<descriptor id>` to allow multiple instances of the same template.
  - Added `bpm agent` command group docs (`config`, `doctor`, `start`, `history`) including provider-backed chat mode and transcript history.
  - Added `bpm agent methods` command docs for generating publication-oriented methods drafts from `project.yaml` + BRS metadata (`METHODS.md`, `citations.yaml`, `run_info.yaml`).
  - Updated CLI overview/index to include `bpm agent`.
  - Updated installation docs for pixi dev tasks and version sync/check workflow.
