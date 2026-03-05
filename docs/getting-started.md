---
title: Getting Started
nav_order: 2
has_toc: true
---

# Getting Started

This guide walks through installing BPM, creating a project, adding a BRS, and rendering/running a template.

## Install

See Installation for pip, Pixi, or Conda instructions. For a quick start:

```
python -m pip install bpm-cli
# or, from source:
python -m pip install -e .
```

## Create a Project

```
bpm project init 250903_TEST --outdir "/abs/path"
```

## Add and Activate a BRS

```
bpm resource add ./UKA_GF_BRS --activate
bpm resource list
```

## Render, Run, Publish

```
cd 250903_TEST
bpm template render demux_bclconvert --param "bcl_dir=/data/BCL"
bpm template run demux_bclconvert
bpm template publish demux_bclconvert
```

## (Optional) Start BPM Agent

```bash
bpm agent config
bpm agent doctor
bpm agent start --goal "help me choose the right template"
```

See Concepts for key ideas and CLI for command help.
