"""Summary report generation for upgrade operations."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import json


@dataclass
class VersionChange:
    """Represents a version change."""
    chart_name: str
    old_version: str
    new_version: str
    timestamp: str


@dataclass
class ConfigChange:
    """Represents a configuration change."""
    file_path: str
    changes: Dict[str, Any]
    timestamp: str


@dataclass
class Issue:
    """Represents an issue encountered during upgrade."""
    severity: str
    component: str
    description: str
    timestamp: str
    resolved: bool = False


@dataclass
class UpgradeSummary:
    """Summary of an upgrade operation."""
    start_time: datetime
    end_time: Optional[datetime] = None
    version_changes: List[VersionChange] = field(default_factory=list)
    config_changes: List[ConfigChange] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    services_upgraded: List[str] = field(default_factory=list)
    services_failed: List[str] = field(default_factory=list)
    rollback_performed: bool = False
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate upgrade duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def total_version_changes(self) -> int:
        """Count of version changes."""
        return len(self.version_changes)
    
    @property
    def total_config_changes(self) -> int:
        """Count of configuration changes."""
        return len(self.config_changes)
    
    @property
    def total_issues(self) -> int:
        """Count of issues encountered."""
        return len(self.issues)
    
    @property
    def critical_issues(self) -> List[Issue]:
        """Get critical issues."""
        return [i for i in self.issues if i.severity == "critical"]
    
    @property
    def success(self) -> bool:
        """Determine if upgrade was successful."""
        return (
            len(self.services_failed) == 0 and
            len(self.critical_issues) == 0 and
            not self.rollback_performed
        )


class SummaryReportGenerator:
    """Generates summary reports for upgrade operations.
    
    Aggregates version changes, configuration changes, duration,
    and issues encountered during the upgrade process.
    """
    
    def __init__(self):
        """Initialize the report generator."""
        self.summary = UpgradeSummary(start_time=datetime.now())
    
    def start_upgrade(self) -> None:
        """Mark the start of an upgrade."""
        self.summary.start_time = datetime.now()
    
    def end_upgrade(self) -> None:
        """Mark the end of an upgrade."""
        self.summary.end_time = datetime.now()
    
    def add_version_change(
        self,
        chart_name: str,
        old_version: str,
        new_version: str
    ) -> None:
        """Add a version change to the summary.
        
        Args:
            chart_name: Name of the chart
            old_version: Previous version
            new_version: New version
        """
        change = VersionChange(
            chart_name=chart_name,
            old_version=old_version,
            new_version=new_version,
            timestamp=datetime.now().isoformat()
        )
        self.summary.version_changes.append(change)
    
    def add_config_change(
        self,
        file_path: str,
        changes: Dict[str, Any]
    ) -> None:
        """Add a configuration change to the summary.
        
        Args:
            file_path: Path to configuration file
            changes: Dictionary of changes made
        """
        change = ConfigChange(
            file_path=file_path,
            changes=changes,
            timestamp=datetime.now().isoformat()
        )
        self.summary.config_changes.append(change)
    
    def add_issue(
        self,
        severity: str,
        component: str,
        description: str,
        resolved: bool = False
    ) -> None:
        """Add an issue to the summary.
        
        Args:
            severity: Issue severity (critical, high, medium, low)
            component: Component where issue occurred
            description: Description of the issue
            resolved: Whether the issue was resolved
        """
        issue = Issue(
            severity=severity,
            component=component,
            description=description,
            timestamp=datetime.now().isoformat(),
            resolved=resolved
        )
        self.summary.issues.append(issue)
    
    def add_service_upgraded(self, service_name: str) -> None:
        """Mark a service as successfully upgraded.
        
        Args:
            service_name: Name of the service
        """
        if service_name not in self.summary.services_upgraded:
            self.summary.services_upgraded.append(service_name)
    
    def add_service_failed(self, service_name: str) -> None:
        """Mark a service upgrade as failed.
        
        Args:
            service_name: Name of the service
        """
        if service_name not in self.summary.services_failed:
            self.summary.services_failed.append(service_name)
    
    def mark_rollback(self) -> None:
        """Mark that a rollback was performed."""
        self.summary.rollback_performed = True
    
    def generate_text_report(self) -> str:
        """Generate a human-readable text report.
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("OpenStack Upgrade Summary Report")
        lines.append("=" * 80)
        lines.append("")
        
        # Overview
        lines.append("OVERVIEW")
        lines.append("-" * 80)
        lines.append(f"Start Time: {self.summary.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if self.summary.end_time:
            lines.append(f"End Time: {self.summary.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Duration: {self._format_duration(self.summary.duration)}")
        lines.append(f"Status: {'SUCCESS' if self.summary.success else 'FAILED'}")
        if self.summary.rollback_performed:
            lines.append("Rollback: PERFORMED")
        lines.append("")
        
        # Version Changes
        lines.append("VERSION CHANGES")
        lines.append("-" * 80)
        lines.append(f"Total Changes: {self.summary.total_version_changes}")
        if self.summary.version_changes:
            lines.append("")
            for change in self.summary.version_changes:
                lines.append(f"  • {change.chart_name}")
                lines.append(f"    {change.old_version} → {change.new_version}")
        else:
            lines.append("  No version changes")
        lines.append("")
        
        # Configuration Changes
        lines.append("CONFIGURATION CHANGES")
        lines.append("-" * 80)
        lines.append(f"Total Changes: {self.summary.total_config_changes}")
        if self.summary.config_changes:
            lines.append("")
            for change in self.summary.config_changes:
                lines.append(f"  • {change.file_path}")
                for key, value in change.changes.items():
                    lines.append(f"    - {key}: {value}")
        else:
            lines.append("  No configuration changes")
        lines.append("")
        
        # Services
        lines.append("SERVICES")
        lines.append("-" * 80)
        lines.append(f"Successfully Upgraded: {len(self.summary.services_upgraded)}")
        if self.summary.services_upgraded:
            for service in self.summary.services_upgraded:
                lines.append(f"  ✓ {service}")
        
        if self.summary.services_failed:
            lines.append("")
            lines.append(f"Failed: {len(self.summary.services_failed)}")
            for service in self.summary.services_failed:
                lines.append(f"  ✗ {service}")
        lines.append("")
        
        # Issues
        lines.append("ISSUES ENCOUNTERED")
        lines.append("-" * 80)
        lines.append(f"Total Issues: {self.summary.total_issues}")
        
        if self.summary.issues:
            # Group by severity
            by_severity = {}
            for issue in self.summary.issues:
                if issue.severity not in by_severity:
                    by_severity[issue.severity] = []
                by_severity[issue.severity].append(issue)
            
            for severity in ["critical", "high", "medium", "low"]:
                if severity in by_severity:
                    lines.append("")
                    lines.append(f"{severity.upper()} ({len(by_severity[severity])})")
                    for issue in by_severity[severity]:
                        status = "✓" if issue.resolved else "✗"
                        lines.append(f"  {status} [{issue.component}] {issue.description}")
        else:
            lines.append("  No issues encountered")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def generate_json_report(self) -> Dict[str, Any]:
        """Generate a JSON report.
        
        Returns:
            Dictionary suitable for JSON serialization
        """
        return {
            "start_time": self.summary.start_time.isoformat(),
            "end_time": self.summary.end_time.isoformat() if self.summary.end_time else None,
            "duration_seconds": self.summary.duration.total_seconds() if self.summary.duration else None,
            "success": self.summary.success,
            "rollback_performed": self.summary.rollback_performed,
            "version_changes": [
                {
                    "chart_name": vc.chart_name,
                    "old_version": vc.old_version,
                    "new_version": vc.new_version,
                    "timestamp": vc.timestamp
                }
                for vc in self.summary.version_changes
            ],
            "config_changes": [
                {
                    "file_path": cc.file_path,
                    "changes": cc.changes,
                    "timestamp": cc.timestamp
                }
                for cc in self.summary.config_changes
            ],
            "services": {
                "upgraded": self.summary.services_upgraded,
                "failed": self.summary.services_failed
            },
            "issues": [
                {
                    "severity": i.severity,
                    "component": i.component,
                    "description": i.description,
                    "timestamp": i.timestamp,
                    "resolved": i.resolved
                }
                for i in self.summary.issues
            ],
            "statistics": {
                "total_version_changes": self.summary.total_version_changes,
                "total_config_changes": self.summary.total_config_changes,
                "total_issues": self.summary.total_issues,
                "critical_issues": len(self.summary.critical_issues)
            }
        }
    
    def save_report(
        self,
        output_dir: Path,
        format: str = "both"
    ) -> None:
        """Save the report to file(s).
        
        Args:
            output_dir: Directory to save reports
            format: Report format ('text', 'json', or 'both')
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format in ["text", "both"]:
            text_file = output_dir / f"upgrade_summary_{timestamp}.txt"
            with open(text_file, 'w') as f:
                f.write(self.generate_text_report())
            print(f"Text report saved to {text_file}")
        
        if format in ["json", "both"]:
            json_file = output_dir / f"upgrade_summary_{timestamp}.json"
            with open(json_file, 'w') as f:
                json.dump(self.generate_json_report(), f, indent=2)
            print(f"JSON report saved to {json_file}")
    
    def _format_duration(self, duration: Optional[timedelta]) -> str:
        """Format duration as human-readable string.
        
        Args:
            duration: Duration to format
            
        Returns:
            Formatted duration string
        """
        if not duration:
            return "N/A"
        
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    def from_action_log(self, action_log: List[Dict[str, Any]]) -> None:
        """Populate summary from action log.
        
        Args:
            action_log: List of action log entries
        """
        for entry in action_log:
            action_type = entry.get("action_type")
            component = entry.get("component")
            details = entry.get("details", {})
            
            if action_type == "version_update":
                self.add_version_change(
                    component,
                    details.get("old_version", "unknown"),
                    details.get("new_version", "unknown")
                )
            
            elif action_type == "config_update":
                self.add_config_change(component, details)
            
            elif action_type == "service_upgrade":
                status = details.get("status")
                if status == "success":
                    self.add_service_upgraded(component)
                elif status == "failed":
                    self.add_service_failed(component)
                    error = details.get("error", "Unknown error")
                    self.add_issue("high", component, f"Service upgrade failed: {error}")
            
            elif action_type == "validation":
                result = details.get("result")
                if result == "failed":
                    issues = details.get("issues", [])
                    for issue in issues:
                        self.add_issue("medium", component, str(issue))
            
            elif action_type == "rollback":
                self.mark_rollback()


class ReportGenerator:
    """High-level report generator for upgrade operations.
    
    Provides methods for generating various types of reports
    including dry-run reports and full upgrade reports.
    """
    
    def __init__(self):
        """Initialize the report generator."""
        self.summary_gen = SummaryReportGenerator()
    
    def generate_dry_run_report(
        self,
        version_result: Any,
        validation_report: Any,
        breaking_report: Any
    ) -> str:
        """Generate a dry-run report showing planned changes.
        
        Args:
            version_result: Version update results
            validation_report: Configuration validation results
            breaking_report: Breaking changes report
            
        Returns:
            Formatted dry-run report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("DRY-RUN REPORT: OpenStack Caracal to Epoxy Upgrade")
        lines.append("=" * 80)
        lines.append("")
        lines.append("This is a dry-run. No changes will be applied.")
        lines.append("")
        
        # Version changes
        lines.append("PLANNED VERSION CHANGES")
        lines.append("-" * 80)
        if hasattr(version_result, 'updates'):
            lines.append(f"Total charts to update: {len(version_result.updates)}")
            lines.append("")
            for update in version_result.updates:
                lines.append(f"  • {update.chart_name}")
                lines.append(f"    {update.current_version} → {update.target_version}")
                lines.append(f"    Category: {update.category}")
        lines.append("")
        
        # Configuration validation
        lines.append("CONFIGURATION VALIDATION")
        lines.append("-" * 80)
        if hasattr(validation_report, 'issues'):
            if validation_report.issues:
                lines.append(f"Issues found: {len(validation_report.issues)}")
                for issue in validation_report.issues:
                    lines.append(f"  [{issue.severity}] {issue.component}: {issue.description}")
            else:
                lines.append("✓ No configuration issues found")
        lines.append("")
        
        # Breaking changes
        lines.append("BREAKING CHANGES")
        lines.append("-" * 80)
        if hasattr(breaking_report, 'changes'):
            if breaking_report.changes:
                lines.append(f"Breaking changes detected: {len(breaking_report.changes)}")
                for change in breaking_report.changes:
                    lines.append(f"  [{change.severity}] {change.component}")
                    lines.append(f"    {change.description}")
                    lines.append(f"    Mitigation: {change.mitigation}")
            else:
                lines.append("✓ No breaking changes detected")
        lines.append("")
        
        lines.append("=" * 80)
        lines.append("To proceed with the upgrade, run without --dry-run flag")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def generate_upgrade_report(
        self,
        version_result: Any,
        validation_report: Any,
        breaking_report: Any,
        upgrade_result: Any,
        config: Any
    ) -> str:
        """Generate a complete upgrade report.
        
        Args:
            version_result: Version update results
            validation_report: Configuration validation results
            breaking_report: Breaking changes report
            upgrade_result: Upgrade execution results
            config: Upgrade configuration
            
        Returns:
            Formatted upgrade report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("UPGRADE REPORT: OpenStack Caracal to Epoxy")
        lines.append("=" * 80)
        lines.append("")
        
        # Configuration
        lines.append("CONFIGURATION")
        lines.append("-" * 80)
        lines.append(f"Source Release: {config.source_release}")
        lines.append(f"Target Release: {config.target_release}")
        lines.append(f"Namespace: {config.namespace}")
        lines.append(f"Skip Optional: {config.skip_optional_services}")
        lines.append("")
        
        # Version changes
        lines.append("VERSION CHANGES")
        lines.append("-" * 80)
        if hasattr(version_result, 'updates'):
            lines.append(f"Charts updated: {len(version_result.updates)}")
            for update in version_result.updates:
                lines.append(f"  ✓ {update.chart_name}: {update.current_version} → {update.target_version}")
        lines.append("")
        
        # Upgrade results
        lines.append("UPGRADE EXECUTION")
        lines.append("-" * 80)
        lines.append(f"Status: {'SUCCESS' if upgrade_result.success else 'FAILED'}")
        lines.append(f"Duration: {upgrade_result.total_duration:.1f} seconds")
        lines.append(f"Services Upgraded: {len(upgrade_result.services_upgraded)}")
        lines.append(f"Services Failed: {len(upgrade_result.services_failed)}")
        lines.append("")
        
        if upgrade_result.services_upgraded:
            lines.append("Successfully Upgraded:")
            for service in upgrade_result.services_upgraded:
                result = upgrade_result.service_results.get(service)
                if result:
                    lines.append(f"  ✓ {service} ({result.duration:.1f}s)")
                else:
                    lines.append(f"  ✓ {service}")
        
        if upgrade_result.services_failed:
            lines.append("")
            lines.append("Failed Services:")
            for service in upgrade_result.services_failed:
                result = upgrade_result.service_results.get(service)
                if result:
                    lines.append(f"  ✗ {service}")
                    for error in result.errors:
                        lines.append(f"    Error: {error}")
        
        if upgrade_result.warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in upgrade_result.warnings:
                lines.append(f"  ⚠ {warning}")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
