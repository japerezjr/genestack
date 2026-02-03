"""Version parsing and comparison logic for OpenStack chart versions."""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path

from ..utils.yaml_utils import read_yaml_file


# Known OpenStack services that should be upgraded
OPENSTACK_SERVICES = {
    # Core services
    'keystone', 'glance', 'cinder', 'neutron', 'nova', 'placement', 'horizon', 'libvirt',
    # Optional services
    'barbican', 'blazar', 'ceilometer', 'cloudkitty', 'freezer', 'gnocchi', 'heat',
    'ironic', 'magnum', 'manila', 'masakari', 'octavia', 'trove', 'zaqar',
    # Infrastructure (may have OpenStack versions)
    'memcached', 'mariadb-operator', 'postgres-operator', 'rabbitmq'
}

# Caracal version patterns (2024.1 or 2024.2)
CARACAL_VERSION_PATTERN = re.compile(r'2024\.[12]')

# Epoxy version pattern (2025.1)
EPOXY_VERSION_PATTERN = re.compile(r'2025\.1')


@dataclass
class VersionUpdate:
    """Represents a version update for a helm chart."""
    chart_name: str
    current_version: str
    target_version: str
    category: str  # "core", "optional", "infrastructure", "non-openstack"
    dependencies: List[str]  # Charts that must be upgraded first
    
    def __str__(self) -> str:
        return f"{self.chart_name}: {self.current_version} -> {self.target_version}"


