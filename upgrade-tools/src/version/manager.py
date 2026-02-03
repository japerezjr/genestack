"""Chart Version Manager - Main interface for version management."""

from pathlib import Path
from typing import Dict, List, Optional
import logging

from .parser import VersionParser, VersionUpdate
from .updater import VersionUpdater
from .reporter import VersionReporter, VersionReport


logger = logging.getLogger(__name__)


class ChartVersionManager:
    """
    Main interface for managing helm chart version updates.
    
    This class provides a high-level API for:
    - Loading and parsing chart versions
    - Identifying charts that need updates
    - Applying version updates
    - Generating reports
    """
    
    def __init__(self, chart_versions_path: str):
        """
        Initialize the Chart Version Manager.
        
        Args:
            chart_versions_path: Path to helm-chart-versions.yaml file
        """
        self.chart_versions_path = Path(chart_versions_path)
        self.parser = VersionParser(str(chart_versions_path))
        self.updater = VersionUpdater(str(chart_versions_path))
        self.reporter = VersionReporter()
        
        self.current_charts: Dict[str, str] = {}
        self.identified_updates: List[VersionUpdate] = []
    
    def load_current_versions(self) -> Dict[str, str]:
        """
        Load current chart versions from file.
        
        Returns:
            Dictionary mapping chart names to version strings
        """
        self.current_charts = self.parser.load_versions()
        logger.info(f"Loaded {len(self.current_charts)} chart versions")
        return self.current_charts
    
    def identify_updates(self, target_release: str = "2025.1") -> List[VersionUpdate]:
        """
        Identify which charts need version updates.
        
        Args:
            target_release: Target OpenStack release version
            
        Returns:
            List of VersionUpdate objects
        """
        self.identified_updates = self.parser.identify_updates(target_release)
        logger.info(f"Identified {len(self.identified_updates)} charts for update")
        return self.identified_updates
    
    def apply_updates(
        self,
        target_release: str = "2025.1",
        dry_run: bool = False
    ) -> Dict[str, str]:
        """
        Apply version updates to helm-chart-versions.yaml.
        
        Args:
            target_release: Target OpenStack release version
            dry_run: If True, don't write changes to file
            
        Returns:
            Dictionary of updated chart versions
        """
        if not self.identified_updates:
            self.identify_updates(target_release)
        
        updated = self.updater.update_versions(
            self.identified_updates,
            target_release,
            dry_run
        )
        
        logger.info(f"Applied {len(updated)} version updates")
        return updated
    
    def generate_report(
        self,
        source_release: str = "2024.1",
        target_release: str = "2025.1",
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None
    ) -> VersionReport:
        """
        Generate a version update report.
        
        Args:
            source_release: Source OpenStack release version
            target_release: Target OpenStack release version
            errors: List of error messages (optional)
            warnings: List of warning messages (optional)
            
        Returns:
            VersionReport object
        """
        if not self.current_charts:
            self.load_current_versions()
        
        if not self.identified_updates:
            self.identify_updates(target_release)
        
        report = self.reporter.generate_report(
            updates=self.identified_updates,
            total_charts=len(self.current_charts),
            source_release=source_release,
            target_release=target_release,
            errors=errors,
            warnings=warnings
        )
        
        return report
    
    def upgrade_caracal_to_epoxy(
        self,
        dry_run: bool = False,
        generate_report: bool = True,
        report_path: Optional[str] = None,
        report_format: str = "markdown"
    ) -> VersionReport:
        """
        Complete workflow: identify, update, and report on Caracal to Epoxy upgrade.
        
        Args:
            dry_run: If True, don't write changes to file
            generate_report: If True, generate a report
            report_path: Path to save report (optional)
            report_format: Report format - "markdown", "text", or "json"
            
        Returns:
            VersionReport object
        """
        logger.info("Starting Caracal to Epoxy upgrade workflow")
        
        # Load current versions
        self.load_current_versions()
        
        # Identify updates
        updates = self.identify_updates(target_release="2025.1")
        
        if not updates:
            logger.info("No updates needed")
            report = self.generate_report(
                source_release="2024.1/2024.2",
                target_release="2025.1",
                warnings=["No charts require version updates"]
            )
            return report
        
        # Apply updates
        try:
            self.apply_updates(target_release="2025.1", dry_run=dry_run)
            errors = []
        except Exception as e:
            logger.error(f"Failed to apply updates: {e}")
            errors = [str(e)]
        
        # Generate report
        report = self.generate_report(
            source_release="2024.1/2024.2",
            target_release="2025.1",
            errors=errors
        )
        
        # Save report if requested
        if generate_report and report_path:
            report.save_to_file(report_path, format=report_format)
            logger.info(f"Report saved to {report_path}")
        
        logger.info("Upgrade workflow complete")
        return report
