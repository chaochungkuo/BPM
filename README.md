# BPM (Bioinformatics Project Manager)

A flexible, template-driven CLI tool for managing bioinformatics projects.

## Features

- **Project Management**: Create and manage bioinformatics projects with standardized naming
- **Template System**: Generate project files from customizable templates
- **Workflow Execution**: Run predefined bioinformatics workflows
- **Repository Management**: Manage template and workflow repositories
- **Host-Aware Paths**: Cross-platform path resolution with host mapping

## Installation

```bash
pip install bpm
```

In order to configure BPM cache folder, it is necessary to set the environment variable `BPM_CACHE` where you want to save cache files. If not specified, it will be set as `$HOME/.cache/bpm`. This variable needs to be always available by BPM and should be set in the `.bashrc`.

```bash
export BPM_CACHE="/path/to/bpm_cache"
```

## Quick Start

1. Initialize a new project:
```bash
bpm init 230101_ProjectName_Institute_Application
```

2. Add a repository:
```bash
bpm repo add /path/to/repository
```

3. Generate files from a template:
```bash
bpm generate template_name --project project.yaml
```

4. Run a workflow:
```bash
bpm run workflow_name --project project.yaml
```

## Commands

### Project Management

```bash
# Initialize a new project
bpm init 230101_ProjectName_Institute_Application

# Show project information
bpm info --project project.yaml

# Update template outputs
bpm update --template section:name --project project.yaml
```

### Repository Management

```bash
# Add a repository
bpm repo add /path/to/repository

# List repositories
bpm repo list

# Select active repository
bpm repo select repository_name

# Update repository
bpm repo update
```

### Template and Workflow Management

```bash
# Generate files from template
bpm generate template_name --project project.yaml

# Run a workflow
bpm run workflow_name --project project.yaml
```

## Development

### Adding New Templates


### Adding New Workflows


## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License
