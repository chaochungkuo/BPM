from pathlib import Path
from typing import Any, Dict, List
from bpm.core.config import get_bpm_config
import os
import psutil

def get_idle_threads_by_percentage(inputs: Dict[str, Any]) -> int:
    """Get the number of CPU cores to use based on real idle cores.
    
    Args:
        inputs: Dictionary of input parameters (unused)
        
    Returns:
        Number of CPU cores to use (percentage of idle cores)
        
    Note:
        First determines truly idle cores (usage < 5%),
        then applies the percentage ratio from config
        to determine how many of those idle cores to use.
    """
    # Get CPU usage for each core
    cpu_percentages = psutil.cpu_percent(interval=1, percpu=True)
    
    # Count truly idle cores (usage < 50%)
    idle_cores = sum(1 for usage in cpu_percentages if usage < 50)
    
    # Get percentage of idle cores to use from config
    percentage_of_cores = get_bpm_config("environment.yaml", "system.percentage_of_cores")
    
    # Calculate number of cores to use
    cores_to_use = int(idle_cores * percentage_of_cores)
    
    # Ensure at least 1 core is used if any are idle
    return max(1, cores_to_use) if idle_cores > 0 else 0
