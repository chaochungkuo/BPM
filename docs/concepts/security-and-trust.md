---
title: Security & Trust
parent: Concepts
nav_order: 16
has_toc: true
---

# Security & Trust

Treat BRS content like code you execute — review and scope it.

## What runs
- Jinja renders files from the active BRS (no code execution yet).
- Hooks and resolvers are imported from the active BRS and called as Python.
- The template entry (e.g., `run.sh`) is executed on your system.

## Practical guidelines
- Trust: activate only stores you trust; pin by tag/commit for shared environments.
- Review: skim `template_config.yaml`, `run.sh.j2`, and any `hooks/` or `resolvers/` before first use.
- Least privilege: run in directories you control; avoid scripts that `rm -rf` outside the run folder.
- Isolation: activate modules/conda/containers in hooks for tool isolation, especially for third‑party templates.
- Secrets: never hard‑code secrets into templates; pass via env vars or secret managers.

## How BPM imports BRS code
- BPM temporarily adds the active BRS root to `sys.path`, purges old modules, and imports the requested `module:function`.
- This ensures hooks/resolvers come from the current store you activated.

## Checklist for new templates
- Read the entry script and hooks for any destructive commands.
- Confirm params and defaults make sense; no credential prompts.
- Ensure `render.into` does not escape the project/out directory.
