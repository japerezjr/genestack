"""Version report generation for upgrade tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json

from .parser import VersionUpdate


@dataclass
class VersionReport:
    """Report of version changes during upgrade."""
    
    timestamp: datetime
    source_release: str  # e.g., "2024.1" or "2024.2"
    target_release: str  # e.g., "2025.1"
    total_charts: int
    updated_charts: int
    updates: List[VersionUpdate]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary format."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'source_release': self.source_release,
            'target_release': self.target_release,
            'total_charts': self.total_charts,
            'updated_charts': self.updated_charts,
            'updates': [
                {
                    'chart_name': u.chart_name,
                    'current_version': u.current_version,
                    'target_version': u.target_version,
                    'category': u.category,
                    'dependencies': u.dependencies
                }
                for u in self.updates
            ],
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def to_markdown(self) -> str:
        """
        Generate a human-readable markdown report.
        
        Returns:
            Markdown-formatted report string
        """
        lines = []
        
        # Header
        lines.append("# OpenStack Chart Version Update Report")
        lines.append("")
        lines.append(f"**Generated:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Source Release:** {self.source_release}")
        lines.append(f"**Target Release:** {self.target_release}")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- Total charts in deployment: {self.total_charts}")
        lines.append(f"- Charts updated: {self.updated_charts}")
        lines.append(f"- Charts unchanged: {self.total_charts - self.updated_charts}")
        lines.append("")
        
        # Errors (if any)
        if self.errors:
            lines.append("## Errors")
            lines.append("")
            for error in self.errors:
                lines.append(f"- ❌ {error}")
            lines.append("")
        
        # Warnings (if any)
        if self.warnings:
            lines.append("## Warnings")
            lines.append("")
            for warning in self.warnings:
                lines.append(f"- ⚠️  {warning}")
            lines.append("")
        
        # Updates by category
        if self.updates:
            # Group updates by category
            by_category = {
                'core': [],
                'optional': [],
                'infrastructure': [],
                'non-openstack': []
            }
            
            for update in self.updates:
                by_category[update.category].append(update)
            
            lines.append("## Version Updates")
            lines.append("")
            
            # Core services
            if by_category['core']:
                lines.append("### Core Services")
                lines.append("")
                lines.append("| Chart | Current Version | Target Version |")
                lines.append("|-------|----------------|----------------|")
                for update in sorted(by_category['core'], key=lambda u: u.chart_name):
                    lines.append(f"| {update.chart_name} | {update.current_version} | {update.target_version} |")
                lines.append("")
            
            # Optional services
            if by_category['optional']:
                lines.append("### Optional Services")
                lines.append("")
                lines.append("| Chart | Current Version | Target Version |")
                lines.append("|-------|----------------|----------------|")
                for update in sorted(by_category['optional'], key=lambda u: u.chart_name):
                    lines.append(f"| {update.chart_name} | {update.current_version} | {update.target_version} |")
                lines.append("")
            
            # Infrastructure services
            if by_category['infrastructure']:
                lines.append("### Infrastructure Services")
                lines.append("")
                lines.append("| Chart | Current Version | Target Version |")
                lines.append("|-------|----------------|----------------|")
                for update in sorted(by_category['infrastructure'], key=lambda u: u.chart_name):
                    lines.append(f"| {update.chart_name} | {update.current_version} | {update.target_version} |")
                lines.append("")
        
        # Dependencies
        if self.updates:
            lines.append("## Upgrade Order Considerations")
            lines.append("")
            lines.append("The following charts have dependencies that must be upgraded first:")
            lines.append("")
            
            for update in sorted(self.updates, key=lambda u: u.chart_name):
                if update.dependencies:
                    deps = ", ".join(update.dependencies)
                    lines.append(f"- **{update.chart_name}** depends on: {deps}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def to_text(self) -> str:
        """
        Generate a simple text report.
        
        Returns:
            Plain text report string
        """
        lines = []
        
        lines.append("=" * 70)
        lines.append("OpenStack Chart Version Update Report")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Source Release: {self.source_release}")
        lines.append(f"Target Release: {self.target_release}")
        lines.append("")
        lines.append(f"Total charts: {self.total_charts}")
        lines.append(f"Updated charts: {self.updated_charts}")
        lines.append("")
        
        if self.errors:
            lines.append("ERRORS:")
            for error in self.errors:
                lines.append(f"  - {error}")
            lines.append("")
        
        if self.warnings:
            lines.append("WARNINGS:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
            lines.append("")
        
        if self.updates:
            lines.append("VERSION UPDATES:")
            lines.append("")
            
            for update in sorted(self.updates, key=lambda u: u.chart_name):
                lines.append(f"  {update.chart_name}:")
                lines.append(f"    Current: {update.current_version}")
                lines.append(f"    Target:  {update.target_version}")
                lines.append(f"    Category: {update.category}")
                if update.dependencies:
                    lines.append(f"    Dependencies: {', '.join(update.dependencies)}")
                lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def save_to_file(self, output_path: str, format: str = "markdown") -> None:
        """
        Save report to a file.
        
        Args:
            output_path: Path where report should be saved
            format: Output format - "markdown", "text", or "json"
            
        Raises:
            ValueError: If format is not supported
            IOError: If file cannot be written
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "markdown":
            content = self.to_markdown()
        elif format == "text":
            content = self.to_text()
        elif format == "json":
            content = self.to_json()
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'markdown', 'text', or 'json'")
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)


class VersionReporter:
    """Generates version update reports."""
    
    def __init__(self):
        """Initialize the version reporter."""
        pass
    
    def generate_report(
        self,
        updates: List[VersionUpdate],
        total_charts: int,
        source_release: str = "2024.1",
        target_release: str = "2025.1",
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None
    ) -> VersionReport:
        """
        Generate a version update report.
        
        Args:
            updates: List of VersionUpdate objects
            total_charts: Total number of charts in deployment
            source_release: Source OpenStack release version
            target_release: Target OpenStack release version
            errors: List of error messages (optional)
            warnings: List of warning messages (optional)
            
        Returns:
            VersionReport object
        """
        return VersionReport(
            timestamp=datetime.now(),
            source_release=source_release,
            target_release=target_release,
            total_charts=total_charts,
            updated_charts=len(updates),
            updates=updates,
            errors=errors or [],
            warnings=warnings or []
        )
    
    def generate_summary(self, updates: List[VersionUpdate]) -> str:
        """
        Generate a brief summary of version updates.
        
        Args:
            updates: List of VersionUpdate objects
            
        Returns:
            Summary string
        """
        if not updates:
            return "No charts require version updates."
        
        by_category = {
            'core': 0,
            'optional': 0,
            'infrastructure': 0,
            'non-openstack': 0
        }
        
        for update in updates:
            by_category[update.category] += 1
        
        parts = []
        if by_category['core']:
            parts.append(f"{by_category['core']} core service(s)")
        if by_category['optional']:
            parts.append(f"{by_category['optional']} optional service(s)")
        if by_category['infrastructure']:
            parts.append(f"{by_category['infrastructure']} infrastructure service(s)")
        
        summary = f"Found {len(updates)} chart(s) to update: {', '.join(parts)}"
        return summary
