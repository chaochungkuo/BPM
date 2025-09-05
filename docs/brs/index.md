---
title: BRS
nav_order: 7
has_toc: true
---

# Bioinformatics Resource Stores (BRS)

Simple catalogs of reusable templates and workflows you control.

- Add a store: `bpm resource add <path-or-git> --activate`
- Render and run: `bpm template render <id>` → `bpm template run <id>`
- Publish outputs to project state for easy reuse

Pages
- [BRS Anatomy](./anatomy.md): folder layout and discovery rules
- [repo.yaml Metadata](./repo-metadata.md): required fields and examples
- [Template Anatomy](./template-anatomy.md): descriptor, files, run entry, hooks, publish
- [Workflow Anatomy](./workflow-anatomy.md): similar to templates, focused on orchestration
- [Hooks & Adapters](./hooks-and-adapters.md): environment, validation, collection
- [Resolvers & Publish Keys](./resolvers-and-publish-keys.md): stable output names
- [Distribution Models](./distribution-models.md): local vs Git, pinning
- [Testing a BRS](./testing-a-brs.md): smoke tests and CI ideas
