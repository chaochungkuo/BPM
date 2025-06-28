# BPM (Bioinformatics Project Manager)

[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue?style=flat-square&logo=github)](https://chaochungkuo.github.io/BPM/)
[![PyPI](https://img.shields.io/pypi/v/bpm?style=flat-square)](https://pypi.org/project/bpm/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python)](https://www.python.org/)

A flexible, template-driven CLI tool for managing bioinformatics projects with standardized workflows and reproducible research practices.

## ✨ Features

- **Project Management**: Create and manage bioinformatics projects with standardized naming
- **Template System**: Generate project files from customizable templates
- **Workflow Execution**: Run predefined bioinformatics workflows
- **Repository Management**: Manage template and workflow repositories
- **Cross-platform**: Works on Linux, macOS, and Windows

## 🚀 Quick Start

### Installation

```bash
pip install bpm
```

### Setup

Set up your cache directory (add to your shell configuration):

```bash
export BPM_CACHE="/path/to/bpm_cache"
```

### Basic Usage

```bash
# Initialize a new project
bpm init 240101_RNAseq_Study_Institute_Research

# Add a repository with templates
bpm repo add https://github.com/IZKF-Genomics/BPM_repo

# Generate files from a template
bpm generate nfcore:rnaseq --project project.yaml

# Run a workflow
bpm run workflows:generate_samplesheet --project project.yaml
```

## 📚 Documentation

For comprehensive documentation, tutorials, and examples, visit:

**📖 [BPM Documentation](https://chaochungkuo.github.io/BPM/)**

The documentation includes:
- [Installation Guide](https://chaochungkuo.github.io/BPM/getting-started/installation/)
- [Quick Start Tutorial](https://chaochungkuo.github.io/BPM/getting-started/quick-start/)
- [User Guide](https://chaochungkuo.github.io/BPM/user-guide/projects/)
- [CLI Reference](https://chaochungkuo.github.io/BPM/user-guide/cli-reference/)
- [Examples](https://chaochungkuo.github.io/BPM/examples/bioinformatics/rnaseq-pipeline/)
- [FAQ](https://chaochungkuo.github.io/BPM/troubleshooting/faq/)

## 🎯 Use Cases

BPM is designed for bioinformatics professionals who need to:

- **Standardize project structure** across multiple research projects
- **Automate repetitive tasks** in bioinformatics workflows
- **Share templates and workflows** within research teams
- **Ensure reproducibility** in bioinformatics research
- **Manage complex pipeline configurations** efficiently

## 🔧 Requirements

- Python 3.10 or higher
- pip (Python package installer)
- Git (for repository management)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://chaochungkuo.github.io/BPM/developer-guide/contributing/) for details.

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [GitHub Repository](https://github.com/chaochungkuo/BPM)
- [PyPI Package](https://pypi.org/project/bpm/)
- [Issues](https://github.com/chaochungkuo/BPM/issues)
- [Releases](https://github.com/chaochungkuo/BPM/releases)
