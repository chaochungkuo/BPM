---
title: Parameters & Precedence
parent: Concepts
nav_order: 4
has_toc: true
---

# Parameters & Precedence

Simple rule: define sensible defaults in the template, store what you ran in the project, and override with the CLI when needed.

## Sources and Precedence
Lowest to highest (last one wins):
- Descriptor defaults: `params:` in `template_config.yaml`.
- Project‑stored values: saved in `project.yaml` after a render.
- CLI overrides: `--param KEY=VALUE` on `render`/`run`.

If a required param has no value after merging, BPM errors out with “Missing required parameters: …”.

## Declaring Params (template_config.yaml)
```
id: hello
params:
  sample_id:        {type: str,  required: true}
  threads:          {type: int,  default: 8}
  skip_qc:          {type: bool, default: false}
  input_dir:        {type: str,  default: "${ctx.project.name}/inputs"}
render:
  into: "${ctx.project.name}/${ctx.template.id}/"
  files:
    - run.sh.j2 -> run.sh
run:
  entry: run.sh
```

Notes:
- Types supported: `str`, `int`, `float`, `bool` (CLI strings are coerced to these types).
- `${ctx.*}` in defaults: safe to use with `ctx.project.*` and `ctx.template.*`. Avoid referencing `ctx.params.*` inside defaults.
- Path validation (optional): add `exists: file|dir|any` on a param to make BPM check the given path exists before rendering. Example:
  `input_dir: { type: str, required: true, exists: dir }`
- Descriptions (optional): add `description: "..."` to a param; shown by `bpm template info`.

## CLI Overrides (–param)
- Format: `--param KEY=VALUE` (repeatable). No spaces around `=`.
- Booleans: `true/false`, `1/0`, `yes/no`, `on/off` are accepted.

Examples
```
# Start with defaults → threads=8
bpm template render hello

# Override for this invocation
bpm template render --param threads=16 hello

# Multiple params
bpm template render --param sample_id=NA12878 --param input_dir=/data/in hello
```

## How Values Are Stored
- Project mode: after a successful render, BPM writes final params to `project.yaml` under this template’s entry. Subsequent runs reuse them unless you override with `--param`.
- Ad‑hoc mode (`--out`): BPM does not modify `project.yaml`; it writes `bpm.meta.yaml` in the output folder with the params used.

## Using Params in Templates
Inside Jinja files, access with `{{ ctx.params.KEY }}`:
```
# run.sh.j2
#!/usr/bin/env bash
set -euo pipefail
echo "Sample: {{ ctx.params.sample_id }}"
toolX --threads {{ ctx.params.threads }} --in "{{ ctx.params.input_dir }}"
```

## Minimal Precedence Walkthrough
1) Defaults in descriptor: `threads=8`.
2) You render and later edit project params (or re‑render with overrides): `project.yaml` now stores `threads=12`.
3) You render again with CLI: `--param threads=20` → final value is 20 for this invocation; project keeps the stored value after render.

## Best Practices
- Mark only truly required params as `required: true`.
- Provide conservative defaults when possible.
- Keep names simple (`[a-z0-9_]+`) and document meaning in the template README.
- Avoid putting secrets in params; pass via environment or secrets managers instead.
