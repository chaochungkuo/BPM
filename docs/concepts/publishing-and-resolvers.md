---
title: Publishing & Resolvers
parent: Concepts
nav_order: 6
has_toc: true
---

# Publishing & Resolvers

Turn run outputs into stable, named artifacts that other steps can find.

## What “publish” is
- In `template_config.yaml`, `publish:` maps friendly keys to resolver functions.
- After `bpm template publish <id>`, BPM calls each resolver and stores results in `project.yaml`.

## Resolver spec (in the template)
```
publish:
  fastq_dir:
    resolver: resolvers.fastq:main
  multiqc_report:
    resolver: resolvers.reports:find
    args:
      pattern: "**/multiqc_report.html"
```
- Dotted path: `module` or `module:function`. Default function is `main`.
- Location: imported from the active BRS root (e.g., `resolvers/fastq.py`).
- Signature: `fn(ctx, **args)` and return a simple value (path, string, number, dict).

## What gets written
- `project.yaml` → `templates[].published[key] = value` for the current template id.
- Example snippet:
```
templates:
  - id: hello
    status: completed
    params: {sample_id: NA12878}
    published:
      fastq_dir: /abs/250903_TEST/hello/fastq
      multiqc_report: /abs/250903_TEST/hello/results/multiqc_report.html
```

## Good key names
- Use short, stable `snake_case`: `fastq_dir`, `bam_dir`, `vcf`, `multiqc_report`.
- Don’t embed semantics that might change (e.g., avoid `multiqc_report_v2`).

## Tips
- Keep resolver logic small and deterministic; avoid globbing huge trees when possible.
- If outputs are optional, have the resolver return `null` (None) and document it.
- Resolvers run after a successful `run`; they should not modify files, only read.
