# CLI Reference

This page provides a complete reference for all BPM command-line interface commands and options.

## Command Overview

BPM provides several main command categories:

- **Project Management**: `init`, `info`
- **Repository Management**: `repo`
- **Template Operations**: `generate`, `update`
- **Workflow Execution**: `run`
- **Utility Commands**: `--help`, `--version`

## Global Options

All BPM commands support these global options:

```bash
--help, -h          Show help message and exit
--version, -V       Show version and exit
--verbose, -v       Enable verbose output
--quiet, -q         Suppress output
```

## Project Management Commands

### `bpm init`

Initialize a new bioinformatics project.

```bash
bpm init PROJECT_NAME [OPTIONS]
```

**Arguments:**
- `PROJECT_NAME`: Project name in format `YYMMDD_ProjectName_Institute_Application`

**Options:**
```bash
--force, -f         Overwrite existing project directory
--template TEXT     Use specific template for initialization
--config PATH       Path to configuration file
```

**Examples:**
```bash
# Basic project initialization
bpm init 240101_RNAseq_Study_Institute_Research

# Initialize with specific template
bpm init 240101_RNAseq_Study_Institute_Research --template nfcore:rnaseq

# Force overwrite existing directory
bpm init 240101_RNAseq_Study_Institute_Research --force
```

### `bpm info`

Display project information and status.

```bash
bpm info [OPTIONS]
```

**Options:**
```bash
--project PATH      Path to project.yaml file (default: current directory)
--template TEXT     Show information for specific template
--verbose, -v       Show detailed information
```

**Examples:**
```bash
# Show current project info
bpm info

# Show info for specific project
bpm info --project /path/to/project/project.yaml

# Show detailed template information
bpm info --template demultiplexing:bclconvert --verbose
```

## Repository Management Commands

### `bpm repo`

Manage BPM repositories.

```bash
bpm repo [COMMAND] [OPTIONS]
```

#### `bpm repo add`

Add a new repository to BPM.

```bash
bpm repo add REPOSITORY_PATH [OPTIONS]
```

**Arguments:**
- `REPOSITORY_PATH`: Path to repository (local path or Git URL)

**Options:**
```bash
--name TEXT         Custom name for the repository
--force, -f         Overwrite existing repository
```

**Examples:**
```bash
# Add local repository
bpm repo add /path/to/local/repo

# Add from Git URL
bpm repo add https://github.com/username/bpm-repo.git

# Add with custom name
bpm repo add /path/to/repo --name my-custom-repo
```

#### `bpm repo list`

List all available repositories.

```bash
bpm repo list [OPTIONS]
```

**Options:**
```bash
--verbose, -v       Show detailed repository information
```

**Examples:**
```bash
# List repositories
bpm repo list

# Show detailed information
bpm repo list --verbose
```

#### `bpm repo select`

Select the active repository.

```bash
bpm repo select REPOSITORY_NAME [OPTIONS]
```

**Arguments:**
- `REPOSITORY_NAME`: Name of the repository to activate

**Examples:**
```bash
# Select repository by name
bpm repo select my-repository

# Select default repository
bpm repo select default
```

#### `bpm repo update`

Update repository from source.

```bash
bpm repo update [REPOSITORY_NAME] [OPTIONS]
```

**Arguments:**
- `REPOSITORY_NAME`: Name of repository to update (optional, updates all if not specified)

**Options:**
```bash
--force, -f         Force update even if no changes detected
```

**Examples:**
```bash
# Update all repositories
bpm repo update

# Update specific repository
bpm repo update my-repository

# Force update
bpm repo update --force
```

#### `bpm repo remove`

Remove a repository from BPM.

```bash
bpm repo remove REPOSITORY_NAME [OPTIONS]
```

**Arguments:**
- `REPOSITORY_NAME`: Name of the repository to remove

**Options:**
```bash
--force, -f         Force removal without confirmation
```

**Examples:**
```bash
# Remove repository
bpm repo remove my-repository

# Force removal
bpm repo remove my-repository --force
```

## Template Operations

### `bpm generate`

Generate files from templates.

```bash
bpm generate TEMPLATE_NAME [OPTIONS]
```

