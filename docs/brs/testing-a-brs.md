---
title: Testing a BRS
parent: BRS
nav_order: 8
has_toc: true
---

# Testing a BRS

Keep confidence high with a few fast checks.

## Smoke tests (example with pytest)
```
def test_hello_renders(tmp_path, monkeypatch):
    # Point BPM to a test cache with your BRS
    # monkeypatch.setenv("BPM_CACHE", str(tmp_path/".bpm_cache"))
    # ... add store and activate ...
    # Render dry-run to catch Jinja issues
    # Expect at least one planned render/copy step
    pass
```

## Golden files
- Render with fixed params and compare key outputs to fixtures (text reports, small configs).
- Avoid large binaries; verify presence or checksums only.

## CI
- Run smoke tests on push/PR; verify template ids and basic rendering still work.
- Optionally run `bpm template publish` to validate resolvers.

## Checklist
- Descriptors have matching `id` and folder name.
- `render.into` uses placeholders; no absolute paths by default.
- Params have sensible defaults and clear `required` flags.
- `run.entry` exists and renders; hooks/resolvers import cleanly.
