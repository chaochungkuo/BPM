# Configuration

This guide covers advanced configuration options for BPM, including environment variables, configuration files, and customization settings.

## Environment Variables

BPM uses several environment variables to control its behavior:

### Required Variables

#### `BPM_CACHE`
The cache directory where BPM stores repositories, templates, and other data.

```bash
# Linux/macOS
export BPM_CACHE="/path/to/your/bpm_cache"

# Windows
setx BPM_CACHE "C:\path\to\your\bpm_cache"
```

**Default**: `$HOME/.cache/bpm`

### Optional Variables

#### `BPM_CONFIG`
Path to a global configuration file.

```bash
export BPM_CONFIG="/path/to/global/config.yaml"
```

#### `BPM_LOG_LEVEL`
Controls the verbosity of BPM's logging output.

```bash
export BPM_LOG_LEVEL="DEBUG"    # Most verbose
export BPM_LOG_LEVEL="INFO"     # Default
export BPM_LOG_LEVEL="WARNING"  # Only warnings and errors
export BPM_LOG_LEVEL="ERROR"    # Only errors
```

#### `BPM_TEMPLATE_PATH`
Additional template search paths (colon-separated on Unix, semicolon-separated on Windows).

```bash
export BPM_TEMPLATE_PATH="/path/to/templates:/another/path"
```

## Configuration Files

BPM uses YAML configuration files at different levels:

### Global Configuration

**Location**: `~/.config/bpm/config.yaml`

```yaml
# Global BPM configuration
cache_dir: "/path/to/cache"
log_level: "INFO"
default_repository: "main"

# Template settings
template_search_paths:
  - "/path/to/custom/templates"
  - "/another/template/path"

# Workflow settings
workflow_timeout: 3600  # seconds
max_concurrent_workflows: 4

# UI settings
color_output: true
progress_bars: true
```

### Project Configuration

**Location**: `project.yaml` in each project directory

```yaml
# Project metadata
name: "240101_RNAseq_Study_Institute_Research"
description: "RNA-seq analysis of treatment vs control samples"
created_date: "2024-01-01"
author: "John Doe"
institution: "Research Institute"

# Project settings
active_repository: "bioinformatics_repo"
output_directory: "results"
temp_directory: "temp"

# Template variables
variables:
  threads: 8
  memory: "32G"
  genome: "GRCh38"
  adapter: "AGATCGGAAGAG"

# Workflow configurations
workflows:
  rnaseq:
    parameters:
      threads: 16
      memory: "64G"
    environment:
      CONDA_ENV: "rnaseq_env"
```

### Repository Configuration

**Location**: `repo.yaml` in each repository directory

```yaml
# Repository metadata
name: "bioinformatics_repo"
version: "1.0.0"
description: "Bioinformatics templates and workflows"
maintainer: "Bioinformatics Team"
license: "MIT"

# Repository settings
default_templates:
  - "demultiplexing:bclconvert"
  - "nfcore:rnaseq"

# Template configurations
templates:
  demultiplexing:
    bclconvert:
      description: "BCL Convert demultiplexing template"
      variables:
        threads: 8
        memory: "16G"
      dependencies:
        - "bclconvert"
        - "fastqc"

  nfcore:
    rnaseq:
      description: "nf-core RNA-seq pipeline template"
      variables:
        threads: 16
        memory: "64G"
        genome: "GRCh38"
      dependencies:
        - "nextflow"
        - "docker"

# Workflow configurations
workflows:
  generate_nfcore_rnaseq_samplesheet:
    description: "Generate sample sheet for nf-core RNA-seq"
    script: "workflows/generate_nfcore_rnaseq_samplesheet.py"
    parameters:
      input_dir: "required"
      output_file: "required"
      sample_pattern: "*.fastq.gz"
```

## Configuration Hierarchy

BPM follows a specific hierarchy for configuration settings:

1. **Command-line arguments** (highest priority)
2. **Project configuration** (`project.yaml`)
3. **Repository configuration** (`repo.yaml`)
4. **Global configuration** (`~/.config/bpm/config.yaml`)
5. **Environment variables**
6. **Default values** (lowest priority)

## Customizing Templates

### Template Variables

You can customize template behavior by setting variables:

