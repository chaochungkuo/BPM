---
title: Adopt Ad‑hoc Runs
parent: How‑to
nav_order: 15
---

# Adopt Ad‑hoc Runs

You can render/run/publish a template in ad‑hoc mode (no project) and later adopt the results into a project.

## Ad‑hoc lifecycle
- Render: `bpm template render --out /adhoc demux_bclconvert` (or `--adhoc` if the template provides `render.adhoc_out_resolver`)
- Run:    `cd /adhoc && bpm template run demux_bclconvert`
- Publish:`cd /adhoc && bpm template publish demux_bclconvert`

This writes `/adhoc/bpm.meta.yaml` with:

```
source:
  brs_id: UKA_GF_BRS
  brs_version: 0.1.1
  template_id: demux_bclconvert
params:
  bcl_dir: /path/to/run
status: completed
published:
  FASTQ_dir: host:/abs/path/to/FASTQs
  multiqc_report: host:/abs/path/to/multiqc/multiqc_report.html
```

## Adopt into an existing project
```
bpm project adopt --dir /projects/MyProj --from /adhoc1 --from /adhoc2
```

Behavior:
- Inserts a template entry for each ad‑hoc folder.
- Collision policy (per template id): `--on-exists skip|merge|overwrite` (default: merge).
- Paths are left as‑is; resolvers usually produce host‑aware paths.

## Create a new project and adopt
```
bpm project init MyProj --outdir /projects --adopt /adhoc
```

This creates the project and immediately adopts the ad‑hoc run.

## Notes
- Adoption preserves `params`, `published`, and `status`.
- The template entry also records the ad‑hoc `source` (BRS id/version, template id).
- If needed, you can re‑run `bpm template publish` in project mode to recompute publish values.
