# BPM (Benomic Project Manager)

## Prerequisites

Before using BPM, you must add the BPM repository to your environment. The repository contains essential configurations and templates.

### Adding BPM Repository

1. Clone the BPM repository:
```bash
git clone https://github.com/your-org/BPM_repo.git
```

2. Add the repository to BPM:
```bash
bpm add-repo /path/to/BPM_repo
```

## Configuration

### Host Path Configuration

BPM requires host path mappings to be configured in your environment. These mappings are stored in the cached environment configuration under `host_paths`. Example:

```yaml
host_paths:
  nextgen1: "/mnt/nextgen/"
  nextgen2: "/mnt/nextgen2/"
  nextgen3: "/mnt/nextgen3/"
  archive: "/mnt/nextgen2/archive/"
```

### Environment Configuration

The environment configuration file (`environment.yaml`) should be present in your BPM repository with the following structure:

```yaml
# System Resources
system:
  percentage_of_cores: 0.9
  max_memory_gb: 32

# Tool Paths
tool_paths:
  bclconvert: bcl-convert
  bcl2fastq: bcl2fastq
  cellranger: cellranger
  # ... other tools

# Reference Data
reference_data:
  cellranger:
    base: /data/shared/10xGenomics/
    # ... other references

# Host Paths
host_paths:
  nextgen1: "/mnt/nextgen/"
  nextgen2: "/mnt/nextgen2/"
  # ... other hosts
```

## Usage

### Path Resolution

BPM provides host-aware path resolution:

```python
from bpm.util.paths import path, from_path_to_hostpath, from_hostpath_to_path

# Get host mappings from config
host_mappings = {
    "nextgen": "/mnt/nextgen/",
    "nextgen2": "/mnt/nextgen2/"
}

# Convert to host:path format
physical_path = "/mnt/nextgen/data/sample1.txt"
host_path = from_path_to_hostpath(physical_path, host_mappings)
# Returns: "nextgen:data/sample1.txt"

# Convert from host:path format
full_path = from_hostpath_to_path("nextgen:data/sample1.txt", host_mappings)
# Returns: Path("/mnt/nextgen/data/sample1.txt")

# Basic path resolution
resolved_path = path.resolve("data/sample1.txt")
```

### Error Handling

If you encounter errors related to host mappings, ensure:
1. BPM repository is added and cached
2. Environment configuration contains valid `host_paths`
3. Current hostname is listed in the mappings

Common errors:
```python
# No configuration available
"No host mappings available. Please ensure environment configuration is cached or provide a valid configuration file."

# Missing cache
"No environment configuration found in cache"

# Missing host_paths
"No host_paths found in environment configuration"
```

## Development

### Adding New Hosts

To add a new host:
1. Update `environment.yaml` in your BPM repository
2. Add the host mapping under `host_paths`
3. Re-cache the environment configuration

### Custom Configuration

You can provide a custom host mappings file:
```python
from bpm.util.paths import HostAwarePath

custom_path = HostAwarePath(config_path="custom_hosts.yaml")
```
