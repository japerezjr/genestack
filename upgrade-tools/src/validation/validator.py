"""Main configuration validator that orchestrates all validation components."""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .scanner import ConfigurationScanner
from .yaml_validator import YAMLValidator, ValidationIssue
from .image_validator import ImageTagValidator, ImageTagIssue
from .deprecation_detector import DeprecationDetector, DeprecationIssue


logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    
    timestamp: datetime
    base_path: str
    total_files_scanned: int
    files_with_issues: int
    
    # YAML validation results
    yaml_errors: List[ValidationIssue] = field(default_factory=list)
    yaml_warnings: List[ValidationIssue] = field(default_factory=list)
    
    # Image tag validation results
    image_tag_issues: List[ImageTagIssue] = field(default_factory=list)
    
    # Deprecation detection results
    deprecation_issues: List[DeprecationIssue] = field(default_factory=list)
    
    # Summary statistics
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return len(self.yaml_errors) > 0
    
    def has_critical_issues(self) -> bool:
        """Check if there are any critical deprecation issues."""
        return any(i.rule.severity == "critical" for i in self.deprecation_issues)
    
    def get_total_issues(self) -> int:
        """Get total count of all issues."""
        return (
            len(self.yaml_errors) +
            len(self.yaml_warnings) +
            len(self.image_tag_issues) +
            len(self.deprecation_issues)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "base_path": self.base_path,
            "total_files_scanned": self.total_files_scanned,
            "files_with_issues": self.files_with_issues,
            "total_issues": self.get_total_issues(),
            "has_errors": self.has_errors(),
            "has_critical_issues": self.has_critical_issues(),
            "yaml_errors": len(self.yaml_errors),
            "yaml_warnings": len(self.yaml_warnings),
            "image_tag_issues": len(self.image_tag_issues),
            "deprecation_issues": len(self.deprecation_issues),
            "summary": self.summary
        }
    
    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            "# Configuration Validation Report",
            "",
            f"**Generated:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Base Path:** {self.base_path}",
            "",
            "## Summary",
            "",
            f"- **Total Files Scanned:** {self.total_files_scanned}",
            f"- **Files with Issues:** {self.files_with_issues}",
            f"- **Total Issues:** {self.get_total_issues()}",
            f"- **Has Errors:** {'Yes' if self.has_errors() else 'No'}",
            f"- **Has Critical Issues:** {'Yes' if self.has_critical_issues() else 'No'}",
            "",
            "### Issue Breakdown",
            "",
            f"- **YAML Errors:** {len(self.yaml_errors)}",
            f"- **YAML Warnings:** {len(self.yaml_warnings)}",
            f"- **Image Tag Issues:** {len(self.image_tag_issues)}",
            f"- **Deprecated Options:** {len(self.deprecation_issues)}",
            ""
        ]
        
        # YAML Errors
        if self.yaml_errors:
            lines.extend([
                "## YAML Validation Errors",
                "",
                "The following files have YAML syntax or structure errors:",
                ""
            ])
            for issue in self.yaml_errors:
                lines.append(f"### {issue.file_path}")
                if issue.line_number:
                    lines.append(f"**Line {issue.line_number}:** {issue.description}")
                else:
                    lines.append(f"**Error:** {issue.description}")
                if issue.remediation:
                    lines.append(f"**Remediation:** {issue.remediation}")
                lines.append("")
        
        # Image Tag Issues
        if self.image_tag_issues:
            lines.extend([
                "## Image Tag Updates Required",
                "",
                "The following image tags contain Caracal version strings and should be updated:",
                ""
            ])
            
            # Group by file
            by_file = {}
            for issue in self.image_tag_issues:
                if issue.file_path not in by_file:
                    by_file[issue.file_path] = []
                by_file[issue.file_path].append(issue)
            
            for file_path, issues in by_file.items():
                lines.append(f"### {file_path}")
                lines.append("")
                for issue in issues:
                    lines.append(f"- **{issue.image_key}**")
                    lines.append(f"  - Current: `{issue.current_tag}`")
                    lines.append(f"  - Recommended: `{issue.recommended_tag}`")
                lines.append("")
        
        # Deprecation Issues
        if self.deprecation_issues:
            lines.extend([
                "## Deprecated Configuration Options",
                "",
                "The following deprecated options were found:",
                ""
            ])
            
            # Group by severity
            by_severity = {
                "critical": [],
                "high": [],
                "medium": [],
                "low": []
            }
            for issue in self.deprecation_issues:
                severity = issue.rule.severity
                if severity in by_severity:
                    by_severity[severity].append(issue)
            
            for severity in ["critical", "high", "medium", "low"]:
                issues = by_severity[severity]
                if issues:
                    lines.append(f"### {severity.upper()} Severity")
                    lines.append("")
                    for issue in issues:
                        lines.append(f"#### {issue.file_path}")
                        lines.append(f"- **Option:** `{issue.key_path}`")
                        lines.append(f"- **Component:** {issue.rule.component}")
                        lines.append(f"- **Current Value:** `{issue.current_value}`")
                        lines.append(f"- **Issue:** {issue.rule.description}")
                        lines.append(f"- **Action:** {issue.rule.replacement}")
                        lines.append("")
        
        # Recommendations
        lines.extend([
            "## Recommendations",
            ""
        ])
        
        if self.has_errors():
            lines.append("⚠️ **CRITICAL:** Fix YAML errors before proceeding with upgrade.")
            lines.append("")
        
        if self.has_critical_issues():
            lines.append("⚠️ **CRITICAL:** Address critical deprecation issues before upgrade.")
            lines.append("")
        
        if self.image_tag_issues:
            lines.append("1. Update all image tags to use Epoxy (2025.1) versions")
            lines.append("")
        
        if self.deprecation_issues:
            lines.append("2. Remove or update deprecated configuration options")
            lines.append("")
        
        if not self.get_total_issues():
            lines.append("✅ No issues found. Configuration is ready for upgrade.")
            lines.append("")
        
        return "\n".join(lines)
    
    def save_to_file(self, file_path: str, format: str = "markdown") -> None:
        """
        Save report to file.
        
        Args:
            file_path: Path to save the report
            format: Report format - "markdown", "text", or "json"
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "markdown":
            content = self.to_markdown()
        elif format == "json":
            import json
            content = json.dumps(self.to_dict(), indent=2)
        else:  # text
            content = self.to_markdown()  # Use markdown for text too
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Report saved to {file_path}")


class ConfigurationValidator:
    """
    Main configuration validator that orchestrates all validation components.
    
    This class coordinates:
    - Configuration file scanning
    - YAML validation
    - Image tag validation
    - Deprecated option detection
    - Report generation
    """
    
    def __init__(
        self,
        base_path: str,
        deprecation_rules_file: Optional[str] = None
    ):
        """
        Initialize the configuration validator.
        
        Args:
            base_path: Base directory to scan (e.g., base-helm-configs/)
            deprecation_rules_file: Path to deprecation rules file
        """
        self.base_path = base_path
        self.scanner = ConfigurationScanner(base_path)
        self.yaml_validator = YAMLValidator()
        self.image_validator = ImageTagValidator()
        self.deprecation_detector = DeprecationDetector(deprecation_rules_file)
    
    def validate_all(self, follow_symlinks: bool = False) -> ValidationReport:
        """
        Run complete validation on all configuration files.
        
        Args:
            follow_symlinks: Whether to follow symbolic links during scan
            
        Returns:
            ValidationReport with all validation results
        """
        logger.info("Starting configuration validation")
        
        # Scan for configuration files
        files = self.scanner.scan(follow_symlinks=follow_symlinks)
        logger.info(f"Found {len(files)} configuration files")
        
        files_with_issues = set()
        
        # Validate each file
        for file_path in files:
            logger.debug(f"Validating {file_path}")
            
            # YAML validation
            is_valid, content = self.yaml_validator.validate_helm_override(file_path)
            
            if not is_valid or content is None:
                files_with_issues.add(file_path)
                continue
            
            # Image tag validation
            image_issues = self.image_validator.validate_config(content, file_path)
            if image_issues:
                files_with_issues.add(file_path)
            
            # Deprecation detection
            deprecation_issues = self.deprecation_detector.scan_config(content, file_path)
            if deprecation_issues:
                files_with_issues.add(file_path)
        
        # Generate report
        report = ValidationReport(
            timestamp=datetime.now(),
            base_path=self.base_path,
            total_files_scanned=len(files),
            files_with_issues=len(files_with_issues),
            yaml_errors=self.yaml_validator.get_issues(severity="error"),
            yaml_warnings=self.yaml_validator.get_issues(severity="warning"),
            image_tag_issues=self.image_validator.get_issues(),
            deprecation_issues=self.deprecation_detector.get_issues(),
            summary={
                "scan_summary": self.scanner.get_scan_summary(),
                "yaml_summary": self.yaml_validator.get_summary(),
                "image_summary": self.image_validator.get_summary(),
                "deprecation_summary": self.deprecation_detector.get_summary()
            }
        )
        
        logger.info(f"Validation complete. Found {report.get_total_issues()} total issues")
        
        return report
