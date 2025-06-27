# Quick Start Guide

This guide will walk you through creating your first bioinformatics project with BPM. You'll learn the basic workflow and see how BPM can streamline your project management.

## Prerequisites

Before starting, ensure you have:

- [BPM installed](installation.md) and configured
- A BPM repository with templates (we'll use the demo repository)

## Step 1: Initialize Your First Project

Start by creating a new bioinformatics project with BPM:

```bash
bpm init 240101_RNAseq_Analysis_Institute_Research
```

This command creates a new project with the standardized naming format: `YYMMDD_ProjectName_Institute_Application`

The project will be created in your current directory with the following structure:

```
240101_RNAseq_Analysis_Institute_Research/
├── project.yaml          # Project configuration
├── README.md            # Project documentation
└── .gitignore          # Git ignore file
```

## Step 2: Add a Repository

BPM works with external repositories that contain templates and workflows. Let's add a repository:

```bash
# Add a local repository
bpm repo add /path/to/your/bpm_repository

# Or add from GitHub (if available)
bpm repo add https://github.com/username/bpm-repo.git
```

List available repositories:

```bash
bpm repo list
```

Select an active repository:

```bash
bpm repo select repository_name
```

## Step 3: Explore Available Templates

See what templates are available in your repository:

```bash
bpm generate --list
```

You should see output like:
```
Available templates:
  demultiplexing:bclconvert
  nfcore:rnaseq
  workflows:generate_nfcore_rnaseq_samplesheet
```

## Step 4: Generate Files from a Template

Generate project files using a template. For example, to create a demultiplexing setup:

```bash
bpm generate demultiplexing:bclconvert --project project.yaml
```

This will create files based on the template, such as:
- Configuration files
- Scripts
- Sample sheets
- Documentation

## Step 5: Run a Workflow

Execute a bioinformatics workflow:

```bash
bpm run workflows:generate_nfcore_rnaseq_samplesheet --project project.yaml
```

This will run the specified workflow and generate outputs in your project directory.

## Step 6: Update Template Outputs

If you need to regenerate files from a template (e.g., after configuration changes):

```bash
bpm update --template demultiplexing:bclconvert --project project.yaml
```

## Step 7: View Project Information

Check your project status and configuration:

```bash
bpm info --project project.yaml
```

This shows:
- Project metadata
- Active repository
- Generated files
- Configuration settings

## Complete Example Workflow

Here's a complete example of setting up an RNA-seq analysis project:

```bash
# 1. Initialize project
bpm init 240101_RNAseq_Study_Institute_Research

# 2. Add repository
bpm repo add /path/to/bioinformatics_repo

# 3. Generate RNA-seq template
bpm generate nfcore:rnaseq --project project.yaml

# 4. Run sample sheet generation
bpm run workflows:generate_nfcore_rnaseq_samplesheet --project project.yaml

# 5. Check project status
bpm info --project project.yaml
```

## Project Structure

After running these commands, your project will have a structure like:

```
240101_RNAseq_Study_Institute_Research/
├── project.yaml
├── README.md
├── .gitignore
├── config/
│   └── nfcore_rnaseq.yaml
├── scripts/
│   └── run_rnaseq.sh
├── samplesheet.csv
└── outputs/
    └── samplesheet_generated.csv
```

## Key Concepts

### Project Naming Convention

BPM uses a standardized naming format: `YYMMDD_ProjectName_Institute_Application`

- **YYMMDD**: Date in YYMMDD format
- **ProjectName**: Descriptive project name
- **Institute**: Your institution or organization
- **Application**: Type of analysis or application

### Template System

Templates are organized as `section:name`:
- **section**: Category (e.g., demultiplexing, nfcore)
- **name**: Specific template (e.g., bclconvert, rnaseq)

### Repository Management

BPM repositories contain:
- **Templates**: File generation templates
- **Workflows**: Executable workflows
- **Configuration**: Repository-specific settings

## Next Steps

Now that you've completed the quick start:

1. **Explore Templates**: Try different templates in your repository
2. **Customize Configurations**: Modify generated files for your specific needs
3. **Learn Advanced Features**: Read the [User Guide](../user-guide/projects.md)
4. **Create Your Own Templates**: See the [Admin Guide](../admin-guide/template-development.md)

## Troubleshooting

If you encounter issues:

- Check that your `BPM_CACHE` environment variable is set correctly
- Ensure your repository contains valid templates and workflows
- Verify that your project.yaml file is properly formatted
- See [Common Issues](../troubleshooting/common-issues.md) for solutions

## Getting Help

- **Documentation**: Browse the full [User Guide](../user-guide/projects.md)
- **Examples**: Check [Example Workflows](../examples/bioinformatics/rnaseq-pipeline.md)
- **Issues**: Report problems on [GitHub](https://github.com/chaochungkuo/BPM/issues)
- **FAQ**: Common questions in [FAQ](../troubleshooting/faq.md) 