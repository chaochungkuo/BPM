---
title: BRS
nav_order: 7
has_toc: true
---

# Bioinformatics Resource Stores (BRS)

- A BRS is a catalog of reusable templates/workflows with metadata (`repo.yaml`).
- Add to BPM with `bpm resource add <path> --activate`.
- Each template documents its parameters, outputs, and publish keys.

Recommended layout:
- `repo.yaml`, `config/`, `templates/`, `workflows/`, `hooks/`, `resolvers/`
