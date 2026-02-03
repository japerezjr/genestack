"""Configuration management for upgrade tools."""

from .schema import UpgradeConfig, VersionUpdate, ValidationResult, ValidationIssue
from .schema import BreakingChange, DeploymentResult

__all__ = [
    "UpgradeConfig",
    "VersionUpdate",
    "ValidationResult",
    "ValidationIssue",
    "BreakingChange",
    "DeploymentResult",
]
