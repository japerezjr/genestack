"""Main breaking change detector that orchestrates catalog, analysis, and reporting."""

from typing import Dict, Any, List
from pathlib import Path

from .catalog import BreakingChangeCatalog
from .analyzer import ImpactAnalyzer
from .reporter import BreakingChangeReporter
from .models import ImpactReport, MitigationPlan


class BreakingChangeDetector:
    """
    Main interface for breaking change detection.
    
    Orchestrates the catalog, analyzer, and reporter to provide
    a complete breaking change detection workflow.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the breaking change detector.
        
        Args:
            config_path: Path to breaking-changes.yaml file (optional)
        """
        self.catalog = BreakingChangeCatalog(config_path)
        self.analyzer = ImpactAnalyzer(self.catalog)
        self.reporter = BreakingChangeReporter()
    
    def detect_in_configuration(
        self,
        config_data: Dict[str, Any],
        service_name: str = None
    ) -> ImpactReport:
        """
        Detect breaking changes in a single configuration.
        
        Args:
            config_data: Parsed configuration data
            service_name: Name of the service (optional)
        
        Returns:
            ImpactReport with detected breaking changes
        """
        return self.analyzer.analyze_configuration(config_data, service_name)
    
    def detect_in_deployment(
        self,
        override_configs: Dict[str, Dict[str, Any]],
        deployed_services: List[str] = None
    ) -> ImpactReport:
        """
        Detect breaking changes across an entire deployment.
        
        Args:
            override_configs: Dict mapping service names to config data
            deployed_services: List of deployed service names (optional)
        
        Returns:
            ImpactReport with detected breaking changes
        """
        return self.analyzer.analyze_deployment(override_configs, deployed_services)
    
    def generate_report(
        self,
        report: ImpactReport,
        output_path: str = None,
        format: str = 'markdown'
    ) -> str:
        """
        Generate a breaking changes report.
        
        Args:
            report: Impact report to format
            output_path: Path to write report (optional, returns string if None)
            format: Output format ('markdown', 'text', 'json')
        
        Returns:
            Formatted report string
        """
        report_content = self.reporter.generate_impact_report(report, format)
        
        if output_path:
            self.reporter.write_report_to_file(report, output_path, format)
        
        return report_content
    
    def generate_mitigation_plan(
        self,
        report: ImpactReport,
        output_path: str = None,
        format: str = 'markdown'
    ) -> MitigationPlan:
        """
        Generate a mitigation plan for breaking changes.
        
        Args:
            report: Impact report with affected changes
            output_path: Path to write plan (optional)
            format: Output format ('markdown', 'text')
        
        Returns:
            MitigationPlan with required actions
        """
        plan = self.analyzer.generate_mitigation_plan(report)
        
        if output_path:
            self.reporter.write_mitigation_plan_to_file(plan, output_path, format)
        
        return plan
    
    def get_catalog_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the breaking changes catalog.
        
        Returns:
            Dict with catalog statistics
        """
        return self.catalog.get_statistics()
    
    def get_critical_changes(self):
        """Get all critical breaking changes from catalog."""
        return self.catalog.get_critical_changes()
    
    def get_changes_by_component(self, component: str):
        """Get breaking changes for a specific component."""
        return self.catalog.get_changes_by_component(component)
    
    def get_changes_by_service(self, service: str):
        """Get breaking changes affecting a specific service."""
        return self.catalog.get_changes_by_service(service)
    
    def detect_for_release(self, release: str) -> ImpactReport:
        """
        Detect all breaking changes for a target release.
        
        This method returns all breaking changes in the catalog
        as an impact report, useful for showing what changes
        exist in the target release.
        
        Args:
            release: Target release version (e.g., "2025.1")
        
        Returns:
            ImpactReport with all breaking changes
        """
        # Get all breaking changes from catalog
        all_changes = self.catalog.get_all_changes()
        
        # Create impact report with all changes marked as affected
        report = ImpactReport()
        for change in all_changes:
            report.add_affected_change(change)
        
        return report