**Arguments:**
- `TEMPLATE_NAME`: Template name in format `section:name`

**Options:**
```bash
--project PATH      Path to project.yaml file
--output PATH       Output directory (default: current directory)
--force, -f         Overwrite existing files
--dry-run          Show what would be generated without creating files
--list, -l         List available templates
--variables TEXT   Additional template variables (JSON format)
```

**Examples:**
```bash
# Generate from template
bpm generate demultiplexing:bclconvert --project project.yaml

# List available templates
bpm generate --list

# Dry run to see what would be generated
bpm generate nfcore:rnaseq --project project.yaml --dry-run

# Generate with custom variables
bpm generate nfcore:rnaseq --project project.yaml --variables '{"threads": 8, "memory": "32G"}'
```

### `bpm update`

Update files generated from templates.

```bash
bpm update [OPTIONS]
```

**Options:**
```bash
--project PATH      Path to project.yaml file
--template TEXT     Update specific template
--force, -f         Force update all templates
--dry-run          Show what would be updated without making changes
```

**Examples:**
```bash
# Update all templates
bpm update --project project.yaml

# Update specific template
bpm update --template demultiplexing:bclconvert --project project.yaml

# Dry run to see changes
bpm update --project project.yaml --dry-run
```

## Workflow Execution

### `bpm run`

Execute workflows.

```bash
bpm run WORKFLOW_NAME [OPTIONS]
```

**Arguments:**
- `WORKFLOW_NAME`: Workflow name in format `section:name`

**Options:**
```bash
--project PATH      Path to project.yaml file
--output PATH       Output directory
--force, -f         Force execution even if outputs exist
--dry-run          Show what would be executed without running
--list, -l         List available workflows
--parameters TEXT  Workflow parameters (JSON format)
```

**Examples:**
```bash
# Run workflow
bpm run workflows:generate_nfcore_rnaseq_samplesheet --project project.yaml

# List available workflows
bpm run --list

# Run with parameters
bpm run workflows:generate_nfcore_rnaseq_samplesheet --project project.yaml --parameters '{"input_dir": "/path/to/data"}'

# Dry run workflow
bpm run workflows:generate_nfcore_rnaseq_samplesheet --project project.yaml --dry-run
```

## Configuration

### Environment Variables

BPM uses these environment variables:

```bash
BPM_CACHE          Cache directory for BPM data (default: $HOME/.cache/bpm)
BPM_CONFIG         Path to global configuration file
BPM_LOG_LEVEL      Logging level (DEBUG, INFO, WARNING, ERROR)
```

### Configuration Files

BPM uses YAML configuration files:

- **Global config**: `~/.config/bpm/config.yaml`
- **Project config**: `project.yaml` in project directory
- **Repository config**: `repo.yaml` in repository directory

## Exit Codes

BPM uses standard exit codes:

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Template error
- `4`: Workflow error
- `5`: Repository error

## Examples

### Complete Workflow Example

```bash
# Initialize project
bpm init 240101_RNAseq_Study_Institute_Research

# Add repository
bpm repo add /path/to/bioinformatics_repo

# List available templates
bpm generate --list

# Generate RNA-seq template
bpm generate nfcore:rnaseq --project project.yaml

# List available workflows
bpm run --list

# Run sample sheet generation
bpm run workflows:generate_nfcore_rnaseq_samplesheet --project project.yaml

# Check project status
bpm info --project project.yaml
```

### Advanced Usage

```bash
# Generate template with custom variables
bpm generate nfcore:rnaseq \
  --project project.yaml \
  --variables '{"threads": 16, "memory": "64G", "genome": "GRCh38"}'

# Run workflow with parameters
bpm run workflows:process_data \
  --project project.yaml \
  --parameters '{"input_dir": "/data/raw", "output_dir": "/data/processed"}'

# Update specific template
bpm update --template demultiplexing:bclconvert --project project.yaml

# Force update all templates
bpm update --project project.yaml --force
```

## Getting Help

For additional help:

```bash
# General help
bpm --help

# Command-specific help
bpm init --help
bpm generate --help
bpm run --help

# Version information
bpm --version
``` 