---
title: bpm template
parent: CLI
nav_order: 3
has_toc: true
---

# bpm template

Render, run, and publish templates from the active BRS.

```
# Render (project mode)
cd 250903_TEST
bpm template render --param "bcl_dir=/data/BCL" demux_bclconvert

# Run entry
bpm template run demux_bclconvert

# Publish resolvers (e.g., FASTQ_dir, multiqc_report)
bpm template publish demux_bclconvert
```
