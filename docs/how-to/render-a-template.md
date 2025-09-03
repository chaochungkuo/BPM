---
title: Render a Template
parent: How-To
nav_order: 1
---

# Render a Template

## Project Mode

```
cd 250903_TEST
bpm template render --param "bcl_dir=/data/BCL" demux_bclconvert
```

## Ad‑hoc Mode

```
bpm template render --out /tmp/out --param "bcl_dir=/data/BCL" demux_bclconvert
```

In ad‑hoc mode, files are written directly to `--out`.

