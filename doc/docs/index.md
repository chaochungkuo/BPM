# BPM Documentation

Welcome to the **Bioinformatics Project Manager (BPM)** documentation! BPM is a flexible, template-driven CLI tool designed to streamline bioinformatics project management.

## 🚀 Quick Start

Get up and running with BPM in minutes:

```bash
# Install BPM
pip install bpm

# Set up cache directory
export BPM_CACHE="/path/to/bpm_cache"

# Initialize your first project
bpm init 230101_MyProject_Institute_Application

# Add a repository
bpm repo add /path/to/repository

# Generate files from a template
bpm generate template_name --project project.yaml
```

## ✨ Key Features

<div class="grid" markdown>

<div class="card" markdown>

### 🗂️ Project Management
Create and manage bioinformatics projects with standardized naming conventions. Keep your projects organized and consistent across your team.

[Learn more →](user-guide/projects.md)

</div>

<div class="card" markdown>

### 📋 Template System
Generate project files from customizable templates. Save time and ensure consistency across all your bioinformatics workflows.

[Learn more →](user-guide/templates.md)

</div>

<div class="card" markdown>

### ⚡ Workflow Execution
Run predefined bioinformatics workflows with ease. Execute complex pipelines with simple commands.

[Learn more →](user-guide/workflows.md)

</div>

<div class="card" markdown>

### 📚 Repository Management
Manage template and workflow repositories. Share and collaborate on templates across your organization.

[Learn more →](user-guide/repositories.md)

</div>

</div>

## 🎯 Use Cases

BPM is designed for bioinformatics professionals who need to:

- **Standardize project structure** across multiple research projects
- **Automate repetitive tasks** in bioinformatics workflows
- **Share templates and workflows** within research teams
- **Manage complex pipeline configurations** efficiently
- **Ensure reproducibility** in bioinformatics research

## 📖 Documentation Sections

<div class="grid" markdown>

<div class="card" markdown>

### Getting Started
New to BPM? Start here to learn the basics.

- [Installation](getting-started/installation.md)
- [Quick Start Guide](getting-started/quick-start.md)
- [Configuration](getting-started/configuration.md)

</div>

<div class="card" markdown>

### User Guide
Learn how to use BPM effectively in your daily workflow.

- [Project Management](user-guide/projects.md)
- [Working with Templates](user-guide/templates.md)
- [Running Workflows](user-guide/workflows.md)
- [CLI Reference](user-guide/cli-reference.md)

</div>

<div class="card" markdown>

### Admin Guide
For administrators and template creators.

- [Repository Setup](admin-guide/repository-setup.md)
- [Template Development](admin-guide/template-development.md)
- [Workflow Development](admin-guide/workflow-development.md)

</div>

<div class="card" markdown>

### Examples
Real-world examples and use cases.

- [RNA-seq Pipeline](examples/bioinformatics/rnaseq-pipeline.md)
- [Demultiplexing](examples/bioinformatics/demultiplexing.md)
- [Template Examples](examples/templates.md)

</div>

</div>

## 🔧 Installation

BPM is available on PyPI and can be installed with pip:

```bash
pip install bpm
```

For detailed installation instructions, see our [Installation Guide](getting-started/installation.md).

## 🤝 Contributing

We welcome contributions! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

- [Contributing Guidelines](developer-guide/contributing.md)
- [Development Setup](developer-guide/architecture.md)
- [Testing Guide](developer-guide/testing.md)

## 📄 License

BPM is released under the MIT License. See the [LICENSE](https://github.com/chaochungkuo/BPM/blob/main/LICENSE) file for details.

## 🔗 Quick Links

- [GitHub Repository](https://github.com/chaochungkuo/BPM)
- [PyPI Package](https://pypi.org/project/bpm/)
- [Issues](https://github.com/chaochungkuo/BPM/issues)
- [Releases](https://github.com/chaochungkuo/BPM/releases)

---

<div class="admonition info" markdown>

### Need Help?

- Check our [FAQ](troubleshooting/faq.md) for common questions
- Look at [Common Issues](troubleshooting/common-issues.md) for solutions
- Open an [issue](https://github.com/chaochungkuo/BPM/issues) for bugs or feature requests

</div> 