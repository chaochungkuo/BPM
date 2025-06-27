# Frequently Asked Questions (FAQ)

This page answers the most common questions about BPM. If you don't find your answer here, check the [Common Issues](common-issues.md) page or open an [issue](https://github.com/chaochungkuo/BPM/issues) on GitHub.

## General Questions

### What is BPM?

**BPM (Bioinformatics Project Manager)** is a flexible, template-driven CLI tool designed to streamline bioinformatics project management. It helps you:

- Create standardized project structures
- Generate files from customizable templates
- Execute predefined bioinformatics workflows
- Manage template and workflow repositories
- Ensure consistency across research projects

### Who should use BPM?

BPM is designed for:
- **Bioinformaticians** who want to standardize their project workflows
- **Research teams** that need consistent project structures
- **Laboratory managers** who want to share templates across their organization
- **Developers** who create bioinformatics tools and want to provide standardized setups

### Is BPM free to use?

Yes! BPM is open-source software released under the MIT License. You can use it freely for both personal and commercial projects.

## Installation & Setup

### How do I install BPM?

The easiest way is using pip:

```bash
pip install bpm
```

For detailed installation instructions, see our [Installation Guide](../getting-started/installation.md).

### What are the system requirements?

- **Python 3.10 or higher**
- **pip** (Python package installer)
- **Git** (for repository management)
- **Sufficient disk space** for your cache directory

### How do I set up the BPM cache directory?

Set the `BPM_CACHE` environment variable:

```bash
# Linux/macOS
export BPM_CACHE="/path/to/your/bpm_cache"

# Windows
setx BPM_CACHE "C:\path\to\your\bpm_cache"
```

If not set, BPM will use the default location: `$HOME/.cache/bpm`

### Can I use BPM without setting BPM_CACHE?

Yes, BPM will use the default cache location (`$HOME/.cache/bpm`), but it's recommended to set a custom location for better organization and backup purposes.

## Project Management

### What is the project naming convention?

BPM uses the format: `YYMMDD_ProjectName_Institute_Application`

- **YYMMDD**: Date in YYMMDD format (e.g., 240101 for January 1, 2024)
- **ProjectName**: Descriptive project name
- **Institute**: Your institution or organization
- **Application**: Type of analysis or application

Example: `240101_RNAseq_Study_Institute_Research`

### Can I change the project naming convention?

The naming convention is built into BPM for consistency. However, you can create custom templates that generate different project structures.

### How do I organize multiple projects?

Each BPM project is self-contained in its own directory. You can organize them however you prefer:

```
research/
├── 240101_RNAseq_Study_Institute_Research/
├── 240102_ChIPseq_Study_Institute_Research/
└── 240103_Metagenomics_Study_Institute_Research/
```

## Templates & Workflows

### What are templates?

Templates are predefined file structures that BPM uses to generate project files. They can include:

- Configuration files
- Scripts
- Sample sheets
- Documentation
- Any other project files

### How do I find available templates?

```bash
bpm generate --list
```

This shows all templates available in your active repository.

### Can I create my own templates?

Yes! See our [Template Development Guide](../admin-guide/template-development.md) for detailed instructions.

### What are workflows?

Workflows are executable scripts or programs that perform specific bioinformatics tasks. They can:

- Process data
- Generate reports
- Create sample sheets
- Run analyses

### How do I find available workflows?

```bash
bpm run --list
```

This shows all workflows available in your active repository.

## Repositories

### What are BPM repositories?

BPM repositories are collections of templates and workflows. They can be:

- **Local directories** on your system
- **Git repositories** (local or remote)
- **Shared repositories** within your organization

### How do I add a repository?

```bash
# Add local repository
bpm repo add /path/to/repository

# Add from Git URL
bpm repo add https://github.com/username/bpm-repo.git
```

### Can I use multiple repositories?

Yes! You can add multiple repositories, but only one can be active at a time. Use `bpm repo select` to switch between them.

