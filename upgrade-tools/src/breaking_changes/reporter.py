"""Report generation for breaking changes."""

from typing import List, TextIO
from datetime import datetime

from .models import BreakingChange, ImpactReport, MitigationPlan


class BreakingChangeReporter:
    """Generates reports for breaking changes and their impact."""
    
    def __init__(self):
        """Initialize the reporter."""
        pass
    
    def generate_impact_report(
        self,
        report: ImpactReport,
        format: str = 'markdown'
    ) -> str:
        """
        Generate a formatted impact report.
        
        Args:
            report: Impact report to format
            format: Output format ('markdown', 'text', 'json')
        
        Returns:
            Formatted report string
        """
        if format == 'markdown':
            return self._generate_markdown_report(report)
        elif format == 'text':
            return self._generate_text_report(report)
        elif format == 'json':
            return self._generate_json_report(report)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_markdown_report(self, report: ImpactReport) -> str:
        """Generate markdown formatted report."""
        lines = []
        
        # Header
        lines.append("# Breaking Changes Impact Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Breaking Changes Affecting Deployment:** {report.total_affected}")
        lines.append(f"- **Critical Issues:** {report.critical_count}")
        lines.append(f"- **High Priority Issues:** {report.high_count}")
        lines.append(f"- **Medium Priority Issues:** {report.medium_count}")
        lines.append(f"- **Low Priority Issues:** {report.low_count}")
        lines.append("")
        
        if report.has_critical_issues:
            lines.append("⚠️ **WARNING: Critical issues detected that will prevent upgrade!**")
            lines.append("")
        elif report.has_blocking_issues:
            lines.append("⚠️ **WARNING: High priority issues detected that should be addressed before upgrade.**")
            lines.append("")
        
        # Affected changes by severity
        if report.total_affected > 0:
            lines.append("## Affected Breaking Changes")
            lines.append("")
            
            # Group by severity
            for severity in ['critical', 'high', 'medium', 'low']:
                severity_changes = [
                    c for c in report.affected_changes
                    if c.severity == severity
                ]
                
                if severity_changes:
                    lines.append(f"### {severity.upper()} Priority")
                    lines.append("")
                    
                    for change in severity_changes:
                        lines.extend(self._format_change_markdown(change))
                        lines.append("")
        else:
            lines.append("## No Breaking Changes Detected")
            lines.append("")
            lines.append("✅ No breaking changes affect your current deployment configuration.")
            lines.append("")
        
        # Unaffected changes (summary only)
        if report.unaffected_changes:
            lines.append("## Unaffected Breaking Changes")
            lines.append("")
            lines.append(f"The following {len(report.unaffected_changes)} breaking changes do not affect your deployment:")
            lines.append("")
            for change in report.unaffected_changes:
                lines.append(f"- **{change.id}**: {change.title} ({change.component})")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_change_markdown(self, change: BreakingChange) -> List[str]:
        """Format a single breaking change in markdown."""
        lines = []
        
        lines.append(f"#### {change.id}: {change.title}")
        lines.append("")
        lines.append(f"**Component:** {change.component}")
        lines.append(f"**Type:** {change.change_type}")
        lines.append(f"**Severity:** {change.severity}")
        lines.append("")
        lines.append(f"**Description:** {change.description}")
        lines.append("")
        lines.append(f"**Impact:** {change.impact}")
        lines.append("")
        lines.append(f"**Mitigation:** {change.mitigation}")
        lines.append("")
        
        if change.affects_services:
            services = ", ".join(change.affects_services)
            lines.append(f"**Affects Services:** {services}")
            lines.append("")
        
        return lines
    
    def _generate_text_report(self, report: ImpactReport) -> str:
        """Generate plain text formatted report."""
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("BREAKING CHANGES IMPACT REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Breaking Changes Affecting Deployment: {report.total_affected}")
        lines.append(f"  Critical Issues: {report.critical_count}")
        lines.append(f"  High Priority Issues: {report.high_count}")
        lines.append(f"  Medium Priority Issues: {report.medium_count}")
        lines.append(f"  Low Priority Issues: {report.low_count}")
        lines.append("")
        
        if report.has_critical_issues:
            lines.append("WARNING: Critical issues detected that will prevent upgrade!")
            lines.append("")
        
        # Affected changes
        if report.total_affected > 0:
            lines.append("AFFECTED BREAKING CHANGES")
            lines.append("-" * 80)
            
            for change in report.get_sorted_changes():
                lines.extend(self._format_change_text(change))
                lines.append("")
        else:
            lines.append("No breaking changes affect your current deployment.")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_change_text(self, change: BreakingChange) -> List[str]:
        """Format a single breaking change in plain text."""
        lines = []
        
        lines.append(f"[{change.severity.upper()}] {change.id}: {change.title}")
        lines.append(f"  Component: {change.component}")
        lines.append(f"  Type: {change.change_type}")
        lines.append(f"  Description: {change.description}")
        lines.append(f"  Impact: {change.impact}")
        lines.append(f"  Mitigation: {change.mitigation}")
        
        if change.affects_services:
            services = ", ".join(change.affects_services)
            lines.append(f"  Affects: {services}")
        
        return lines
    
    def _generate_json_report(self, report: ImpactReport) -> str:
        """Generate JSON formatted report."""
        import json
        
        data = {
            'generated': datetime.now().isoformat(),
            'summary': {
                'total_affected': report.total_affected,
                'critical_count': report.critical_count,
                'high_count': report.high_count,
                'medium_count': report.medium_count,
                'low_count': report.low_count,
                'has_critical_issues': report.has_critical_issues,
                'has_blocking_issues': report.has_blocking_issues
            },
            'affected_changes': [
                {
                    'id': c.id,
                    'component': c.component,
                    'change_type': c.change_type,
                    'title': c.title,
                    'description': c.description,
                    'impact': c.impact,
                    'mitigation': c.mitigation,
                    'severity': c.severity,
                    'priority': c.priority,
                    'affects_services': c.affects_services
                }
                for c in report.affected_changes
            ],
            'unaffected_changes': [
                {
                    'id': c.id,
                    'component': c.component,
                    'title': c.title,
                    'severity': c.severity
                }
                for c in report.unaffected_changes
            ]
        }
        
        return json.dumps(data, indent=2)
    
    def generate_mitigation_plan_report(
        self,
        plan: MitigationPlan,
        format: str = 'markdown'
    ) -> str:
        """
        Generate a formatted mitigation plan report.
        
        Args:
            plan: Mitigation plan to format
            format: Output format ('markdown', 'text')
        
        Returns:
            Formatted report string
        """
        if format == 'markdown':
            return self._generate_mitigation_markdown(plan)
        elif format == 'text':
            return self._generate_mitigation_text(plan)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_mitigation_markdown(self, plan: MitigationPlan) -> str:
        """Generate markdown formatted mitigation plan."""
        lines = []
        
        lines.append("# Breaking Changes Mitigation Plan")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        if plan.required_actions:
            lines.append("## Required Actions (Must Complete Before Upgrade)")
            lines.append("")
            for i, action in enumerate(plan.required_actions, 1):
                lines.append(f"{i}. {action}")
            lines.append("")
        
        if plan.recommended_actions:
            lines.append("## Recommended Actions (Should Complete Before Upgrade)")
            lines.append("")
            for i, action in enumerate(plan.recommended_actions, 1):
                lines.append(f"{i}. {action}")
            lines.append("")
        
        if plan.optional_actions:
            lines.append("## Optional Actions (Can Complete After Upgrade)")
            lines.append("")
            for i, action in enumerate(plan.optional_actions, 1):
                lines.append(f"{i}. {action}")
            lines.append("")
        
        if not plan.has_required_actions:
            lines.append("✅ No required actions - deployment is ready for upgrade!")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_mitigation_text(self, plan: MitigationPlan) -> str:
        """Generate plain text formatted mitigation plan."""
        lines = []
        
        lines.append("=" * 80)
        lines.append("BREAKING CHANGES MITIGATION PLAN")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        if plan.required_actions:
            lines.append("REQUIRED ACTIONS (Must Complete Before Upgrade)")
            lines.append("-" * 80)
            for i, action in enumerate(plan.required_actions, 1):
                lines.append(f"{i}. {action}")
            lines.append("")
        
        if plan.recommended_actions:
            lines.append("RECOMMENDED ACTIONS (Should Complete Before Upgrade)")
            lines.append("-" * 80)
            for i, action in enumerate(plan.recommended_actions, 1):
                lines.append(f"{i}. {action}")
            lines.append("")
        
        if plan.optional_actions:
            lines.append("OPTIONAL ACTIONS (Can Complete After Upgrade)")
            lines.append("-" * 80)
            for i, action in enumerate(plan.optional_actions, 1):
                lines.append(f"{i}. {action}")
            lines.append("")
        
        return "\n".join(lines)
    
    def write_report_to_file(
        self,
        report: ImpactReport,
        filepath: str,
        format: str = 'markdown'
    ):
        """
        Write impact report to a file.
        
        Args:
            report: Impact report to write
            filepath: Path to output file
            format: Output format
        """
        content = self.generate_impact_report(report, format)
        with open(filepath, 'w') as f:
            f.write(content)
    
    def write_mitigation_plan_to_file(
        self,
        plan: MitigationPlan,
        filepath: str,
        format: str = 'markdown'
    ):
        """
        Write mitigation plan to a file.
        
        Args:
            plan: Mitigation plan to write
            filepath: Path to output file
            format: Output format
        """
        content = self.generate_mitigation_plan_report(plan, format)
        with open(filepath, 'w') as f:
            f.write(content)
