"""Configuration models for BPM.

This module defines the core data structures for configuration settings.
"""

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class RetentionPolicy(StrEnum):
    """Enumeration of retention policy types.
    
    Attributes:
        days: Retention period in days
        months: Retention period in months
        years: Retention period in years
    """
    days = "days"
    months = "months"
    years = "years"


class PolicyConfig(BaseModel):
    """Policy configuration model.
    
    This model stores policy settings including retention and cleanup policies.

    Attributes:
        retention_policy: Number of days to retain projects
        cleanup_policy: Whether to automatically clean up old projects
    """
    retention_policy: int = 365
    cleanup_policy: bool = False


class AuthorConfig(BaseModel):
    """Author configuration model.
    
    This model stores author information including name, affiliation,
    and contact details.

    Attributes:
        name: Author's full name
        affiliation: Author's institution or organization
        email: Author's email address
    """
    name: str
    affiliation: str
    email: str


class MainConfig(BaseModel):
    """Main configuration model.
    
    This model stores the main configuration settings including authors,
    policies, and paths.

    Attributes:
        authors: Dictionary of author configurations
        policy: Policy configuration
        template_dir: Path to templates directory
        project_dir: Path to projects directory
    """
    authors: dict[str, AuthorConfig]
    policy: PolicyConfig = PolicyConfig()
    template_dir: Path | None = None
    project_dir: Path | None = None 