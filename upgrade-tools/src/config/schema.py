"""Configuration schema definitions using Pydantic."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
import yaml


class UpgradeConfig(BaseModel):
    """Configuration for the upgrade process."""
    
    source_release: str = Field(description="Source release version (e.g., '2024.1' or '2024.2')")
    target_release: str = Field(default="2025.1", description="Target release version")
    chart_versions_path: str = Field(
        default="helm-chart-versions.yaml",
        description="Path to helm-chart-versions.yaml"
    )
    overrides_base_path: str = Field(
        default="base-helm-configs/",
        description="Path to base-helm-configs/ directory"
    )
    namespace: str = Field(default="openstack", description="Kubernetes namespace")
    dry_run: bool = Field(default=False, description="Simulate without applying changes")
    skip_optional_services: bool = Field(
        default=False,
        description="Only upgrade core services"
    )
    backup_path: str = Field(default="backups/", description="Path to store backups")
    timeout_per_service: int = Field(
        default=600,
        description="Timeout in seconds for each service"
    )
    
    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "UpgradeConfig":
        """Load configuration from YAML file.
        
        Args:
            path: Path to YAML configuration file
            
        Returns:
            UpgradeConfig instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            raise ValueError(f"Empty or invalid YAML file: {path}")
        
        return cls(**data)


class VersionUpdate(BaseModel):
    """Represents a chart version update."""
    
    chart_name: str = Field(description="Name of the helm chart")
    current_version: str = Field(description="Current version string")
    target_version: str = Field(description="Target version string")
    category: str = Field(description="Category: core, optional, or infrastructure")
    dependencies: List[str] = Field(
        default_factory=list,
        description="Charts that must be upgraded first"
    )


class ValidationIssue(BaseModel):
    """Represents a validation issue."""
    
    severity: str = Field(description="Severity: critical, high, medium, or low")
    component: str = Field(description="Component name")
    description: str = Field(description="Issue description")
    remediation: str = Field(description="How to fix the issue")


class ValidationResult(BaseModel):
    """Result of a validation check."""
    
    passed: bool = Field(description="Whether validation passed")
    issues: List[ValidationIssue] = Field(
        default_factory=list,
        description="List of validation issues"
    )
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When validation was performed"
    )


class BreakingChange(BaseModel):
    """Represents a breaking change between releases."""
    
    component: str = Field(description="Service name")
    change_type: str = Field(
        description="Type: config, api, database, or dependency"
    )
    description: str = Field(description="Description of the change")
    impact: str = Field(description="Description of impact")
    mitigation: str = Field(description="How to address the change")
    severity: str = Field(description="Severity: critical, high, medium, or low")
    affects_deployment: bool = Field(
        default=False,
        description="Whether this deployment is affected"
    )


class DeploymentResult(BaseModel):
    """Result of a helm deployment."""
    
    success: bool = Field(description="Whether deployment succeeded")
    chart_name: str = Field(description="Name of the chart")
    release_name: str = Field(description="Helm release name")
    revision: int = Field(description="Helm revision number")
    duration: float = Field(description="Duration in seconds")
    pod_status: Dict[str, str] = Field(
        default_factory=dict,
        description="Pod name to status mapping"
    )
    errors: List[str] = Field(default_factory=list, description="Error messages")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
