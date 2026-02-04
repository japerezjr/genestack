"""Pre-upgrade validation orchestrator with failure handling."""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .pod_checker import PodStatusChecker
from .endpoint_checker import EndpointChecker
from .aggregator import HealthAggregator, HealthReport
from .resource_validator import ResourceValidator, ValidationReport


@dataclass
class ValidationFailure:
    """Represents a validation failure."""
    
    category: str  # "health", "resources", "backups", "jobs"
    severity: str  # "critical", "high", "medium", "low"
    description: str
    remediation: str
    details: Optional[str] = None


@dataclass
class PreUpgradeValidationReport:
    """Complete pre-upgrade validation report."""
    
    timestamp: datetime
    passed: bool
    health_report: Optional[HealthReport] = None
    resource_report: Optional[ValidationReport] = None
    failures: List[ValidationFailure] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def summary(self) -> str:
        """Generate a summary of the validation."""
        lines = []
        lines.append("=" * 70)
        lines.append("PRE-UPGRADE VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append(f"Timestamp: {self.timestamp.isoformat()}")
        lines.append(f"Status: {'✅ PASSED' if self.passed else '❌ FAILED'}")
        lines.append("")
        
        if self.failures:
            lines.append(f"Failures: {len(self.failures)}")
            critical = sum(1 for f in self.failures if f.severity == "critical")
            high = sum(1 for f in self.failures if f.severity == "high")
            medium = sum(1 for f in self.failures if f.severity == "medium")
            low = sum(1 for f in self.failures if f.severity == "low")
            
            lines.append(f"  Critical: {critical}")
            lines.append(f"  High: {high}")
            lines.append(f"  Medium: {medium}")
            lines.append(f"  Low: {low}")
            lines.append("")
        
        if self.warnings:
            lines.append(f"Warnings: {len(self.warnings)}")
            lines.append("")
        
        if not self.passed:
            lines.append("VALIDATION FAILED - UPGRADE CANNOT PROCEED")
            lines.append("")
            lines.append("The following issues must be resolved before upgrading:")
            lines.append("")
            
            for i, failure in enumerate(self.failures, 1):
                lines.append(f"{i}. [{failure.severity.upper()}] {failure.category}: {failure.description}")
                lines.append(f"   Remediation: {failure.remediation}")
                if failure.details:
                    lines.append(f"   Details: {failure.details}")
                lines.append("")
        else:
            lines.append("All validation checks passed. System is ready for upgrade.")
        
        lines.append("=" * 70)
        return "\n".join(lines)


class PreUpgradeValidator:
    """Orchestrates all pre-upgrade validation checks."""
    
    def __init__(
        self,
        in_cluster: bool = False,
        check_endpoints: bool = True,
        backup_path: Optional[str] = None,
        namespace: str = "openstack"
    ):
        """
        Initialize the pre-upgrade validator.
        
        Args:
            in_cluster: If True, use in-cluster Kubernetes config
            check_endpoints: Whether to check OpenStack API endpoints
            backup_path: Path to backup directory
            namespace: Kubernetes namespace to check
        """
        self.in_cluster = in_cluster
        self.check_endpoints = check_endpoints
        self.backup_path = backup_path or "/var/backups/openstack"
        self.namespace = namespace
        
        # Initialize checkers
        self.pod_checker = PodStatusChecker(in_cluster=in_cluster)
        self.endpoint_checker = EndpointChecker() if check_endpoints else None
        self.health_aggregator = HealthAggregator(
            pod_checker=self.pod_checker,
            endpoint_checker=self.endpoint_checker
        )
        self.resource_validator = ResourceValidator(in_cluster=in_cluster)
    
    def validate(self) -> PreUpgradeValidationReport:
        """
        Run all pre-upgrade validation checks.
        
        Returns:
            PreUpgradeValidationReport with results and failures
        """
        failures = []
        warnings = []
        
        # Check service health
        health_report = None
        try:
            health_report = self.health_aggregator.check_all_services(
                namespaces=[self.namespace],
                check_endpoints=self.check_endpoints
            )
            
            if not health_report.overall_healthy:
                for service_name in health_report.get_unhealthy_services():
                    service = health_report.get_service_health(service_name)
                    if service:
                        for issue in service.issues:
                            failures.append(ValidationFailure(
                                category="health",
                                severity="critical",
                                description=f"Service {service_name} is unhealthy: {issue}",
                                remediation="Ensure all services are running and healthy before upgrading"
                            ))
        except Exception as e:
            failures.append(ValidationFailure(
                category="health",
                severity="critical",
                description=f"Failed to check service health: {e}",
                remediation="Verify Kubernetes cluster is accessible and services are deployed"
            ))
        
        # Check resources and backups
        resource_report = None
        try:
            resource_report = self.resource_validator.validate_all(
                backup_path=self.backup_path,
                namespace=self.namespace
            )
            
            if not resource_report.passed:
                # Resource issues
                if not resource_report.resource_status.sufficient:
                    for issue in resource_report.resource_status.issues:
                        failures.append(ValidationFailure(
                            category="resources",
                            severity="high",
                            description=issue,
                            remediation="Free up cluster resources or add more nodes before upgrading"
                        ))
                
                # Backup issues
                if not resource_report.backup_status.backup_valid:
                    for issue in resource_report.backup_status.issues:
                        failures.append(ValidationFailure(
                            category="backups",
                            severity="critical",
                            description=issue,
                            remediation="Create fresh database backups before upgrading"
                        ))
                
                # Job issues
                if not resource_report.job_status.safe_to_upgrade:
                    for issue in resource_report.job_status.issues:
                        failures.append(ValidationFailure(
                            category="jobs",
                            severity="high",
                            description=issue,
                            remediation="Wait for active jobs and migrations to complete before upgrading"
                        ))
        except Exception as e:
            failures.append(ValidationFailure(
                category="resources",
                severity="critical",
                description=f"Failed to validate resources: {e}",
                remediation="Verify Kubernetes cluster is accessible"
            ))
        
        # Determine overall pass/fail
        passed = len(failures) == 0
        
        return PreUpgradeValidationReport(
            timestamp=datetime.now(),
            passed=passed,
            health_report=health_report,
            resource_report=resource_report,
            failures=failures,
            warnings=warnings
        )
    
    def validate_and_halt_on_failure(self) -> PreUpgradeValidationReport:
        """
        Run validation and raise exception if validation fails.
        
        Returns:
            PreUpgradeValidationReport if validation passes
            
        Raises:
            ValidationError if validation fails
        """
        report = self.validate()
        
        if not report.passed:
            raise ValidationError(
                "Pre-upgrade validation failed. See report for details.",
                report=report
            )
        
        return report
    
    def generate_detailed_report(
        self,
        output_format: str = "text"
    ) -> str:
        """
        Generate a detailed validation report.
        
        Args:
            output_format: Output format (text, json, markdown)
            
        Returns:
            Formatted report string
        """
        report = self.validate()
        
        if output_format == "text":
            return self._format_text_report(report)
        elif output_format == "json":
            return self._format_json_report(report)
        elif output_format == "markdown":
            return self._format_markdown_report(report)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _format_text_report(self, report: PreUpgradeValidationReport) -> str:
        """Format report as plain text."""
        lines = [report.summary]
        
        if report.health_report:
            lines.append("\n" + "=" * 70)
            lines.append("SERVICE HEALTH")
            lines.append("=" * 70)
            lines.append(report.health_report.summary)
        
        if report.resource_report:
            lines.append("\n" + "=" * 70)
            lines.append("RESOURCE VALIDATION")
            lines.append("=" * 70)
            lines.append(report.resource_report.summary)
        
        return "\n".join(lines)
    
    def _format_json_report(self, report: PreUpgradeValidationReport) -> str:
        """Format report as JSON."""
        import json
        
        data = {
            "timestamp": report.timestamp.isoformat(),
            "passed": report.passed,
            "failures": [
                {
                    "category": f.category,
                    "severity": f.severity,
                    "description": f.description,
                    "remediation": f.remediation,
                    "details": f.details
                }
                for f in report.failures
            ],
            "warnings": report.warnings
        }
        
        if report.health_report:
            data["health"] = {
                "overall_healthy": report.health_report.overall_healthy,
                "unhealthy_services": report.health_report.get_unhealthy_services()
            }
        
        if report.resource_report:
            data["resources"] = {
                "passed": report.resource_report.passed,
                "cpu_utilization": report.resource_report.resource_status.cpu_utilization,
                "memory_utilization": report.resource_report.resource_status.memory_utilization,
                "backup_valid": report.resource_report.backup_status.backup_valid,
                "safe_to_upgrade": report.resource_report.job_status.safe_to_upgrade
            }
        
        return json.dumps(data, indent=2)
    
    def _format_markdown_report(self, report: PreUpgradeValidationReport) -> str:
        """Format report as Markdown."""
        lines = []
        lines.append("# Pre-Upgrade Validation Report")
        lines.append("")
        lines.append(f"**Timestamp:** {report.timestamp.isoformat()}")
        lines.append("")
        lines.append(f"**Status:** {'✅ PASSED' if report.passed else '❌ FAILED'}")
        lines.append("")
        
        if report.failures:
            lines.append("## Failures")
            lines.append("")
            
            for failure in report.failures:
                lines.append(f"### [{failure.severity.upper()}] {failure.category}")
                lines.append("")
                lines.append(f"**Description:** {failure.description}")
                lines.append("")
                lines.append(f"**Remediation:** {failure.remediation}")
                lines.append("")
                if failure.details:
                    lines.append(f"**Details:** {failure.details}")
                    lines.append("")
        
        if report.warnings:
            lines.append("## Warnings")
            lines.append("")
            for warning in report.warnings:
                lines.append(f"- {warning}")
            lines.append("")
        
        if report.health_report:
            lines.append("## Service Health")
            lines.append("")
            lines.append(f"**Overall:** {'✅ Healthy' if report.health_report.overall_healthy else '❌ Unhealthy'}")
            lines.append("")
        
        if report.resource_report:
            lines.append("## Resource Validation")
            lines.append("")
            lines.append(f"**CPU Utilization:** {report.resource_report.resource_status.cpu_utilization:.1f}%")
            lines.append(f"**Memory Utilization:** {report.resource_report.resource_status.memory_utilization:.1f}%")
            lines.append(f"**Backup Valid:** {'✅ Yes' if report.resource_report.backup_status.backup_valid else '❌ No'}")
            lines.append(f"**Safe to Upgrade:** {'✅ Yes' if report.resource_report.job_status.safe_to_upgrade else '❌ No'}")
            lines.append("")
        
        return "\n".join(lines)


class ValidationError(Exception):
    """Exception raised when pre-upgrade validation fails."""
    
    def __init__(self, message: str, report: PreUpgradeValidationReport):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            report: Validation report with details
        """
        super().__init__(message)
        self.report = report
