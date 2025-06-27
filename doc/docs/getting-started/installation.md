# Installation

This guide will help you install BPM and set up your environment for bioinformatics project management.

## Prerequisites

Before installing BPM, ensure you have:

- **Python 3.10 or higher** installed on your system
- **pip** (Python package installer)
- **Git** (for repository management)

### Check Your Python Version

```bash
python --version
# or
python3 --version
```

If you don't have Python 3.10+, you can download it from [python.org](https://www.python.org/downloads/).

## Installation Methods

### Method 1: Install from PyPI (Recommended)

The easiest way to install BPM is using pip:

```bash
pip install bpm
```

### Method 2: Install from Source

If you want to install the latest development version:

```bash
# Clone the repository
git clone https://github.com/chaochungkuo/BPM.git
cd BPM

# Install in development mode
pip install -e .
```

### Method 3: Using Conda (Coming Soon)

```bash
# This will be available once we publish to conda-forge
conda install -c conda-forge bpm
```

## Verify Installation

After installation, verify that BPM is working correctly:

```bash
bpm --version
```

You should see output similar to:
```
BPM version 0.0.3
```

## Configuration

### Setting Up BPM Cache

BPM uses a cache directory to store repositories, templates, and other data. You need to set the `BPM_CACHE` environment variable:

#### Linux/macOS

Add this line to your shell configuration file (`.bashrc`, `.zshrc`, etc.):

```bash
export BPM_CACHE="/path/to/your/bpm_cache"
```

Then reload your shell configuration:

```bash
source ~/.bashrc
# or
source ~/.zshrc
```

#### Windows

Set the environment variable through System Properties or use:

```cmd
setx BPM_CACHE "C:\path\to\your\bpm_cache"
```

#### Default Location

If you don't set `BPM_CACHE`, BPM will use the default location:
- **Linux/macOS**: `$HOME/.cache/bpm`
- **Windows**: `%USERPROFILE%\.cache\bpm`

### Verify Configuration

Test that your cache directory is properly configured:

```bash
bpm info
```

This should show your BPM configuration including the cache directory.

## Dependencies

BPM automatically installs the following dependencies:

- **pydantic** (≥2.0.0) - Data validation
- **pyyaml** (≥6.0.0) - YAML file handling
- **typer** (≥0.9.0) - CLI framework
- **rich** (≥13.0.0) - Terminal formatting
- **jinja2** (≥3.1.0) - Template engine
- **ruamel.yaml** (≥0.17.0) - YAML processing
- **psutil** (≥6.0.0) - System utilities
- **httpx** (≥0.24.0) - HTTP client
- **gitpython** (≥3.1.0) - Git integration

## Troubleshooting

### Common Installation Issues

#### Permission Errors

If you encounter permission errors during installation:

```bash
# Use user installation
pip install --user bpm

# Or use a virtual environment
python -m venv bpm_env
source bpm_env/bin/activate  # On Windows: bpm_env\Scripts\activate
pip install bpm
```

#### Python Version Issues

Ensure you're using Python 3.10 or higher:

```bash
# Check Python version
python --version

# If you have multiple Python versions, use python3
python3 --version
```

#### Cache Directory Issues

If BPM can't access the cache directory:

```bash
# Create the directory manually
mkdir -p /path/to/your/bpm_cache

# Set proper permissions
chmod 755 /path/to/your/bpm_cache
```

### Getting Help

If you encounter issues during installation:

1. Check the [Common Issues](troubleshooting/common-issues.md) page
2. Look at the [FAQ](troubleshooting/faq.md)
3. Open an [issue](https://github.com/chaochungkuo/BPM/issues) on GitHub

## Next Steps

Once BPM is installed and configured, you can:

1. [Quick Start Guide](quick-start.md) - Get your first project running
2. [Configuration](configuration.md) - Learn about advanced configuration options
3. [User Guide](../user-guide/projects.md) - Explore BPM's features

## Updating BPM

To update BPM to the latest version:

```bash
pip install --upgrade bpm
```

To check for updates:

```bash
pip list --outdated | grep bpm
``` 