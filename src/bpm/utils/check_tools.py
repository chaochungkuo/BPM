"""Utility functions for checking tool availability.

This module provides functions to validate whether required programs
are accessible in the system PATH.
"""

import shutil
from typing import List, Dict, Tuple


def check_programs(programs: List[str] | str) -> Tuple[bool, List[str]]:
    """Check if programs are accessible in PATH.
    
    Args:
        programs: Single program name or list of program names to check
        
    Returns:
        Tuple of (all_programs_found, list of missing programs)
        
    Example:
        >>> check_programs("bcl2fastq")
        (True, [])
        >>> check_programs(["bcl2fastq", "fastqc"])
        (False, ["fastqc"])
    """
    if isinstance(programs, str):
        programs = [programs]
        
    missing = []
    for program in programs:
        if shutil.which(program) is None:
            missing.append(program)
            
    return len(missing) == 0, missing
