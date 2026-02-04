"""OpenStack API endpoint checker for pre-upgrade validation."""

import requests
from typing import Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
import os


@dataclass
class EndpointStatus:
    """Represents the status of an API endpoint."""
    
    service: str
    endpoint_type: str  # public, internal, admin
    url: str
    reachable: bool
    status_code: Optional[int] = None
    response_time: Optional[float] = None  # in seconds
    error: Optional[str] = None


@dataclass
class EndpointReport:
    """Aggregated endpoint status report."""
    
    total_endpoints: int
    reachable: int
    unreachable: int
    endpoints: List[EndpointStatus]
    healthy: bool
    
    @property
    def summary(self) -> str:
        """Generate a summary string."""
        return (
            f"Total: {self.total_endpoints}, "
            f"Reachable: {self.reachable}, "
            f"Unreachable: {self.unreachable}"
        )


class EndpointChecker:
    """Checks OpenStack API endpoint connectivity."""
    
    def __init__(
        self,
        auth_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        project_name: Optional[str] = None,
        user_domain_name: str = "Default",
        project_domain_name: str = "Default",
        timeout: int = 10
    ):
        """
        Initialize the endpoint checker.
        
        Args:
            auth_url: Keystone authentication URL
            username: OpenStack username
            password: OpenStack password
            project_name: OpenStack project name
            user_domain_name: User domain name
            project_domain_name: Project domain name
            timeout: Request timeout in seconds
        """
        # Try to get credentials from environment if not provided
        self.auth_url = auth_url or os.getenv("OS_AUTH_URL")
        self.username = username or os.getenv("OS_USERNAME")
        self.password = password or os.getenv("OS_PASSWORD")
        self.project_name = project_name or os.getenv("OS_PROJECT_NAME")
        self.user_domain_name = user_domain_name or os.getenv("OS_USER_DOMAIN_NAME", "Default")
        self.project_domain_name = project_domain_name or os.getenv("OS_PROJECT_DOMAIN_NAME", "Default")
        self.timeout = timeout
        self.token = None
        self.catalog = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Keystone and get service catalog.
        
        Returns:
            True if authentication succeeded, False otherwise
        """
        if not all([self.auth_url, self.username, self.password, self.project_name]):
            raise ValueError(
                "Missing required credentials. Provide auth_url, username, "
                "password, and project_name either as arguments or environment variables."
            )
        
        auth_data = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": self.username,
                            "domain": {"name": self.user_domain_name},
                            "password": self.password
                        }
                    }
                },
                "scope": {
                    "project": {
                        "name": self.project_name,
                        "domain": {"name": self.project_domain_name}
                    }
                }
            }
        }
        
        try:
            # Keystone v3 auth endpoint
            auth_endpoint = f"{self.auth_url.rstrip('/')}/v3/auth/tokens"
            
            response = requests.post(
                auth_endpoint,
                json=auth_data,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                self.token = response.headers.get("X-Subject-Token")
                self.catalog = response.json()["token"]["catalog"]
                return True
            else:
                return False
                
        except Exception as e:
            raise RuntimeError(f"Authentication failed: {e}")
    
    def check_endpoint(self, url: str, service: str, endpoint_type: str) -> EndpointStatus:
        """
        Check if an endpoint is reachable.
        
        Args:
            url: Endpoint URL to check
            service: Service name (e.g., "keystone", "nova")
            endpoint_type: Endpoint type (public, internal, admin)
            
        Returns:
            EndpointStatus with check results
        """
        try:
            # Make a simple GET request to the endpoint
            # Most OpenStack APIs return version info on root path
            headers = {}
            if self.token:
                headers["X-Auth-Token"] = self.token
            
            import time
            start_time = time.time()
            
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                verify=False  # In production, should verify SSL
            )
            
            response_time = time.time() - start_time
            
            # Consider 200-299 and 300 (Multiple Choices) as success
            # Some services return 300 for version discovery
            reachable = response.status_code < 400
            
            return EndpointStatus(
                service=service,
                endpoint_type=endpoint_type,
                url=url,
                reachable=reachable,
                status_code=response.status_code,
                response_time=response_time,
                error=None if reachable else f"HTTP {response.status_code}"
            )
            
        except requests.exceptions.Timeout:
            return EndpointStatus(
                service=service,
                endpoint_type=endpoint_type,
                url=url,
                reachable=False,
                status_code=None,
                response_time=None,
                error="Timeout"
            )
        except requests.exceptions.ConnectionError as e:
            return EndpointStatus(
                service=service,
                endpoint_type=endpoint_type,
                url=url,
                reachable=False,
                status_code=None,
                response_time=None,
                error=f"Connection error: {str(e)[:100]}"
            )
        except Exception as e:
            return EndpointStatus(
                service=service,
                endpoint_type=endpoint_type,
                url=url,
                reachable=False,
                status_code=None,
                response_time=None,
                error=f"Error: {str(e)[:100]}"
            )
    
    def check_all_endpoints(
        self,
        endpoint_types: Optional[List[str]] = None
    ) -> EndpointReport:
        """
        Check all endpoints in the service catalog.
        
        Args:
            endpoint_types: List of endpoint types to check (public, internal, admin).
                          If None, checks all types.
        
        Returns:
            EndpointReport with aggregated results
        """
        if not self.catalog:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        if endpoint_types is None:
            endpoint_types = ["public", "internal", "admin"]
        
        endpoint_statuses = []
        
        for service in self.catalog:
            service_name = service.get("name", service.get("type", "unknown"))
            
            for endpoint in service.get("endpoints", []):
                interface = endpoint.get("interface")
                
                if interface in endpoint_types:
                    url = endpoint.get("url")
                    if url:
                        status = self.check_endpoint(url, service_name, interface)
                        endpoint_statuses.append(status)
        
        # Aggregate results
        reachable = sum(1 for e in endpoint_statuses if e.reachable)
        unreachable = len(endpoint_statuses) - reachable
        healthy = unreachable == 0
        
        return EndpointReport(
            total_endpoints=len(endpoint_statuses),
            reachable=reachable,
            unreachable=unreachable,
            endpoints=endpoint_statuses,
            healthy=healthy
        )
    
    def check_service_endpoints(
        self,
        service_name: str,
        endpoint_types: Optional[List[str]] = None
    ) -> EndpointReport:
        """
        Check endpoints for a specific service.
        
        Args:
            service_name: Name of the service to check
            endpoint_types: List of endpoint types to check
            
        Returns:
            EndpointReport with results for the service
        """
        if not self.catalog:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        if endpoint_types is None:
            endpoint_types = ["public", "internal", "admin"]
        
        endpoint_statuses = []
        
        for service in self.catalog:
            svc_name = service.get("name", service.get("type", "unknown"))
            
            if svc_name == service_name:
                for endpoint in service.get("endpoints", []):
                    interface = endpoint.get("interface")
                    
                    if interface in endpoint_types:
                        url = endpoint.get("url")
                        if url:
                            status = self.check_endpoint(url, service_name, interface)
                            endpoint_statuses.append(status)
        
        # Aggregate results
        reachable = sum(1 for e in endpoint_statuses if e.reachable)
        unreachable = len(endpoint_statuses) - reachable
        healthy = unreachable == 0
        
        return EndpointReport(
            total_endpoints=len(endpoint_statuses),
            reachable=reachable,
            unreachable=unreachable,
            endpoints=endpoint_statuses,
            healthy=healthy
        )
    
    def get_unreachable_endpoints(self, report: EndpointReport) -> List[EndpointStatus]:
        """
        Get list of unreachable endpoints from a report.
        
        Args:
            report: EndpointReport to analyze
            
        Returns:
            List of EndpointStatus for unreachable endpoints
        """
        return [e for e in report.endpoints if not e.reachable]
