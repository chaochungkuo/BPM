---
title: Getting Started
nav_order: 2
has_toc: true
---

# Getting Started

This guide walks through installing BPM, creating a project, adding a BRS, and rendering/running a template.

## Install

```
pip install -e .[dev]
```

## Create a Project

```
bpm project init 250903_TEST --path "/abs/path/250903_TEST"
```

## Add and Activate a BRS

```
bpm resource add ./UKA_GF_BRS --activate
bpm resource list
```

## Render, Run, Publish

```
cd 250903_TEST
bpm template render --param "bcl_dir=/data/BCL" demux_bclconvert
bpm template run demux_bclconvert
bpm template publish demux_bclconvert
```

See Concepts for key ideas and CLI for command help.
