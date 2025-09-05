---
title: Render and Run a Template
parent: How-To
nav_order: 3
has_toc: true
---

# Render and Run a Template

Project mode
```
cd /abs/path/250903_TEST
bpm template list
bpm template render --param sample_id=NA12878 hello
bpm template run hello
```

Publish outputs
```
bpm template publish hello
```

Notes
- Use `--param KEY=VALUE` to override descriptor defaults (repeatable).
- Missing required params cause render to fail early with a clear error.
- `run` executes the entry (default `run.sh`) in the rendered folder.

