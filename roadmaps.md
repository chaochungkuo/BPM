Awesome — here’s a tight, step-by-step development & testing roadmap to build BPM from scratch and keep everything green the whole way. It’s sequenced so each milestone is shippable and covered by unit/CLI tests.

⸻

0) Bootstrap (Day 0)

Create repo + scaffolding
	•	Files: pyproject.toml, bpm/__init__.py, tests/conftest.py, .gitignore, .github/workflows/ci.yml
	•	Dev deps: pytest, pytest-cov, typer, jinja2, pyyaml, rich (optional), ruff, black
	•	CI: run pytest -q on 3.10–3.12

Tests: a single assert True smoke test to verify CI.

⸻

1) Models & IO primitives (Day 1)

Implement
	•	bpm/models/hostpath.py — normalize/write as host:/abs, materialize to local path via hosts.yaml
	•	bpm/models/store_index.py — schema for $BPM_CACHE/stores.yaml (lean version you defined)
	•	bpm/models/project.py — Project, TemplateEntry, enums (initiated|active|closed, active|completed)
	•	bpm/io/yamlio.py — safe_load_yaml, safe_dump_yaml (atomic)
	•	bpm/utils/time.py, bpm/utils/errors.py

Tests
	•	tests/unit/test_hostpath.py: normalize/materialize w/ your hosts.yaml
	•	tests/unit/test_yamlio.py: roundtrip + atomic write
	•	tests/unit/test_models_project.py: minimal schema load/save

Exit criteria: serialize/deserialize models cleanly; coverage ≥85% for these modules.

⸻

2) Environment & Store registry (Day 2)

Implement
	•	bpm/core/env.py — resolve $BPM_CACHE, ensure dirs exist
	•	bpm/core/store_registry.py — read/modify $BPM_CACHE/stores.yaml (add/activate/remove/update/list/info) with file lock + atomic writes

Tests
	•	tests/unit/test_store_registry.py: init empty registry; add a store; activate; remove; update timestamps

Exit criteria: stores.yaml reflects mutations exactly; no disk races in tests.

⸻

3) BRS loader & minimal fixture (Day 2–3)

Create test fixture BRS under tests/data/brs_min/:
	•	repo.yaml (lean)
	•	config/authors.yaml, config/hosts.yaml, config/settings.yaml
	•	templates/hello/{template.config.yaml, run.sh.j2}
	•	hooks/__init__.py, resolvers/__init__.py

