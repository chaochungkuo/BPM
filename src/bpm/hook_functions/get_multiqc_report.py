from pathlib import Path
from typing import Any, Dict, List
import os
import glob


def get_multiqc_report(inputs: Dict[str, Any]) -> Path:
    """Locate the MultiQC report HTML file.
    
    Args:
        inputs: Dictionary of input parameters (unused)
        
    Returns:
        Path to the MultiQC report HTML file
        
    Raises:
        FileNotFoundError: If no MultiQC report is found
    """
    current_dir = Path.cwd()
    report_files = []
    
    # Walk through all subdirectories
    for root, _, _ in os.walk(current_dir):
        # Search for multiqc_report_*.html files
        reports = glob.glob(str(Path(root) / "multiqc_report*.html"))
        report_files.extend([Path(report) for report in reports])
    
    if not report_files:
        raise FileNotFoundError(
            "No MultiQC report found in current directory or subdirectories"
        )
    
    if len(report_files) > 1:
        print("Warning: Multiple MultiQC reports found:")
        for report in report_files:
            print(f"  - {report}")
        print(f"Using: {report_files[0]}")
    
    return report_files[0]
