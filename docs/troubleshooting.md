---
title: Troubleshooting
nav_order: 9
render_with_liquid: false
---

# Troubleshooting

## Jinja Errors (e.g., Missing end of comment tag)
- Check for unclosed `{# ... #}` or mismatched `{% %}`.
- Renderer now surfaces file:line to locate issues.

## Missing Tools
- Ensure required tools (e.g., bcl-convert, fastqc, multiqc) are on PATH.

## Cache/Store Issues
- `bpm resource list` to verify active store
- `bpm resource update --id <id> --force` to refresh
