---
title: Interop with Workflow Engines
parent: Concepts
nav_order: 17
has_toc: true
---

# Interop with Workflow Engines

BPM doesn’t replace your engine (Nextflow, Snakemake, CWL, plain Bash). It surrounds it with a consistent project context and parameter system so you don’t hand‑edit configs for each run.

## What BPM Provides
- Single source of truth: `ctx.params` holds all inputs, with precedence (defaults → project → CLI).
- Stable paths: `render.into` resolves with `${ctx.project.name}/${ctx.template.id}/` so outputs land in predictable folders.
- Reusable renders: Jinja templates generate engine config/CLI exactly for the current context.
- Publication: resolvers turn engine outputs into named keys stored in `project.yaml`.

## Patterns by Engine

1) Nextflow
- Render `nextflow.config` and/or a launcher script from Jinja, then execute with `run.sh`.
```
# template file: nextflow.config.j2
params.sample_id = '{{ ctx.params.sample_id }}'
params.input     = '{{ ctx.params.input }}'
profiles         = '{{ ctx.params.profile | default("standard") }}'
```

```
# template file: run.sh.j2
#!/usr/bin/env bash
set -euo pipefail
nextflow run main.nf -c nextflow.config -with-report report.html -with-trace
```

2) Snakemake
- Render `config.yaml` (or `--config`) and call Snakemake from `run.sh`.
```
# template file: config.yaml.j2
sample_id: {{ ctx.params.sample_id }}
input: {{ ctx.params.input | tojson }}
threads: {{ ctx.params.threads | default(8) }}
```

```
# template file: run.sh.j2
#!/usr/bin/env bash
set -euo pipefail
snakemake --cores {{ ctx.params.threads | default(8) }} \
          --configfile config.yaml \
          --use-conda --printshellcmds
```

3) CWL (cwltool)
- Render an inputs file then run:
```
# inputs.yml.j2
sample_id: {{ ctx.params.sample_id }}
reads: {{ ctx.params.reads | tojson }}
```

```
# run.sh.j2
#!/usr/bin/env bash
set -euo pipefail
cwltool workflow.cwl inputs.yml
```

4) Plain Bash/Tools
- Use `ctx.params` directly in scripts without editing them later:
```
# run.sh.j2
#!/usr/bin/env bash
set -euo pipefail
toolX --input "{{ ctx.params.input }}" --out out/ --threads {{ ctx.params.threads | default(4) }}
```

## Publishing Engine Outputs
- Add publish resolvers in `template_config.yaml` to expose key artifacts.
```
publish:
  fastq_dir:
    resolver: resolvers.fastq_dir:main
  multiqc_report:
    resolver: resolvers.reports:find
    args:
      pattern: "**/multiqc_report.html"
```
- After `bpm template publish <id>`, BPM writes these keys to `project.yaml` so other steps can find them.

## Why This Avoids Manual Param Changes
- Centralized params: Set values once with `--param` or in `project.yaml`. Templates read `{{ ctx.params.* }}` so you never edit engine configs by hand.
- Consistent paths: `render.into` anchors outputs; scripts don’t need hard‑coded directories.
- Mode‑aware: Project vs ad‑hoc behavior is handled by BPM; templates stay the same.
- Reproducible state: `project.yaml` records params and published outputs used for each run.

## Minimal End‑to‑End Example (Nextflow)
```
# template_config.yaml (excerpt)
id: nf_align
params:
  reads: []
  ref: ""
render:
  into: "${ctx.project.name}/${ctx.template.id}/"
  files:
    - nextflow.config.j2 -> nextflow.config
    - run.sh.j2 -> run.sh
run:
  entry: run.sh
publish:
  bam_dir:
    resolver: resolvers.paths:dir
    args: { path: "results/bam" }
```

CLI
```
bpm template render --param "reads=['R1.fastq','R2.fastq']" --param ref=/data/ref.fa nf_align
bpm template run nf_align
bpm template publish nf_align
```

No manual edits: the render step materializes the right config and command using `ctx.params` and project context.
