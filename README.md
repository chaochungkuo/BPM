# BPM - Bioinformatics Project Manager

A flexible, template-driven CLI tool for managing genomic projects. BPM helps you organize and manage your genomic analysis workflows with a consistent project structure and template-based approach.

## Features

- Project initialization with standardized structure
- Template-based workflow management
- Support for demultiplexing, processing, and analysis workflows
- Project configuration management
- Command history tracking

## Installation

### From PyPI

```bash
pip install bpm
```

### From Source

1. Clone the repository:
```bash
git clone https://github.com/ckuo/bpm.git
cd bpm
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

## Usage

### Initialize a New Project

```bash
bpm init --name 250704_ProjectA_ProjectB_MedI_3mRNAseq \
         --date 250704 \
         --institute MedI \
         --application 3mRNAseq \
         --authors "Chao-Chung Kuo <ckuo@ukaachen.de>" \
         --project-dir "nextgen2:/data/projects/250704_ProjectA_ProjectB_MedI_3mRNAseq"
```

### Generate Workflow from Template

```bash
bpm generate bclconvert --raw nextgen:/novaseq/250704_A01742_0410_AHC3FFDRX5 \
                       --outdir nextgen:/data/fastq/250704
```

### Update Project Configuration

```bash
bpm update demultiplexing.bclconvert.raw_data_path "nextgen:/novaseq/new_data"
```

## Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
# Format code
black .
isort .

# Type checking
mypy .

# Linting
ruff check .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 