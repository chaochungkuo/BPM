from pathlib import Path
from typing import Any, Dict, List
import os


def get_FASTQ_folder(inputs: Dict[str, Any]) -> Path:
    """Locate the folder containing FASTQ files, excluding Undetermined reads.
    
    Args:
        inputs: Dictionary of input parameters (unused)
        
    Returns:
        Path to the folder containing FASTQ files
        
    Raises:
        FileNotFoundError: If no valid FASTQ folder is found
    """
    current_dir = Path.cwd()
    fastq_extensions = ['.fastq', '.fastq.gz', '.fq', '.fq.gz']
    fastq_folders = []
    
    # Walk through all subdirectories
    for root, _, files in os.walk(current_dir):
        # Skip if this is an Undetermined folder
        if 'Undetermined' in root:
            continue
            
        # Check if any FASTQ files exist in this directory
        has_fastq = any(
            any(file.endswith(ext) for ext in fastq_extensions)
            for file in files
        )
        
        if has_fastq:
            fastq_folders.append(Path(root))
    
    if not fastq_folders:
        raise FileNotFoundError(
            "No FASTQ files found in current directory or subdirectories "
            "(excluding Undetermined reads)"
        )
    
    if len(fastq_folders) > 1:
        print("Warning: Multiple FASTQ folders found:")
        for folder in fastq_folders:
            print(f"  - {folder}")
        print(f"Using: {fastq_folders[0]}")
    
    return fastq_folders[0]
