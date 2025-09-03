---
title: Templates & Rendering
parent: Concepts
nav_order: 2
render_with_liquid: false
---

# Templates & Rendering

- Templates live in a BRS and declare parameters and render rules in `template_config.yaml`.
- `render.into` controls the output directory (supports `${ctx.project.name}` and `${ctx.template.id}` placeholders).
- Parameter precedence: defaults < project-stored < CLI `--param`.
- Jinja rendering is strict: missing variables error; reference the context explicitly.

Examples:
{% raw %}
```
${ctx.project.name}/${ctx.template.id}/
```

```
{{ ctx.params.name }}
```
{% endraw %}

Project vs Ad‑hoc:
- Project mode: base is `ctx.project_dir`.
- Ad‑hoc mode: base is `--out` (render.into is treated as `.`).
