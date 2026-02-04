"""Rollback verifier for verifying system health after rollback.

This module handles verification that all services return to healthy state
after a rollback operation.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

from health.aggregator import HealthAggregator, HealthReport
from health.pod_checker import PodStatusChecker
from health.endpoint_checker import EndpointChecker


@dataclass
class RollbackVerificationResult:
    """Result of rollback verification."""
    success: bool
    timestamp: datetime
    health_report: HealthReport
    pod_status_ok: bool
    endpoints_ok: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class RollbackReport:
    """Comprehensive rollback report."""
    backup_id: str
    rollback_timestamp: datetime
    verification_result: RollbackVerificationResult
    components_restored: List[str]
    services_verified: List[str]
    summary: str = ""
    
    def __post_init__(self):
        """Generate summary after initialization."""
        self._generate_summary()
    
    def _generate_summary(self):
        """Generate a summary of the rollback report."""
        status = "SUCCESSFUL" if self.verification_result.success else "FAILED"
        
        self.summary = (
            f"Rollback Report\n"
            f"{'=' * 60}\n"
            f"Backup ID: {self.backup_id}\n"
            f"Timestamp: {self.rollback_timestamp.isoformat()}\n"
            f"Status: {status}\n"
            f"\n"
            f"Components Restored: {', '.join(self.components_restored)}\n"
            f"Services Verified: {len(self.services_verified)}\n"
            f"\n"
            f"Verification Results:\n"
            f"  Pod Status: {'OK' if self.verification_result.pod_status_ok else 'FAILED'}\n"
            f"  Endpoints: {'OK' if self.verification_result.endpoints_ok else 'FAILED'}\n"
            f"  Overall Health: {'HEALTHY' if self.verification_result.health_report.overall_healthy else 'UNHEALTHY'}\n"
        )
        
        if self.verification_result.issues:
            self.summary += "\nIssues:\n"
            for issue in self.verification_result.issues:
                self.summary += f"  - {issue}\n"
        
        if self.verification_result.warnings:
            self.summary += "\nWarnings:\n"
            for warning in self.verification_result.warnings:
                self.summary += f"  - {warning}\n"


class RollbackVerifier:
    """Verifies system health after rollback."""
    
    def __init__(
        self,
        health_aggregator: Optional[HealthAggregator] = None,
        pod_checker: Optional[PodStatusChecker] = None,
        endpoint_checker: Optional[EndpointChecker] = None
    ):
        """Initialize rollback verifier.
        
        Args:
            health_aggregator: HealthAggregator instance (created if not provided)
            pod_checker: PodStatusChecker instance (created if not provided)
            endpoint_checker: EndpointChecker instance (created if not provided)
        """
        self.pod_checker = pod_checker or PodStatusChecker()
        self.endpoint_checker = endpoint_checker
        self.health_aggregator = health_aggregator or HealthAggregator(
            pod_checker=self.pod_checker,
            endpoint_checker=self.endpoint_checker
        )
    
    def verify_rollback(
        self,
        namespaces: Optional[List[str]] = None,
        check_endpoints: bool = True
    ) -> RollbackVerificationResult:
        """Verify system health after rollback.
        
        Args:
            namespaces: List of namespaces to check (default: ["openstack"])
            check_endpoints: Whether to check API endpoints
            
        Returns:
            RollbackVerificationResult with verification status
        """
        timestamp = datetime.now()
        issues = []
        warnings = []
        
        if namespaces is None:
            namespaces = ["openstack"]
        
        # Check overall health
        health_report = self.health_aggregator.check_all_services(
            namespaces=namespaces,
            check_endpoints=check_endpoints
        )
        
        # Verify pod status
        pod_status_ok = True
        for namespace in namespaces:
            try:
                pod_report = self.pod_checker.check_namespace(namespace)
                if not pod_report.healthy:
                    pod_status_ok = False
                    issues.append(
                        f"Unhealthy pods in {namespace}: "
                        f"{pod_report.failed} failed, "
                        f"{pod_report.pending} pending"
                    )
            except Exception as e:
                pod_status_ok = False
                issues.append(f"Failed to check pods in {namespace}: {e}")
        
        # Verify endpoints
        endpoints_ok = True
        if check_endpoints and self.endpoint_checker:
            try:
                if not self.endpoint_checker.catalog:
                    self.endpoint_checker.authenticate()
                
                endpoint_report = self.endpoint_checker.check_all_endpoints()
                if not endpoint_report.healthy:
                    endpoints_ok = False
                    issues.append(
                        f"Unreachable endpoints: {endpoint_report.unreachable} "
                        f"out of {endpoint_report.total_endpoints}"
                    )
            except Exception as e:
                endpoints_ok = False
                warnings.append(f"Failed to check endpoints: {e}")
        
        # Overall success if health report is healthy and no critical issues
        success = (
            health_report.overall_healthy and
            pod_status_ok and
            (endpoints_ok or not check_endpoints)
        )
        
        return RollbackVerificationResult(
            success=success,
            timestamp=timestamp,
            health_report=health_report,
            pod_status_ok=pod_status_ok,
            endpoints_ok=endpoints_ok,
            issues=issues,
            warnings=warnings
        )
    
    def verify_service_health(
        self,
        service_name: str,
        namespace: str = "openstack",
        check_endpoints: bool = True
    ) -> RollbackVerificationResult:
        """Verify health of a specific service after rollback.
        
        Args:
            service_name: Name of the service to verify
            namespace: Kubernetes namespace
            check_endpoints: Whether to check API endpoints
            
        Returns:
            RollbackVerificationResult with verification status
        """
        timestamp = datetime.now()
        issues = []
        warnings = []
        
        # Check service health
        service_health = self.health_aggregator.check_service_health(
            service_name=service_name,
            namespace=namespace,
            check_endpoints=check_endpoints
        )
        
        # Create a health report with just this service
        from health.aggregator import HealthReport
        health_report = HealthReport(
            timestamp=timestamp,
            overall_healthy=service_health.healthy,
            services={service_name: service_health}
        )
        
        # Check pod status
        pod_status_ok = True
        if service_health.pod_status:
            if not service_health.pod_status.healthy:
                pod_status_ok = False
                issues.append(
                    f"Unhealthy pods for {service_name}: "
                    f"{service_health.pod_status.failed} failed, "
                    f"{service_health.pod_status.pending} pending"
                )
        
        # Check endpoint status
        endpoints_ok = True
        if service_health.endpoint_status:
            if not service_health.endpoint_status.healthy:
                endpoints_ok = False
                issues.append(
                    f"Unreachable endpoints for {service_name}: "
                    f"{service_health.endpoint_status.unreachable} "
                    f"out of {service_health.endpoint_status.total_endpoints}"
                )
        
        success = service_health.healthy and pod_status_ok and endpoints_ok
        
        return RollbackVerificationResult(
            success=success,
            timestamp=timestamp,
            health_report=health_report,
            pod_status_ok=pod_status_ok,
            endpoints_ok=endpoints_ok,
            issues=issues,
            warnings=warnings
        )
    
    def generate_rollback_report(
        self,
        backup_id: str,
        rollback_timestamp: datetime,
        components_restored: List[str],
        verification_result: RollbackVerificationResult,
        services_verified: Optional[List[str]] = None
    ) -> RollbackReport:
        """Generate a comprehensive rollback report.
        
        Args:
            backup_id: ID of the backup that was restored
            rollback_timestamp: When the rollback occurred
            components_restored: List of components that were restored
            verification_result: Result of rollback verification
            services_verified: List of services that were verified
            
        Returns:
            RollbackReport with complete rollback information
        """
        if services_verified is None:
            services_verified = list(verification_result.health_report.services.keys())
        
        return RollbackReport(
            backup_id=backup_id,
            rollback_timestamp=rollback_timestamp,
            verification_result=verification_result,
            components_restored=components_restored,
            services_verified=services_verified
        )
    
    def format_report(
        self,
        report: RollbackReport,
        output_format: str = "text"
    ) -> str:
        """Format a rollback report.
        
        Args:
            report: RollbackReport to format
            output_format: Output format (text, json, markdown)
            
        Returns:
            Formatted report string
        """
        if output_format == "text":
            return self._format_text_report(report)
        elif output_format == "json":
            return self._format_json_report(report)
        elif output_format == "markdown":
            return self._format_markdown_report(report)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _format_text_report(self, report: RollbackReport) -> str:
        """Format report as plain text."""
        output = []
        output.append("=" * 60)
        output.append("ROLLBACK REPORT")
        output.append("=" * 60)
        output.append(f"Backup ID: {report.backup_id}")
        output.append(f"Rollback Timestamp: {report.rollback_timestamp.isoformat()}")
        output.append(f"Verification Timestamp: {report.verification_result.timestamp.isoformat()}")
        output.append("")
        output.append(f"Status: {'✓ SUCCESSFUL' if report.verification_result.success else '✗ FAILED'}")
        output.append("")
        
        output.append("Components Restored:")
        for component in report.components_restored:
            output.append(f"  - {component}")
        output.append("")
        
        output.append("Verification Results:")
        output.append(f"  Pod Status: {'✓ OK' if report.verification_result.pod_status_ok else '✗ FAILED'}")
        output.append(f"  Endpoints: {'✓ OK' if report.verification_result.endpoints_ok else '✗ FAILED'}")
        output.append(f"  Overall Health: {'✓ HEALTHY' if report.verification_result.health_report.overall_healthy else '✗ UNHEALTHY'}")
        output.append("")
        
        if report.verification_result.issues:
            output.append("Issues:")
            for issue in report.verification_result.issues:
                output.append(f"  - {issue}")
            output.append("")
        
        if report.verification_result.warnings:
            output.append("Warnings:")
            for warning in report.verification_result.warnings:
                output.append(f"  - {warning}")
            output.append("")
        
        output.append("Services Verified:")
        for service in report.services_verified:
            service_health = report.verification_result.health_report.services.get(service)
            if service_health:
                status = "✓" if service_health.healthy else "✗"
                output.append(f"  {status} {service}")
        
        output.append("")
        output.append("=" * 60)
        
        return "\n".join(output)
    
    def _format_json_report(self, report: RollbackReport) -> str:
        """Format report as JSON."""
        import json
        
        data = {
            "backup_id": report.backup_id,
            "rollback_timestamp": report.rollback_timestamp.isoformat(),
            "verification_timestamp": report.verification_result.timestamp.isoformat(),
            "success": report.verification_result.success,
            "components_restored": report.components_restored,
            "verification": {
                "pod_status_ok": report.verification_result.pod_status_ok,
                "endpoints_ok": report.verification_result.endpoints_ok,
                "overall_healthy": report.verification_result.health_report.overall_healthy
            },
            "issues": report.verification_result.issues,
            "warnings": report.verification_result.warnings,
            "services": {}
        }
        
        for service_name, service_health in report.verification_result.health_report.services.items():
            data["services"][service_name] = {
                "healthy": service_health.healthy,
                "issues": service_health.issues
            }
        
        return json.dumps(data, indent=2)
    
    def _format_markdown_report(self, report: RollbackReport) -> str:
        """Format report as Markdown."""
        output = []
        output.append("# Rollback Report")
        output.append("")
        output.append(f"**Backup ID:** {report.backup_id}")
        output.append(f"**Rollback Timestamp:** {report.rollback_timestamp.isoformat()}")
        output.append(f"**Verification Timestamp:** {report.verification_result.timestamp.isoformat()}")
        output.append("")
        
        status_icon = "✅" if report.verification_result.success else "❌"
        status_text = "SUCCESSFUL" if report.verification_result.success else "FAILED"
        output.append(f"**Status:** {status_icon} {status_text}")
        output.append("")
        
        output.append("## Components Restored")
        output.append("")
        for component in report.components_restored:
            output.append(f"- {component}")
        output.append("")
        
        output.append("## Verification Results")
        output.append("")
        pod_icon = "✅" if report.verification_result.pod_status_ok else "❌"
        endpoint_icon = "✅" if report.verification_result.endpoints_ok else "❌"
        health_icon = "✅" if report.verification_result.health_report.overall_healthy else "❌"
        
        output.append(f"- **Pod Status:** {pod_icon}")
        output.append(f"- **Endpoints:** {endpoint_icon}")
        output.append(f"- **Overall Health:** {health_icon}")
        output.append("")
        
        if report.verification_result.issues:
            output.append("## Issues")
            output.append("")
            for issue in report.verification_result.issues:
                output.append(f"- {issue}")
            output.append("")
        
        if report.verification_result.warnings:
            output.append("## Warnings")
            output.append("")
            for warning in report.verification_result.warnings:
                output.append(f"- {warning}")
            output.append("")
        
        output.append("## Services Verified")
        output.append("")
        for service in report.services_verified:
            service_health = report.verification_result.health_report.services.get(service)
            if service_health:
                icon = "✅" if service_health.healthy else "❌"
                output.append(f"- {icon} {service}")
        output.append("")
        
        return "\n".join(output)
