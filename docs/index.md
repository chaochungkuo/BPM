---
title: Home
nav_order: 1
---

# BPM

Bioinformatics Project Manager (BPM) — a lightweight CLI to organize, render, run, and publish analysis templates from Bioinformatics Resource Stores (BRS).

## Quickstart

```
# Install (editable for local dev)
pip install -e .[dev]

# Initialize a project
bpm project init 250903_TEST --path "/abs/path/250903_TEST"

# Add and activate a BRS (local path)
bpm resource add ./UKA_GF_BRS --activate

# Render → Run → Publish a template
cd 250903_TEST
bpm template render --param "bcl_dir=/data/BCL" demux_bclconvert
bpm template run demux_bclconvert
bpm template publish demux_bclconvert
```

## What BPM Is (and Isn’t)

- BPM manages projects, templates, and stores; it does not replace workflow engines.
- Works alongside Nextflow/Snakemake; keeps state in plain files (project.yaml, stores.yaml).

Continue with Getting Started to learn the basics.