class VersionParser:
    """Parser for helm chart versions."""
    
    def __init__(self, chart_versions_path: str):
        """
        Initialize the version parser.
        
        Args:
            chart_versions_path: Path to helm-chart-versions.yaml file
        """
        self.chart_versions_path = Path(chart_versions_path)
        self.charts: Dict[str, str] = {}
        
    def load_versions(self) -> Dict[str, str]:
        """
        Load current chart versions from YAML file.
        
        Returns:
            Dictionary mapping chart names to version strings
            
        Raises:
            FileNotFoundError: If the versions file doesn't exist
            ValueError: If the file format is invalid
        """
        data = read_yaml_file(self.chart_versions_path)
        
        if 'charts' not in data:
            raise ValueError(f"Invalid format: 'charts' key not found in {self.chart_versions_path}")
        
        self.charts = data['charts']
        return self.charts
    
    def is_openstack_service(self, chart_name: str) -> bool:
        """
        Determine if a chart is an OpenStack service.
        
        Args:
            chart_name: Name of the helm chart
            
        Returns:
            True if the chart is an OpenStack service, False otherwise
        """
        return chart_name in OPENSTACK_SERVICES
    
    def is_caracal_version(self, version: str) -> bool:
        """
        Check if a version string is a Caracal version (2024.1 or 2024.2).
        
        Args:
            version: Version string to check
            
        Returns:
            True if the version contains 2024.1 or 2024.2, False otherwise
        """
        return bool(CARACAL_VERSION_PATTERN.search(version))
    
    def is_epoxy_version(self, version: str) -> bool:
        """
        Check if a version string is an Epoxy version (2025.1).
        
        Args:
            version: Version string to check
            
        Returns:
            True if the version contains 2025.1, False otherwise
        """
        return bool(EPOXY_VERSION_PATTERN.search(version))
    
    def categorize_chart(self, chart_name: str) -> str:
        """
        Categorize a chart as core, optional, infrastructure, or non-openstack.
        
        Args:
            chart_name: Name of the helm chart
            
        Returns:
            Category string: "core", "optional", "infrastructure", or "non-openstack"
        """
        core_services = {'keystone', 'glance', 'cinder', 'neutron', 'nova', 'placement', 'horizon', 'libvirt'}
        optional_services = {'barbican', 'blazar', 'ceilometer', 'cloudkitty', 'freezer', 'gnocchi', 
                           'heat', 'ironic', 'magnum', 'manila', 'masakari', 'octavia', 'trove', 'zaqar'}
        infrastructure_services = {'memcached', 'mariadb-operator', 'postgres-operator', 'rabbitmq'}
        
        if chart_name in core_services:
            return "core"
        elif chart_name in optional_services:
            return "optional"
        elif chart_name in infrastructure_services:
            return "infrastructure"
        else:
            return "non-openstack"
    
    def identify_updates(self, target_release: str = "2025.1") -> List[VersionUpdate]:
        """
        Identify which charts need version updates.
        
        Args:
            target_release: Target OpenStack release version (default: "2025.1")
            
        Returns:
            List of VersionUpdate objects for charts that need updating
        """
        if not self.charts:
            self.load_versions()
        
        updates = []
        
        for chart_name, current_version in self.charts.items():
            # Check if this is an OpenStack service with a Caracal version
            if self.is_openstack_service(chart_name) and self.is_caracal_version(current_version):
                # Determine the target version by replacing Caracal version with Epoxy
                target_version = self._compute_target_version(current_version, target_release)
                
                # Get chart category
                category = self.categorize_chart(chart_name)
                
                # Get dependencies (simplified for now, can be enhanced later)
                dependencies = self._get_dependencies(chart_name)
                
                update = VersionUpdate(
                    chart_name=chart_name,
                    current_version=current_version,
                    target_version=target_version,
                    category=category,
                    dependencies=dependencies
                )
                updates.append(update)
        
        return updates
    
    def _compute_target_version(self, current_version: str, target_release: str) -> str:
        """
        Compute the target version by replacing Caracal version with Epoxy.
        
        Args:
            current_version: Current version string
            target_release: Target release version (e.g., "2025.1")
            
        Returns:
            Target version string with Caracal version replaced
        """
        # Replace 2024.1 or 2024.2 with target release (2025.1)
        target_version = CARACAL_VERSION_PATTERN.sub(target_release, current_version)
        return target_version
    
    def _get_dependencies(self, chart_name: str) -> List[str]:
        """
        Get the list of charts that must be upgraded before this chart.
        
        Args:
            chart_name: Name of the helm chart
            
        Returns:
            List of chart names that are dependencies
        """
        # Simplified dependency mapping
        # Infrastructure services have no dependencies
        # Core services depend on infrastructure
        # Optional services depend on core services
        
        dependency_map = {
            # Core services depend on infrastructure
            'keystone': ['mariadb-operator', 'memcached', 'rabbitmq'],
            'glance': ['keystone', 'mariadb-operator'],
            'placement': ['keystone', 'mariadb-operator'],
            'cinder': ['keystone', 'placement', 'mariadb-operator', 'rabbitmq'],
            'neutron': ['keystone', 'mariadb-operator', 'rabbitmq'],
            'nova': ['keystone', 'placement', 'neutron', 'mariadb-operator', 'rabbitmq', 'libvirt'],
            'horizon': ['keystone'],
            'libvirt': [],
            
            # Optional services depend on core services
            'barbican': ['keystone', 'mariadb-operator'],
            'blazar': ['keystone', 'nova', 'mariadb-operator'],
            'ceilometer': ['keystone', 'rabbitmq'],
            'cloudkitty': ['keystone', 'gnocchi'],
            'freezer': ['keystone', 'mariadb-operator'],
            'gnocchi': ['keystone', 'ceilometer'],
            'heat': ['keystone', 'neutron', 'mariadb-operator'],
            'ironic': ['keystone', 'neutron', 'mariadb-operator'],
            'magnum': ['keystone', 'nova', 'neutron', 'mariadb-operator'],
            'manila': ['keystone', 'neutron', 'mariadb-operator'],
            'masakari': ['keystone', 'nova', 'mariadb-operator'],
            'octavia': ['keystone', 'neutron', 'mariadb-operator'],
            'trove': ['keystone', 'nova', 'neutron', 'mariadb-operator'],
            'zaqar': ['keystone', 'mariadb-operator'],
        }
        
        return dependency_map.get(chart_name, [])
