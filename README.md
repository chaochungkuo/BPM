<h1 align="center">🔬 Bioinformatics Project Manager (BPM)</h1>

Bioinformatics research is diverse: every dataset has quirks, and labs juggle a mix of
scripts, pipelines, and frameworks. This flexibility is powerful, but it also creates
problems:

- Projects are hard to reproduce.
- Scripts get copied, modified, and lost.
- Sharing across people or facilities means reinventing the same work.

BPM (Bioinformatics Project Manager) was created to solve this gap.

## ✅ What BPM Is

BPM is a lightweight, Python-based command-line tool that provides a management layer for
bioinformatics projects. It brings order and reusability without forcing you into a single
framework.

At its core:

- BPM = the engine (stable CLI for project and template management).
- BRS = Bioinformatics Resource Store (repositories of templates, workflows, hooks, and
  resolvers customized for your facility or personal work).

## 🚫 What BPM Is Not

- Not a workflow engine (Nextflow, Snakemake, Cromwell). It doesn’t replace them — it wraps
  and organizes them.
- Not a LIMS. It doesn’t manage samples, machines, or lab metadata — it focuses on analysis.
- Not a cloud service or central registry. State lives in plain files (project.yaml,
  stores.yaml) under your control.

Instead, BPM complements these tools:

- Organize projects with BPM, then run Nextflow/Snakemake inside BPM templates.
- Keep facility-specific environments, scripts, and settings in a BRS for reuse.
- Still log into a LIMS or DB if you want — BPM keeps the analysis side reproducible.

### Why It’s Useful

- Reusability: Share and rerun templates across datasets with one command.
- Consistency: Naming policy and status tracking simplify archiving and collaboration.
- Flexibility: Each group can maintain its own BRS — no central server required.
- Transparency: Everything in YAML; works with version control by default.
- Lifecycle management: Track project and template states automatically.
- Hooks & resolvers: Automate environment-specific paths and post-processing.
- Ad‑hoc mode: Run templates outside BPM projects when you just need scripts.

> In short: BPM doesn’t replace your workflow engine, pipelines, or LIMS. It sits one layer
> above them, helping you organize, reuse, and share your bioinformatics projects in a clean
> and reproducible way.

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

---

## Concepts

### Bioinformatics Resource Store (BRS)

A BRS is a folder containing the reusable building blocks for your org or personal work:

- `config/` — authors, hosts, and settings (e.g., project name policy)
- `templates/` — reusable analysis blueprints
- `workflows/` — higher-level wrappers similar to templates
- `hooks/` — Python hook functions (pre/post render/run)
- `resolvers/` — publish resolvers to compute structured outputs

See the minimal example in `tests/data/brs_min/`.

### Templates

Each template lives in `templates/<id>/` and is described by `template.config.yaml`.

Key fields:

- `id`: Template id (must match folder name).
- `params`: Map of parameters (type, required, default, optional `cli` alias).
- `render.into`: Where to render (supports `${ctx.*}` placeholders).
- `render.files`: List of mappings (e.g., `a.j2 -> a`) — `*.j2` renders with Jinja2, others copied.
- `run.entry`: Optional script to execute (e.g., `run.sh`); BPM marks it executable.
- `required_templates`: Dependencies that must already exist in the project.
- `publish`: Resolvers to compute structured values after run.
- `hooks`: `post_render`, `pre_run`, `post_run` lists of dotted hook functions.

Parameter precedence when rendering:

1) descriptor defaults < 2) project‑stored values < 3) CLI `--param` overrides

Jinja has access to a rich context via `ctx` (see Context System below).

### Workflows

Workflows mirror templates but live under `workflows/<id>/` with `workflow.yaml`. They use the
same rendering rules and `${ctx…}` placeholders, but they don’t touch `project.yaml` (no publish
or template status tracking). They are useful for one‑off utilities and glue tasks.

---

## Modes: Project vs Ad‑hoc

### Project Mode (with Context System)

Create a project directory and a `project.yaml` with:

- `name`, `created`, `project_path` (host‑aware string like `nextgen:/projects/NAME`)
- `authors` (expanded from `config/authors.yaml`)
- `status` (initiated → active, etc.)
- `templates` (list of rendered templates, params, and statuses)

The context object `ctx` passed to templates/hooks/resolvers contains:

- `ctx.project`: `{ name, project_path }`
- `ctx.template`: `{ id, published }`
- `ctx.params`: final resolved params
- `ctx.brs`: `{ repo, authors, hosts, settings }`
- `ctx.cwd`: Path used as the base for rendering/running
- Helpers: `ctx.hostname()`, `ctx.materialize(hostpath)`, `ctx.now()`

Project‑mode rendering updates `project.yaml` and sets:

- template entry: status → `active`, params → final
- project status: `active`

Running a template marks it `completed`. Publish persists resolver outputs.

CLI parameters (project mode):

```bash
# Create a project (policy enforced by active BRS settings)
bpm project init <project_name> \
  --project-path <host:path> \
  [--author <id1,id2>] \
  [--cwd <dir>]

# Inspect
bpm project info   --dir <project_dir>
bpm project status --dir <project_dir>

# Render / run / publish
bpm template render  <template_id> --dir <project_dir> [--param KEY=VALUE] [--dry]
bpm template run     <template_id> --dir <project_dir>
bpm template publish <template_id> --dir <project_dir>
```

### Ad‑hoc Mode (no project.yaml)

Render a template directly to an output folder without changing a project:

- Skips dependency checks and hooks
- Does not read or write `project.yaml`
- Overrides `render.into` to `.` so files materialize under the output folder
- Writes `bpm.meta.yaml` with source metadata and final params

CLI parameters (ad‑hoc):

```bash
bpm template render <template_id> \
  --out <output_dir> \
  [--param KEY=VALUE] \
  [--dry]
```

## Shell completion

Enable shell completion for the `bpm` command.

- Zsh: `echo 'eval "$( _BPM_COMPLETE=zsh_source bpm )"' >> ~/.zshrc && exec zsh`
- Bash: `echo 'eval "$( _BPM_COMPLETE=bash_source bpm )"' >> ~/.bashrc && exec bash`
- Fish: `echo 'eval (env _BPM_COMPLETE=fish_source bpm)' >> ~/.config/fish/config.fish && exec fish`

Or use Typer helper once completion is enabled: `bpm --install-completion`.

---

## Installation

Using Pixi (recommended for development / tests):

```bash
pixi install
pixi run test   # run tests
pixi run lint   # ruff
pixi run fmt    # black
```

Editable install with pip:

```bash
python -m pip install -e .[dev]
pytest -q
```

---

## Links

- Roadmap: `roadmaps.md`
- Structure & design notes: `structure.md`

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
  --outdir /tmp \
  [--author ckuo,lgan] \
  [--host nextgen]

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
