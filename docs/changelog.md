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
  - Simplified descriptor discovery: only `template_config.yaml` and `workflow_config.yaml` are supported; missing descriptors now return explicit errors pointing at those paths.
  - Templates can be rendered with an `--alias`; project entries store `id=<alias>` and `source_template=<descriptor id>` to allow multiple instances of the same template.