```yaml
# In project.yaml
variables:
  # System resources
  threads: 16
  memory: "64G"
  
  # Analysis parameters
  genome: "GRCh38"
  adapter: "AGATCGGAAGAG"
  quality_threshold: 20
  
  # Paths
  data_dir: "/path/to/data"
  results_dir: "results"
  
  # Custom settings
  email: "user@institute.edu"
  queue: "long"
```

### Template Inheritance

Templates can inherit settings from parent configurations:

```yaml
# Base template configuration
base_template:
  variables:
    threads: 8
    memory: "32G"

# Specific template overrides
rnaseq_template:
  extends: "base_template"
  variables:
    threads: 16  # Override base setting
    memory: "64G"  # Override base setting
    genome: "GRCh38"  # New variable
```

## Advanced Settings

### Workflow Configuration

Configure workflow execution settings:

```yaml
# In project.yaml
workflows:
  default:
    timeout: 3600  # 1 hour
    retries: 3
    environment:
      CONDA_ENV: "bioinformatics"
    
  rnaseq:
    timeout: 7200  # 2 hours
    retries: 2
    parameters:
      threads: 16
      memory: "64G"
    environment:
      CONDA_ENV: "rnaseq_env"
      SLURM_PARTITION: "long"
```

### Repository Management

Configure repository behavior:

```yaml
# In global config
repositories:
  auto_update: true
  update_interval: 86400  # 24 hours
  cache_size_limit: "10GB"
  
  # Repository-specific settings
  bioinformatics_repo:
    auto_update: false
    update_interval: 604800  # 1 week
```

### Logging Configuration

Customize logging behavior:

```yaml
# In global config
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "/path/to/bpm.log"
  max_size: "10MB"
  backup_count: 5
```

## Security Considerations

### Sensitive Information

Avoid storing sensitive information in configuration files:

```yaml
# ❌ Don't do this
variables:
  api_key: "secret_key_here"
  password: "my_password"

# ✅ Use environment variables instead
variables:
  api_key: "${API_KEY}"
  password: "${DB_PASSWORD}"
```

### File Permissions

Set appropriate permissions for configuration files:

```bash
# Global config
chmod 600 ~/.config/bpm/config.yaml

# Project config
chmod 644 project.yaml

# Repository config
chmod 644 repo.yaml
```

## Troubleshooting Configuration

### Common Issues

1. **Configuration not loaded**: Check file paths and permissions
2. **Variables not resolved**: Ensure environment variables are set
3. **Template inheritance issues**: Verify YAML syntax and structure
4. **Workflow failures**: Check timeout and resource settings

### Debugging

Enable debug logging to troubleshoot configuration issues:

```bash
export BPM_LOG_LEVEL="DEBUG"
bpm info --verbose
```

### Validation

BPM validates configuration files and will show errors for invalid settings:

```bash
# Check project configuration
bpm info --project project.yaml

# Validate repository configuration
bpm repo list --verbose
```

## Best Practices

1. **Use environment variables** for sensitive information
2. **Keep configurations version-controlled** when appropriate
3. **Document custom configurations** in project README files
4. **Test configurations** before deploying to production
5. **Use consistent naming conventions** across projects
6. **Backup important configurations** regularly

## Examples

### Complete Project Configuration

```yaml
# project.yaml
name: "240101_RNAseq_Study_Institute_Research"
description: "RNA-seq analysis of treatment vs control samples"
created_date: "2024-01-01"
author: "John Doe"
institution: "Research Institute"

active_repository: "bioinformatics_repo"
output_directory: "results"
temp_directory: "temp"

variables:
  # System resources
  threads: 16
  memory: "64G"
  
  # Analysis parameters
  genome: "GRCh38"
  adapter: "AGATCGGAAGAG"
  quality_threshold: 20
  
  # Paths
  data_dir: "/data/raw"
  results_dir: "results"
  
  # Custom settings
  email: "john.doe@institute.edu"
  queue: "long"

workflows:
  rnaseq:
    timeout: 7200
    retries: 2
    parameters:
      threads: 16
      memory: "64G"
    environment:
      CONDA_ENV: "rnaseq_env"
      SLURM_PARTITION: "long"
```

This configuration provides a comprehensive setup for a typical RNA-seq analysis project with all necessary parameters and settings. 