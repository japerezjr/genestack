"""Deprecated option detection for configuration validation."""

import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

from ..utils.yaml_utils import read_yaml_file


logger = logging.getLogger(__name__)


@dataclass
class DeprecationRule:
    """Represents a deprecation rule."""
    
    component: str
    option: str
    replacement: str
    severity: str
    description: str
    is_pattern: bool = False
    
    def matches(self, key_path: str, value: Any = None) -> bool:
        """
        Check if this rule matches a configuration key path.
        
        Args:
            key_path: Full path to the configuration key
            value: Value of the configuration (optional)
            
        Returns:
            True if the rule matches
        """
        if self.is_pattern:
            # Pattern-based matching
            return self.option in key_path or re.search(self.option, key_path) is not None
        else:
            # Exact or wildcard matching
            # Handle wildcards like "conf.*.oslo_messaging_rabbit.heartbeat_in_pthread"
            pattern = self.option.replace("*", "[^.]+")
            pattern = f"^{pattern}$"
            return re.match(pattern, key_path) is not None


@dataclass
class DeprecationIssue:
    """Represents a deprecated option found in configuration."""
    
    file_path: str
    key_path: str
    current_value: Any
    rule: DeprecationRule
    
    def __str__(self) -> str:
        """String representation of the issue."""
        return (
            f"[{self.rule.severity.upper()}] {self.file_path} - {self.key_path}:\n"
            f"  Component: {self.rule.component}\n"
            f"  Issue: {self.rule.description}\n"
            f"  Current value: {self.current_value}\n"
            f"  Remediation: {self.rule.replacement}"
        )


class DeprecationDetector:
    """
    Detector for deprecated configuration options.
    
    This class loads deprecation rules and scans configurations
    for deprecated options, providing recommendations for updates.
    """
    
    def __init__(self, rules_file: Optional[str] = None):
        """
        Initialize the deprecation detector.
        
        Args:
            rules_file: Path to deprecation rules YAML file
        """
        self.rules: List[DeprecationRule] = []
        self.issues: List[DeprecationIssue] = []
        
        if rules_file:
            self.load_rules(rules_file)
    
    def load_rules(self, rules_file: str) -> None:
        """
        Load deprecation rules from a YAML file.
        
        Args:
            rules_file: Path to the rules file
        """
        try:
            rules_data = read_yaml_file(rules_file)
            
            # Load explicit deprecations
            if 'deprecations' in rules_data:
                for dep in rules_data['deprecations']:
                    component = dep.get('component', 'unknown')
                    for opt in dep.get('deprecated_options', []):
                        rule = DeprecationRule(
                            component=component,
                            option=opt['option'],
                            replacement=opt['replacement'],
                            severity=opt.get('severity', 'medium'),
                            description=opt.get('description', ''),
                            is_pattern=False
                        )
                        self.rules.append(rule)
            
            # Load pattern-based deprecations
            if 'patterns' in rules_data:
                for pattern in rules_data['patterns']:
                    rule = DeprecationRule(
                        component=pattern.get('component', 'unknown'),
                        option=pattern['pattern'],
                        replacement=pattern['replacement'],
                        severity=pattern.get('severity', 'medium'),
                        description=pattern.get('description', ''),
                        is_pattern=True
                    )
                    self.rules.append(rule)
            
            logger.info(f"Loaded {len(self.rules)} deprecation rules from {rules_file}")
        
        except Exception as e:
            logger.error(f"Failed to load deprecation rules from {rules_file}: {e}")
            raise
    
    def scan_config(
        self,
        config: Dict[str, Any],
        file_path: str,
        prefix: str = ""
    ) -> List[DeprecationIssue]:
        """
        Scan a configuration for deprecated options.
        
        Args:
            config: Parsed configuration dictionary
            file_path: Path to the configuration file
            prefix: Key prefix for nested structures
            
        Returns:
            List of deprecation issues found in this file
        """
        file_issues = []
        
        if not isinstance(config, dict):
            return file_issues
        
        for key, value in config.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            # Check if this key matches any deprecation rule
            for rule in self.rules:
                if rule.matches(current_path, value):
                    issue = DeprecationIssue(
                        file_path=file_path,
                        key_path=current_path,
                        current_value=value,
                        rule=rule
                    )
                    file_issues.append(issue)
                    self.issues.append(issue)
                    logger.info(f"Found deprecated option in {file_path}: {current_path}")
            
            # Recursively scan nested dictionaries
            if isinstance(value, dict):
                nested_issues = self.scan_config(value, file_path, current_path)
                file_issues.extend(nested_issues)
            
            # Scan lists
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        nested_issues = self.scan_config(
                            item,
                            file_path,
                            f"{current_path}[{i}]"
                        )
                        file_issues.extend(nested_issues)
        
        return file_issues
    
    def get_issues(self, severity: Optional[str] = None) -> List[DeprecationIssue]:
        """
        Get deprecation issues, optionally filtered by severity.
        
        Args:
            severity: Filter by severity (critical, high, medium, low)
            
        Returns:
            List of deprecation issues
        """
        if severity:
            return [i for i in self.issues if i.rule.severity == severity]
        return self.issues
    
    def get_issues_by_file(self) -> Dict[str, List[DeprecationIssue]]:
        """
        Group issues by file path.
        
        Returns:
            Dictionary mapping file paths to lists of issues
        """
        by_file = {}
        for issue in self.issues:
            if issue.file_path not in by_file:
                by_file[issue.file_path] = []
            by_file[issue.file_path].append(issue)
        return by_file
    
    def get_issues_by_component(self) -> Dict[str, List[DeprecationIssue]]:
        """
        Group issues by component.
        
        Returns:
            Dictionary mapping components to lists of issues
        """
        by_component = {}
        for issue in self.issues:
            component = issue.rule.component
            if component not in by_component:
                by_component[component] = []
            by_component[component].append(issue)
        return by_component
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of deprecation detection.
        
        Returns:
            Dictionary with detection statistics
        """
        by_severity = {
            "critical": len(self.get_issues("critical")),
            "high": len(self.get_issues("high")),
            "medium": len(self.get_issues("medium")),
            "low": len(self.get_issues("low"))
        }
        
        return {
            "total_issues": len(self.issues),
            "files_affected": len(self.get_issues_by_file()),
            "components_affected": len(self.get_issues_by_component()),
            "by_severity": by_severity
        }
    
    def generate_remediation_plan(self) -> List[Dict[str, Any]]:
        """
        Generate a remediation plan for all deprecated options.
        
        Returns:
            List of remediation actions
        """
        plan = []
        
        for issue in self.issues:
            plan.append({
                "file": issue.file_path,
                "key": issue.key_path,
                "component": issue.rule.component,
                "severity": issue.rule.severity,
                "current_value": str(issue.current_value),
                "action": issue.rule.replacement,
                "description": issue.rule.description
            })
        
        # Sort by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        plan.sort(key=lambda x: severity_order.get(x["severity"], 4))
        
        return plan
    
    def has_critical_issues(self) -> bool:
        """Check if there are any critical severity issues."""
        return len(self.get_issues("critical")) > 0
    
    def clear_issues(self) -> None:
        """Clear all detected issues."""
        self.issues = []
