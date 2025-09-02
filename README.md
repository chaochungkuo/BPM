# BPM

Minimal, test-driven skeleton for a Bio Project Manager (BPM) CLI. Implements
project scaffolding, template rendering/running/publish, resource stores, and
workflows. Everything is covered by CLI/unit tests and runnable via Pixi.

## Quickstart

```bash
pixi install
pixi run test   # run all tests
pixi run lint   # ruff
pixi run fmt    # black
```

## CLI overview

- `bpm resource …`: manage BRS stores (add/activate/remove/list/info)
- `bpm project …`: init/info/status for a project directory
- `bpm template …`: render/run/publish templates from the active BRS
- `bpm workflow …`: render/run workflows from the active BRS

### Resource

```bash
# add a local BRS and activate it
bpm resource add /path/to/brs --activate

# list stores (active marked with *)
bpm resource list

# switch active
bpm resource activate <id>
```

### Project

```bash
# create a new project (policy enforced by active BRS)
bpm project init 250901_Demo_UKA \
  --project-path nextgen:/projects/250901_Demo_UKA \
  --cwd /tmp

# inspect
bpm project info --dir /tmp/250901_Demo_UKA
bpm project status --dir /tmp/250901_Demo_UKA
```

### Template

```bash
# render into project with params
bpm template render hello --dir /tmp/250901_Demo_UKA --param name=Alice

# run (executes run.sh in the rendered folder, with hooks)
bpm template run hello --dir /tmp/250901_Demo_UKA

# publish (runs resolvers and persists to project.yaml)
bpm template publish hello --dir /tmp/250901_Demo_UKA

# ad‑hoc render (no project.yaml changes); writes bpm.meta.yaml in output
bpm template render hello --out /tmp/adhoc_out --param name=Alice
```

### Workflow

Workflows mirror templates but do not touch `project.yaml`.

```bash
# render a workflow into the project
bpm workflow render clean --dir /tmp/250901_Demo_UKA --param name=Alice

# run the workflow entry script
bpm workflow run clean --dir /tmp/250901_Demo_UKA
```

See example skeleton under `tests/data/brs_min` and `tests/cli/test_workflow_run.py`.
