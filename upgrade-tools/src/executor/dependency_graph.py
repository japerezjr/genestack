"""Service dependency graph for OpenStack upgrade ordering.

This module defines the dependencies between OpenStack services and provides
topological sorting to determine the correct upgrade order.
"""

from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class ServiceNode:
    """Represents a service in the dependency graph."""
    name: str
    category: str  # "infrastructure", "core", "optional"
    dependencies: List[str]  # List of service names this service depends on


class DependencyGraph:
    """Manages service dependencies and computes upgrade order."""
    
    # Define service dependencies based on OpenStack architecture
    SERVICE_DEPENDENCIES = {
        # Infrastructure services (no OpenStack dependencies)
        "memcached": ServiceNode("memcached", "infrastructure", []),
        "mariadb-operator": ServiceNode("mariadb-operator", "infrastructure", []),
        "postgres-operator": ServiceNode("postgres-operator", "infrastructure", []),
        "rabbitmq": ServiceNode("rabbitmq", "infrastructure", []),
        
        # Core services
        "keystone": ServiceNode("keystone", "core", ["mariadb-operator", "memcached"]),
        "glance": ServiceNode("glance", "core", ["keystone", "mariadb-operator"]),
        "placement": ServiceNode("placement", "core", ["keystone", "mariadb-operator"]),
        "cinder": ServiceNode("cinder", "core", ["keystone", "mariadb-operator", "rabbitmq"]),
        "neutron": ServiceNode("neutron", "core", ["keystone", "mariadb-operator", "rabbitmq"]),
        "nova": ServiceNode("nova", "core", ["keystone", "placement", "neutron", "glance", "mariadb-operator", "rabbitmq"]),
        "horizon": ServiceNode("horizon", "core", ["keystone"]),
        "libvirt": ServiceNode("libvirt", "core", []),
        
        # Optional services
        "barbican": ServiceNode("barbican", "optional", ["keystone", "mariadb-operator", "rabbitmq"]),
        "blazar": ServiceNode("blazar", "optional", ["keystone", "nova", "mariadb-operator"]),
        "ceilometer": ServiceNode("ceilometer", "optional", ["keystone", "rabbitmq"]),
        "cloudkitty": ServiceNode("cloudkitty", "optional", ["keystone", "mariadb-operator"]),
        "freezer": ServiceNode("freezer", "optional", ["keystone", "mariadb-operator"]),
        "gnocchi": ServiceNode("gnocchi", "optional", ["keystone", "ceilometer"]),
        "heat": ServiceNode("heat", "optional", ["keystone", "neutron", "mariadb-operator", "rabbitmq"]),
        "ironic": ServiceNode("ironic", "optional", ["keystone", "neutron", "glance", "mariadb-operator", "rabbitmq"]),
        "magnum": ServiceNode("magnum", "optional", ["keystone", "nova", "neutron", "heat", "mariadb-operator", "rabbitmq"]),
        "manila": ServiceNode("manila", "optional", ["keystone", "neutron", "mariadb-operator", "rabbitmq"]),
        "masakari": ServiceNode("masakari", "optional", ["keystone", "nova", "mariadb-operator", "rabbitmq"]),
        "octavia": ServiceNode("octavia", "optional", ["keystone", "neutron", "nova", "glance", "mariadb-operator", "rabbitmq"]),
        "trove": ServiceNode("trove", "optional", ["keystone", "nova", "neutron", "mariadb-operator", "rabbitmq"]),
        "zaqar": ServiceNode("zaqar", "optional", ["keystone", "mariadb-operator"]),
    }
    
    def __init__(self, services: List[str] = None):
        """Initialize dependency graph.
        
        Args:
            services: List of service names to include. If None, includes all services.
        """
        if services is None:
            self.services = list(self.SERVICE_DEPENDENCIES.keys())
        else:
            # Validate all services exist
            unknown = set(services) - set(self.SERVICE_DEPENDENCIES.keys())
            if unknown:
                raise ValueError(f"Unknown services: {unknown}")
            self.services = services
    
    def get_dependencies(self, service: str) -> List[str]:
        """Get direct dependencies for a service.
        
        Args:
            service: Service name
            
        Returns:
            List of service names this service depends on
            
        Raises:
            ValueError: If service is unknown
        """
        if service not in self.SERVICE_DEPENDENCIES:
            raise ValueError(f"Unknown service: {service}")
        return self.SERVICE_DEPENDENCIES[service].dependencies
    
    def get_category(self, service: str) -> str:
        """Get category for a service.
        
        Args:
            service: Service name
            
        Returns:
            Category: "infrastructure", "core", or "optional"
            
        Raises:
            ValueError: If service is unknown
        """
        if service not in self.SERVICE_DEPENDENCIES:
            raise ValueError(f"Unknown service: {service}")
        return self.SERVICE_DEPENDENCIES[service].category
    
    def topological_sort(self) -> List[str]:
        """Compute topological sort of services for upgrade order.
        
        Returns:
            List of service names in upgrade order (dependencies first)
            
        Raises:
            ValueError: If circular dependency detected
        """
        # Build adjacency list for services we're upgrading
        graph = {}
        in_degree = {}
        
        for service in self.services:
            graph[service] = []
            in_degree[service] = 0
        
        # Add edges for dependencies
        for service in self.services:
            deps = self.get_dependencies(service)
            for dep in deps:
                # Only add edge if dependency is in our service list
                if dep in self.services:
                    graph[dep].append(service)
                    in_degree[service] += 1
        
        # Kahn's algorithm for topological sort
        queue = [s for s in self.services if in_degree[s] == 0]
        result = []
        
        while queue:
            # Sort queue to ensure deterministic ordering
            queue.sort()
            node = queue.pop(0)
            result.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for circular dependencies
        if len(result) != len(self.services):
            unprocessed = set(self.services) - set(result)
            raise ValueError(f"Circular dependency detected involving: {unprocessed}")
        
        return result
    
    def get_upgrade_order(self, skip_optional: bool = False) -> List[str]:
        """Get services in upgrade order, optionally skipping optional services.
        
        Args:
            skip_optional: If True, exclude optional services
            
        Returns:
            List of service names in upgrade order
        """
        if skip_optional:
            # Filter to only infrastructure and core services
            filtered_services = [
                s for s in self.services
                if self.get_category(s) in ["infrastructure", "core"]
            ]
            graph = DependencyGraph(filtered_services)
            return graph.topological_sort()
        else:
            return self.topological_sort()
    
    def validate_dependencies(self) -> Dict[str, List[str]]:
        """Validate that all dependencies are available.
        
        Returns:
            Dictionary mapping services to their missing dependencies
        """
        missing = {}
        
        for service in self.services:
            deps = self.get_dependencies(service)
            missing_deps = [d for d in deps if d not in self.services]
            if missing_deps:
                missing[service] = missing_deps
        
        return missing
