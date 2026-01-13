---
title: Installation
nav_order: 2
has_toc: true
---

# Installation

BPM supports multiple setup paths. Choose one that fits your workflow.

## Pip

- User install (latest published):
  ```bash
  python -m pip install bpm-cli
  ```

- From source (editable) while hacking on BPM:
  ```bash
  git clone https://github.com/your-org/BPM.git
  cd BPM
  python -m pip install -e .
  ```

## Pixi (recommended for development)

```bash
pixi install           # create env with runtime deps
pixi run python -m pip install bpm-cli
pixi run test          # run tests
pixi run lint          # ruff
pixi run fmt           # black
```

## Conda/Mamba

- Quick environment with runtime deps:
  ```bash
  mamba create -n bpm -c conda-forge python>=3.10 typer jinja2 pyyaml rich
  mamba activate bpm
  ```

- Or use the provided file:
  ```bash
  mamba env create -f environment.yml
  conda activate bpm
  ```

Then install BPM itself (from PyPI or local source):
```bash
python -m pip install bpm-cli   # from PyPI
# or
python -m pip install -e .      # from source checkout
```

## Notes

- Python 3.10 or newer is required.
- `rich` enhances table output; if absent, BPM falls back to plain text.
- For isolated CLI installs, `pipx install bpm-cli` also works (command is still `bpm`).