### How do I update repositories?

```bash
# Update all repositories
bpm repo update

# Update specific repository
bpm repo update repository_name
```

## Configuration

### Where are configuration files stored?

- **Global config**: `~/.config/bpm/config.yaml`
- **Project config**: `project.yaml` in project directory
- **Repository config**: `repo.yaml` in repository directory

### Can I customize BPM behavior?

Yes, through:
- Environment variables
- Configuration files
- Custom templates and workflows

### How do I set environment variables?

```bash
# Linux/macOS (add to .bashrc or .zshrc)
export BPM_CACHE="/path/to/cache"
export BPM_LOG_LEVEL="DEBUG"

# Windows
setx BPM_CACHE "C:\path\to\cache"
setx BPM_LOG_LEVEL "DEBUG"
```

## Troubleshooting

### BPM command not found

This usually means BPM isn't installed or isn't in your PATH:

```bash
# Check if BPM is installed
pip list | grep bpm

# Reinstall if needed
pip install bpm

# Check PATH
which bpm
```

### Permission errors

Try installing with user permissions:

```bash
pip install --user bpm
```

Or use a virtual environment:

```bash
python -m venv bpm_env
source bpm_env/bin/activate  # On Windows: bpm_env\Scripts\activate
pip install bpm
```

### Cache directory issues

```bash
# Create directory manually
mkdir -p /path/to/your/bpm_cache

# Set proper permissions
chmod 755 /path/to/your/bpm_cache

# Check environment variable
echo $BPM_CACHE
```

### Template not found

Check that:
1. You have an active repository: `bpm repo list`
2. The template exists: `bpm generate --list`
3. The repository is up to date: `bpm repo update`

### Workflow execution fails

Common causes:
1. **Missing dependencies**: Install required software
2. **Incorrect parameters**: Check workflow documentation
3. **Permission issues**: Ensure scripts are executable
4. **Path issues**: Verify input/output paths exist

## Advanced Usage

### Can I use BPM in scripts?

Yes! BPM is designed for automation:

```bash
#!/bin/bash
# Initialize project
bpm init 240101_MyProject_Institute_Research

# Generate template
bpm generate nfcore:rnaseq --project project.yaml

# Run workflow
bpm run workflows:process_data --project project.yaml
```

### Can I integrate BPM with other tools?

Yes! BPM can be integrated with:
- **Nextflow** workflows
- **Snakemake** pipelines
- **Docker** containers
- **Slurm** job schedulers
- **Git** version control

### How do I backup my BPM data?

Backup your cache directory:

```bash
# Backup cache
tar -czf bpm_cache_backup.tar.gz $BPM_CACHE

# Restore cache
tar -xzf bpm_cache_backup.tar.gz
```

### Can I share templates with my team?

Yes! Create a shared repository:

1. Create a Git repository with your templates
2. Share the repository URL with your team
3. Team members add it with: `bpm repo add <repository_url>`

## Getting Help

### Where can I get help?

1. **Documentation**: Browse our [User Guide](../user-guide/projects.md)
2. **Examples**: Check [Example Workflows](../examples/bioinformatics/rnaseq-pipeline.md)
3. **Issues**: Report bugs on [GitHub](https://github.com/chaochungkuo/BPM/issues)
4. **FAQ**: This page for common questions

### How do I report a bug?

1. Check if it's already reported: [Issues](https://github.com/chaochungkuo/BPM/issues)
2. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Your system information
   - Error messages

### Can I contribute to BPM?

Yes! We welcome contributions:

- **Code**: Fix bugs, add features
- **Documentation**: Improve guides, add examples
- **Templates**: Share useful templates
- **Testing**: Report issues, test new features

See our [Contributing Guide](../developer-guide/contributing.md) for details.

### How do I stay updated?

- **Watch the repository** on GitHub for updates
- **Check releases** for new versions
- **Follow the changelog** for detailed updates
- **Update regularly**: `pip install --upgrade bpm` 