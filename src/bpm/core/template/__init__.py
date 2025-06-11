"""Template management for BPM.

This package provides functionality for managing bioinformatics project templates.
"""

from bpm.core.template.models import TemplateConfig
from bpm.core.template.operations import Template

__all__ = [
    "TemplateConfig",
    "Template",
] 