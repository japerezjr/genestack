"""Service health aggregation for pre-upgrade validation."""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .pod_checker import PodStatusReport, PodStatusChecker
from .endpoint_checker import EndpointReport, EndpointChecker


@dataclass
class ServiceHealth:
    """Health status for a single service."""
    
    service_name: str
    pod_status: Optional[PodStatusReport] = None
    endpoint_status: Optional[EndpointReport] = None
    healthy: bool = False
    issues: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate overall health after initialization."""
        self._calculate_health()
    
    def _calculate_health(self):
        """Calculate overall health based on pod and endpoint status."""
        self.issues = []
        
        # Check pod health
        if self.pod_status:
            if not self.pod_status.healthy:
                self.issues.append(
                    f"Unhealthy pods: {self.pod_status.failed} failed, "
                    f"{self.pod_status.pending} pending, "
                    f"{self.pod_status.unknown} unknown"
                )
        
        # Check endpoint health
        if self.endpoint_status:
            if not self.endpoint_status.healthy:
                self.issues.append(
                    f"Unreachable endpoints: {self.endpoint_status.unreachable} "
                    f"out of {self.endpoint_status.total_endpoints}"
                )
        
        # Service is healthy if both checks pass (or are not performed)
        pod_healthy = self.pod_status.healthy if self.pod_status else True
        endpoint_healthy = self.endpoint_status.healthy if self.endpoint_status else True
        
        self.healthy = pod_healthy and endpoint_healthy


@dataclass
class HealthReport:
    """Aggregated health report for all services."""
    
    timestamp: datetime
    overall_healthy: bool
    services: Dict[str, ServiceHealth]
    summary: str = ""
    
    def __post_init__(self):
        """Generate summary after initialization."""
        self._generate_summary()
    
    def _generate_summary(self):
        """Generate a summary of the health report."""
        total_services = len(self.services)
        healthy_services = sum(1 for s in self.services.values() if s.healthy)
        unhealthy_services = total_services - healthy_services
        
        self.summary = (
            f"Overall Health: {'HEALTHY' if self.overall_healthy else 'UNHEALTHY'}\n"
            f"Total Services: {total_services}\n"
            f"Healthy: {healthy_services}\n"
            f"Unhealthy: {unhealthy_services}\n"
        )
        
        if not self.overall_healthy:
            self.summary += "\nIssues:\n"
            for service_name, service in self.services.items():
                if not service.healthy:
                    self.summary += f"\n{service_name}:\n"
                    for issue in service.issues:
                        self.summary += f"  - {issue}\n"
    
    def get_unhealthy_services(self) -> List[str]:
        """Get list of unhealthy service names."""
        return [
            name for name, service in self.services.items()
            if not service.healthy
        ]
    
    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """Get health status for a specific service."""
        return self.services.get(service_name)


class HealthAggregator:
    """Aggregates health checks from multiple sources."""
    
    def __init__(
        self,
        pod_checker: Optional[PodStatusChecker] = None,
        endpoint_checker: Optional[EndpointChecker] = None
    ):
        """
        Initialize the health aggregator.
        
        Args:
            pod_checker: PodStatusChecker instance (created if not provided)
            endpoint_checker: EndpointChecker instance (created if not provided)
        """
        self.pod_checker = pod_checker or PodStatusChecker()
        self.endpoint_checker = endpoint_checker
    
    def check_service_health(
        self,
        service_name: str,
        namespace: str = "openstack",
        check_endpoints: bool = True
    ) -> ServiceHealth:
        """
        Check health of a single service.
        
        Args:
            service_name: Name of the service to check
            namespace: Kubernetes namespace
            check_endpoints: Whether to check API endpoints
            
        Returns:
            ServiceHealth with aggregated status
        """
        # Check pod status
        pod_status = self.pod_checker.check_namespace(namespace)
        
        # Check endpoint status if requested and checker is available
        endpoint_status = None
        if check_endpoints and self.endpoint_checker:
            try:
                if not self.endpoint_checker.catalog:
                    self.endpoint_checker.authenticate()
                endpoint_status = self.endpoint_checker.check_service_endpoints(
                    service_name
                )
            except Exception:
                # If endpoint check fails, continue without it
                pass
        
        return ServiceHealth(
            service_name=service_name,
            pod_status=pod_status,
            endpoint_status=endpoint_status
        )
    
    def check_all_services(
        self,
        namespaces: Optional[List[str]] = None,
        check_endpoints: bool = True
    ) -> HealthReport:
        """
        Check health of all services across namespaces.
        
        Args:
            namespaces: List of namespaces to check (default: ["openstack"])
            check_endpoints: Whether to check API endpoints
            
        Returns:
            HealthReport with aggregated status
        """
        if namespaces is None:
            namespaces = ["openstack"]
        
        services = {}
        
        # Check pod status for each namespace
        for namespace in namespaces:
            try:
                pod_status = self.pod_checker.check_namespace(namespace)
                
                # Create a service health entry for this namespace
                services[namespace] = ServiceHealth(
                    service_name=namespace,
                    pod_status=pod_status,
                    endpoint_status=None
                )
            except Exception as e:
                # If check fails, mark as unhealthy
                services[namespace] = ServiceHealth(
                    service_name=namespace,
                    pod_status=None,
                    endpoint_status=None,
                    healthy=False
                )
                services[namespace].issues.append(f"Failed to check pods: {e}")
        
        # Check endpoint status if requested
        if check_endpoints and self.endpoint_checker:
            try:
                if not self.endpoint_checker.catalog:
                    self.endpoint_checker.authenticate()
                
                endpoint_report = self.endpoint_checker.check_all_endpoints()
                
                # Add endpoint status to the report
                services["endpoints"] = ServiceHealth(
                    service_name="endpoints",
                    pod_status=None,
                    endpoint_status=endpoint_report
                )
            except Exception as e:
                # If endpoint check fails, add as unhealthy service
                services["endpoints"] = ServiceHealth(
                    service_name="endpoints",
                    pod_status=None,
                    endpoint_status=None,
                    healthy=False
                )
                services["endpoints"].issues.append(f"Failed to check endpoints: {e}")
        
        # Determine overall health
        overall_healthy = all(s.healthy for s in services.values())
        
        return HealthReport(
            timestamp=datetime.now(),
            overall_healthy=overall_healthy,
            services=services
        )
    
    def check_openstack_health(
        self,
        check_endpoints: bool = True
    ) -> HealthReport:
        """
        Check health of OpenStack deployment.
        
        This is a convenience method that checks the standard OpenStack namespace.
        
        Args:
            check_endpoints: Whether to check API endpoints
            
        Returns:
            HealthReport with aggregated status
        """
        return self.check_all_services(
            namespaces=["openstack"],
            check_endpoints=check_endpoints
        )
    
    def generate_health_report(
        self,
        namespaces: Optional[List[str]] = None,
        check_endpoints: bool = True,
        output_format: str = "text"
    ) -> str:
        """
        Generate a formatted health report.
        
        Args:
            namespaces: List of namespaces to check
            check_endpoints: Whether to check API endpoints
            output_format: Output format (text, json, markdown)
            
        Returns:
            Formatted health report string
        """
        report = self.check_all_services(namespaces, check_endpoints)
        
        if output_format == "text":
            return self._format_text_report(report)
        elif output_format == "json":
            return self._format_json_report(report)
        elif output_format == "markdown":
            return self._format_markdown_report(report)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _format_text_report(self, report: HealthReport) -> str:
        """Format report as plain text."""
        output = []
        output.append("=" * 60)
        output.append("OpenStack Health Report")
        output.append("=" * 60)
        output.append(f"Timestamp: {report.timestamp.isoformat()}")
        output.append("")
        output.append(report.summary)
        
        if not report.overall_healthy:
            output.append("\nDetailed Issues:")
            output.append("-" * 60)
            
            for service_name, service in report.services.items():
                if not service.healthy:
                    output.append(f"\n{service_name}:")
                    
                    if service.pod_status:
                        output.append(f"  Pods: {service.pod_status.summary}")
                    
                    if service.endpoint_status:
                        output.append(f"  Endpoints: {service.endpoint_status.summary}")
                    
                    for issue in service.issues:
                        output.append(f"  Issue: {issue}")
        
        output.append("\n" + "=" * 60)
        return "\n".join(output)
    
    def _format_json_report(self, report: HealthReport) -> str:
        """Format report as JSON."""
        import json
        
        data = {
            "timestamp": report.timestamp.isoformat(),
            "overall_healthy": report.overall_healthy,
            "services": {}
        }
        
        for service_name, service in report.services.items():
            data["services"][service_name] = {
                "healthy": service.healthy,
                "issues": service.issues
            }
            
            if service.pod_status:
                data["services"][service_name]["pods"] = {
                    "total": service.pod_status.total_pods,
                    "running": service.pod_status.running,
                    "pending": service.pod_status.pending,
                    "failed": service.pod_status.failed,
                    "healthy": service.pod_status.healthy
                }
            
            if service.endpoint_status:
                data["services"][service_name]["endpoints"] = {
                    "total": service.endpoint_status.total_endpoints,
                    "reachable": service.endpoint_status.reachable,
                    "unreachable": service.endpoint_status.unreachable,
                    "healthy": service.endpoint_status.healthy
                }
        
        return json.dumps(data, indent=2)
    
    def _format_markdown_report(self, report: HealthReport) -> str:
        """Format report as Markdown."""
        output = []
        output.append("# OpenStack Health Report")
        output.append("")
        output.append(f"**Timestamp:** {report.timestamp.isoformat()}")
        output.append("")
        output.append(f"**Overall Status:** {'✅ HEALTHY' if report.overall_healthy else '❌ UNHEALTHY'}")
        output.append("")
        
        output.append("## Summary")
        output.append("")
        output.append(f"- Total Services: {len(report.services)}")
        output.append(f"- Healthy: {sum(1 for s in report.services.values() if s.healthy)}")
        output.append(f"- Unhealthy: {sum(1 for s in report.services.values() if not s.healthy)}")
        output.append("")
        
        if not report.overall_healthy:
            output.append("## Issues")
            output.append("")
            
            for service_name, service in report.services.items():
                if not service.healthy:
                    output.append(f"### {service_name}")
                    output.append("")
                    
                    if service.pod_status:
                        output.append(f"**Pods:** {service.pod_status.summary}")
                        output.append("")
                    
                    if service.endpoint_status:
                        output.append(f"**Endpoints:** {service.endpoint_status.summary}")
                        output.append("")
                    
                    if service.issues:
                        output.append("**Issues:**")
                        for issue in service.issues:
                            output.append(f"- {issue}")
                        output.append("")
        
        return "\n".join(output)
