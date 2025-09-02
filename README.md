🔬 Bioinformatics Project Manager (BPM)

Bioinformatics research is diverse: every dataset has quirks, and labs juggle a mix of
scripts, pipelines, and frameworks. This flexibility is powerful, but it also creates
problems:
- Projects are hard to reproduce.
- Scripts get copied, modified, and lost.
- Sharing across people or facilities means reinventing the same work.

BPM (Bioinformatics Project Manager) was created to solve this gap.

✅ What BPM is

BPM is a lightweight, Python-based command-line tool that provides a management layer for
bioinformatics projects. It brings order and reusability without forcing you into a single
framework.

At its core:
- BPM = the engine (stable CLI for project and template management).
- BRS = Bioinformatics Resource Store (repositories of templates, workflows, hooks, and
  resolvers customized for your facility or personal work).

🚫 What BPM is not
- BPM is not a workflow execution engine (like Nextflow, Snakemake, or Cromwell). It
  doesn’t replace them — it wraps and organizes them.
- BPM is not a LIMS (Laboratory Information Management System). It doesn’t manage samples,
  sequencing machines, or lab metadata — it focuses on the analysis side.
- BPM is not a central registry or cloud service. All state lives in plain files
  (project.yaml, stores.yaml) in your projects and cache, under your full control.

Instead, BPM complements these tools:
- You can use BPM to organize projects, then call Nextflow/Snakemake inside BPM templates.
- You can keep your facility-specific environments, scripts, and settings in a BRS and
  reuse them across projects.
- You can still log everything into a LIMS or database if you want — BPM just keeps your
  analysis side reproducible and portable.

Why it’s useful
- Reusability: Templates can be shared and rerun across datasets with one command.
- Consistency: Project naming policies and status tracking make archiving and collaboration
  easier.
- Flexibility: Each group or user can keep their own BRS — no central server required.
- Transparency: Everything is stored in YAML; version control works out of the box.
- Lifecycle management: Track project and template states automatically.
- Hooks & resolvers: Automate environment-specific paths and post-processing steps.
- Ad-hoc mode: Run templates outside BPM projects when you just need scripts.

✨ In short: BPM doesn’t replace your workflow engine, pipelines, or LIMS. Instead, it sits
one layer above them, helping you organize, reuse, and share your bioinformatics projects in
a clean and reproducible way.

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

## Shell completion

Enable shell completion for the `bpm` command.

- Zsh: `echo 'eval "$( _BPM_COMPLETE=zsh_source bpm )"' >> ~/.zshrc && exec zsh`
- Bash: `echo 'eval "$( _BPM_COMPLETE=bash_source bpm )"' >> ~/.bashrc && exec bash`
- Fish: `echo 'eval (env _BPM_COMPLETE=fish_source bpm)' >> ~/.config/fish/config.fish && exec fish`

Or use Typer helper once completion is enabled: `bpm --install-completion`.

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
