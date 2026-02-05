"""Chart resolver for determining Helm chart references.

This module resolves service names to their Helm chart references,
handling both repository-based charts and local charts.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ChartReference:
    """Reference to a Helm chart."""
    
    chart_path: str  # e.g., "openstack-helm/libvirt" or "/path/to/chart"
    version: Optional[str] = None
    repo_name: Optional[str] = None
    repo_url: Optional[str] = None
    is_oci: bool = False
    
    def __str__(self) -> str:
        """String representation of the chart reference."""
        if self.version:
            return f"{self.chart_path} (version: {self.version})"
        return self.chart_path


class ChartResolver:
    """Resolves service names to Helm chart references."""
    
    # Default repository mappings for OpenStack services
    DEFAULT_REPOS = {
        "openstack-helm": {
            "url": "https://tarballs.opendev.org/openstack/openstack-helm",
            "services": [
                "barbican", "cinder", "glance", "heat", "horizon",
                "keystone", "neutron", "nova", "octavia", "placement"
            ]
        },
        "openstack-helm-infra": {
            "url": "https://tarballs.opendev.org/openstack/openstack-helm-infra",
            "services": [
                "libvirt", "mariadb", "memcached", "rabbitmq", "ovn"
            ]
        }
    }
    
    def __init__(
        self,
        chart_versions_path: str,
        custom_overrides_dir: Optional[str] = None
    ):
        """Initialize the chart resolver.
        
        Args:
            chart_versions_path: Path to helm-chart-versions.yaml
            custom_overrides_dir: Path to custom overrides directory
        """
        self.chart_versions_path = Path(chart_versions_path)
        self.custom_overrides_dir = Path(custom_overrides_dir) if custom_overrides_dir else None
        self.chart_versions: Dict[str, str] = {}
        self.custom_repos: Dict[str, Dict[str, str]] = {}
        
        self._load_chart_versions()
        if self.custom_overrides_dir:
            self._load_custom_repos()
    
    def _load_chart_versions(self) -> None:
        """Load chart versions from helm-chart-versions.yaml."""
        if not self.chart_versions_path.exists():
            logger.warning(f"Chart versions file not found: {self.chart_versions_path}")
            return
        
        try:
            with open(self.chart_versions_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if data and 'charts' in data:
                self.chart_versions = data['charts']
                logger.info(f"Loaded {len(self.chart_versions)} chart versions")
            else:
                logger.warning("No 'charts' section found in helm-chart-versions.yaml")
        
        except Exception as e:
            logger.error(f"Failed to load chart versions: {e}")
    
    def _load_custom_repos(self) -> None:
        """Load custom repository configurations from override files."""
        if not self.custom_overrides_dir or not self.custom_overrides_dir.exists():
            return
        
        # Look for service-specific override directories
        for service_dir in self.custom_overrides_dir.iterdir():
            if not service_dir.is_dir():
                continue
            
            service_name = service_dir.name
            
            # Check for YAML files with chart metadata
            for yaml_file in service_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r') as f:
                        data = yaml.safe_load(f)
                    
                    if data and 'chart' in data:
                        chart_config = data['chart']
                        self.custom_repos[service_name] = {
                            'repo_url': chart_config.get('repo_url', ''),
                            'repo_name': chart_config.get('repo_name', ''),
                            'service_name': chart_config.get('service_name', service_name)
                        }
                        logger.debug(f"Loaded custom repo config for {service_name}")
                        break  # Use first match
                
                except Exception as e:
                    logger.debug(f"Could not load chart config from {yaml_file}: {e}")
    
    def resolve(self, service_name: str) -> ChartReference:
        """Resolve a service name to a chart reference.
        
        Args:
            service_name: Name of the service
            
        Returns:
            ChartReference with chart path and metadata
        """
        # Get version from chart versions file
        version = self.chart_versions.get(service_name)
        
        # Check for custom repository configuration
        if service_name in self.custom_repos:
            custom = self.custom_repos[service_name]
            repo_url = custom['repo_url']
            repo_name = custom['repo_name']
            chart_service_name = custom['service_name']
            
            # Handle OCI registries
            if repo_url.startswith('oci://'):
                chart_path = f"{repo_url}/{repo_name}/{chart_service_name}"
                return ChartReference(
                    chart_path=chart_path,
                    version=version,
                    repo_name=repo_name,
                    repo_url=repo_url,
                    is_oci=True
                )
            else:
                chart_path = f"{repo_name}/{chart_service_name}"
                return ChartReference(
                    chart_path=chart_path,
                    version=version,
                    repo_name=repo_name,
                    repo_url=repo_url,
                    is_oci=False
                )
        
        # Use default repository mappings
        for repo_name, repo_config in self.DEFAULT_REPOS.items():
            if service_name in repo_config['services']:
                chart_path = f"{repo_name}/{service_name}"
                return ChartReference(
                    chart_path=chart_path,
                    version=version,
                    repo_name=repo_name,
                    repo_url=repo_config['url'],
                    is_oci=False
                )
        
        # Fallback: assume it's in openstack-helm repo
        logger.warning(
            f"No repository mapping found for {service_name}, "
            f"assuming openstack-helm repository"
        )
        return ChartReference(
            chart_path=f"openstack-helm/{service_name}",
            version=version,
            repo_name="openstack-helm",
            repo_url=self.DEFAULT_REPOS["openstack-helm"]["url"],
            is_oci=False
        )
    
    def get_version(self, service_name: str) -> Optional[str]:
        """Get the version for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Version string or None if not found
        """
        return self.chart_versions.get(service_name)
    
    def ensure_repo_added(self, chart_ref: ChartReference) -> bool:
        """Ensure the Helm repository is added.
        
        Args:
            chart_ref: Chart reference with repository info
            
        Returns:
            True if repository is ready, False otherwise
        """
        if chart_ref.is_oci:
            # OCI registries don't need to be added
            return True
        
        if not chart_ref.repo_name or not chart_ref.repo_url:
            logger.warning("Missing repository name or URL")
            return False
        
        try:
            import subprocess
            
            # Add repository
            subprocess.run(
                ["helm", "repo", "add", chart_ref.repo_name, chart_ref.repo_url],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Update repository
            subprocess.run(
                ["helm", "repo", "update"],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info(f"Added Helm repository: {chart_ref.repo_name}")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add Helm repository: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Failed to add Helm repository: {e}")
            return False