Implement
	•	bpm/core/brs_loader.py — return active BRS path; load repo.yaml + config/*; expose template/workflow roots

Tests
	•	tests/unit/test_brs_loader.py: add BRS to cache via registry; activate; load config paths

Exit criteria: active BRS path resolves; config files parsed.

⸻

4) Descriptor loader & param resolution (Day 3–4)

Implement
	•	bpm/core/descriptor_loader.py — read templates/<id>/template.config.yaml → TemplateDescriptor (pydantic)
	•	bpm/core/param_resolver.py — precedence: CLI > stored > param_refs > defaults; interpolation ${ctx…} support
	•	bpm/core/context.py — build ctx (project, template, params; helpers: hostname(), materialize(), now())

Tests
	•	tests/unit/test_descriptor_loader.py: valid/invalid descriptor; required fields erroring nicely
	•	tests/unit/test_param_precedence.py: assert precedence + ${ctx…} expansion
	•	tests/unit/test_context_paths.py: ctx.materialize with your hosts.yaml

Exit criteria: can compute final params deterministically.

⸻

5) Renderer (Day 4)

Implement
	•	bpm/core/jinja_renderer.py — flat rule: render all *.j2 at template root (strip extension), copy others; set +x on run.sh; --dry returns plan

Tests
	•	tests/unit/test_renderer.py: render hello; verify file contents; --dry shows planned files

Exit criteria: files appear exactly as expected in a temp folder.

⸻

6) Project I/O & CLI: project init/status (Day 5)

Implement
	•	bpm/core/project_io.py — load/save project.yaml (HostPath normalize on save)
	•	bpm/core/project_service.py — init, status, info, close (auto state transitions)
	•	bpm/cli/project.py — Typer commands

Tests
	•	tests/cli/test_project_init.py: with fixture BRS, --author ckuo,lgan expands from authors.yaml; name regex enforced from settings.yaml
	•	tests/cli/test_project_status.py: shows table with initiated state

Exit criteria: can create a project dir with a valid project.yaml and view status.

⸻

7) Hooks & Publish resolvers (Day 6)

Implement
	•	bpm/core/hooks_runner.py — import hooks.module.func from active BRS; run post_render, pre_run, post_run
	•	bpm/core/publish_resolver.py — import resolvers.module.main(ctx); ensure return is YAML-serializable; write to project.yaml

Tests
	•	tests/unit/test_hooks_runner.py: run a demo hook writing a file; error bubbles up cleanly
	•	tests/unit/test_publish_resolver.py: resolver returns string → appears under published: with HostPath normalization

Exit criteria: lifecycle hooks run; publish updates persisted.

⸻

8) Template service & CLI (render/run/publish) (Day 7–8)

Implement
	•	bpm/core/template_service.py
	•	render(template_id, cli_params, dry=False):
	•	dependency check (from descriptor)
	•	param resolution
	•	render
	•	post_render hooks
	•	optional publish
	•	update template entry (status → active, record source, brs_commit)
	•	project state → active
	•	run(template_id): execute run.sh via io.exec.run_process; pre_run/post_run; on success → publish; mark template completed
	•	publish(template_id): run publish resolvers only
	•	bpm/cli/template.py — Typer commands

Tests
	•	tests/cli/test_template_render.py: render hello, assert files exist, template recorded in project.yaml
	•	tests/cli/test_template_run.py: run, hook writes a file, publish value appears, status transitions ok
	•	tests/cli/test_template_publish.py: publish only path produces expected published fields

Exit criteria: full loop works for the minimal hello template.

⸻

9) Resource commands (Day 9)

Implement
	•	bpm/cli/resource.py — add|activate|remove|update|list|info mapped to store_registry

Tests
	•	tests/cli/test_resource_cli.py: add local fixture BRS; list shows active *; info reads repo.yaml; remove clears entry

Exit criteria: can manage multiple BRS caches; one active at a time.

⸻

10) Ad-hoc mode (optional MVP+) (Day 10)

Implement
	•	Extend template_service.render(..., adhoc_out=None):
	•	If --out provided: do not touch project.yaml
	•	Disable deps/param_refs/resolvers/hooks (per your rule)
	•	Write bpm.meta.yaml in the ad-hoc output folder (params + source)

Tests
	•	tests/cli/test_template_render_adhoc.py: render to --out; ensure no project change; files written; meta present

Exit criteria: ad-hoc works without project context.

⸻

11) UX polish & status table (Day 11)

Implement
	•	bpm/utils/table.py — small helper for bpm project status output
	•	Improve error messages with actionable hints

Tests
	•	Snapshot-style tests for status output (assert key lines/columns present)

Exit criteria: human-friendly CLI output.

⸻

12) Workflows (optional later)

Implement
	•	bpm/core/workflow_service.py + bpm/cli/workflow.py
	•	Parse workflows/<id>/workflow.yaml (similar to template but no publish), render/run with ctx

Tests
	•	tests/cli/test_workflow_run.py: run clean/archive on a temp project

⸻

Recurring practices
	•	TDD for each module: write failing tests first.
	•	Ruff/Black pre-commit: keep diffs small/clean.
	•	Coverage gate: keep ≥85% (exclude CLI Typer glue if needed).
	•	Golden tests: for rendered outputs (run.sh content).
	•	Fast CI: avoid network; use local fixture BRS.

⸻

Daily build checklist (for each milestone)
	1.	Update TODO in README for the milestone.
	2.	Write/extend tests.
	3.	Implement minimal code to pass.
	4.	Run pytest -q locally.
	5.	Push → CI green.
	6.	Tag milestone (optional) and jot down acceptance notes.

⸻

If you want, I can generate the exact pyproject.toml and the first test fixture BRS folder (tests/data/brs_min) so you can start with step 1 immediately.