"""Impact analysis for breaking changes."""

import re
from typing import List, Dict, Any, Set
from pathlib import Path

from .models import BreakingChange, ImpactReport, MitigationPlan
from .catalog import BreakingChangeCatalog


class ImpactAnalyzer:
    """Analyzes the impact of breaking changes on a deployment."""
    
    def __init__(self, catalog: BreakingChangeCatalog):
        """
        Initialize the impact analyzer.
        
        Args:
            catalog: Breaking change catalog to analyze against
        """
        self.catalog = catalog
    
    def analyze_configuration(
        self,
        config_data: Dict[str, Any],
        service_name: str = None
    ) -> ImpactReport:
        """
        Analyze a configuration for breaking changes.
        
        Args:
            config_data: Parsed configuration data (nested dict)
            service_name: Name of the service (optional, for filtering)
        
        Returns:
            ImpactReport with affected and unaffected changes
        """
        report = ImpactReport()
        
        # Get all breaking changes (or filter by service)
        if service_name:
            changes = self.catalog.get_changes_by_service(service_name)
        else:
            changes = self.catalog.get_all_changes()
        
        # Analyze each breaking change
        for change in changes:
            if self._change_affects_config(change, config_data):
                report.add_affected_change(change)
            else:
                report.add_unaffected_change(change)
        
        return report
    
    def analyze_deployment(
        self,
        override_configs: Dict[str, Dict[str, Any]],
        deployed_services: List[str] = None
    ) -> ImpactReport:
        """
        Analyze an entire deployment for breaking changes.
        
        Args:
            override_configs: Dict mapping service names to their config data
            deployed_services: List of deployed service names (optional)
        
        Returns:
            ImpactReport with affected and unaffected changes
        """
        report = ImpactReport()
        
        # Get all breaking changes
        all_changes = self.catalog.get_all_changes()
        
        # Track which changes we've already added
        added_change_ids: Set[str] = set()
        
        # Analyze each service's configuration
        for service_name, config_data in override_configs.items():
            # Get changes relevant to this service
            service_changes = [
                c for c in all_changes
                if c.matches_service(service_name) and c.id not in added_change_ids
            ]
            
            for change in service_changes:
                if self._change_affects_config(change, config_data):
                    report.add_affected_change(change)
                    added_change_ids.add(change.id)
        
        # Check for changes that affect deployment but aren't config-specific
        for change in all_changes:
            if change.id in added_change_ids:
                continue
            
            # Check if change affects any deployed service
            if deployed_services:
                affects_deployed = any(
                    change.matches_service(svc) for svc in deployed_services
                )
            else:
                affects_deployed = True  # Assume all services deployed
            
            if affects_deployed:
                # For non-config changes (database, dependency, api)
                # that don't have detection patterns, mark as affected
                if change.change_type in ['database', 'dependency', 'api']:
                    if not change.detection_pattern:
                        report.add_affected_change(change)
                        added_change_ids.add(change.id)
                    else:
                        # Still need to check configs for these
                        for config_data in override_configs.values():
                            if self._change_affects_config(change, config_data):
                                report.add_affected_change(change)
                                added_change_ids.add(change.id)
                                break
        
        # Add remaining changes as unaffected
        for change in all_changes:
            if change.id not in added_change_ids:
                report.add_unaffected_change(change)
        
        return report
    
    def _change_affects_config(
        self,
        change: BreakingChange,
        config_data: Dict[str, Any]
    ) -> bool:
        """
        Check if a breaking change affects a specific configuration.
        
        Args:
            change: Breaking change to check
            config_data: Configuration data to check against
        
        Returns:
            True if the change affects this configuration
        """
        # If no detection pattern, can't determine from config alone
        if not change.detection_pattern:
            return False
        
        # Convert config to flat string for pattern matching
        config_str = self._flatten_config(config_data)
        
        # Check if pattern exists in config
        try:
            pattern = re.compile(change.detection_pattern, re.IGNORECASE)
            if pattern.search(config_str):
                # If detection_section specified, check if in right section
                if change.detection_section:
                    return self._pattern_in_section(
                        change.detection_pattern,
                        change.detection_section,
                        config_data
                    )
                return True
        except re.error:
            # Invalid regex pattern, fall back to simple string search
            if change.detection_pattern.lower() in config_str.lower():
                return True
        
        return False
    
    def _flatten_config(self, config_data: Dict[str, Any], prefix: str = '') -> str:
        """
        Flatten nested config dict to string for pattern matching.
        
        Args:
            config_data: Configuration data
            prefix: Key prefix for nested dicts
        
        Returns:
            Flattened string representation
        """
        result = []
        
        for key, value in config_data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                result.append(self._flatten_config(value, full_key))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        result.append(self._flatten_config(item, full_key))
                    else:
                        result.append(f"{full_key}={item}")
            else:
                result.append(f"{full_key}={value}")
        
        return " ".join(result)
    
    def _pattern_in_section(
        self,
        pattern: str,
        section: str,
        config_data: Dict[str, Any]
    ) -> bool:
        """
        Check if pattern exists in a specific config section.
        
        Args:
            pattern: Pattern to search for
            section: Section name to search in (can be partial path)
            config_data: Configuration data
        
        Returns:
            True if pattern found in section
        """
        # Try to find the section anywhere in the config tree
        section_data = self._find_section_recursive(config_data, section)
        if not section_data:
            return False
        
        # Check pattern in section
        section_str = self._flatten_config(section_data)
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            return bool(regex.search(section_str))
        except re.error:
            return pattern.lower() in section_str.lower()
    
    def _find_section_recursive(
        self,
        config_data: Dict[str, Any],
        section_name: str
    ) -> Dict[str, Any]:
        """
        Recursively search for a section by name in config tree.
        
        Args:
            config_data: Configuration data to search
            section_name: Section name to find
        
        Returns:
            Section data if found, empty dict otherwise
        """
        if not isinstance(config_data, dict):
            return {}
        
        # Check if this level has the section
        for key, value in config_data.items():
            if key.lower() == section_name.lower():
                return value if isinstance(value, dict) else {}
            
            # Recursively search nested dicts
            if isinstance(value, dict):
                result = self._find_section_recursive(value, section_name)
                if result:
                    return result
        
        return {}
    
    def _get_section(
        self,
        config_data: Dict[str, Any],
        section_path: str
    ) -> Dict[str, Any]:
        """
        Get a nested section from config data.
        
        Args:
            config_data: Configuration data
            section_path: Dot-separated path to section (e.g., 'conf.nova.oslo_messaging_rabbit')
        
        Returns:
            Section data if found, empty dict otherwise
        """
        parts = section_path.split('.')
        current = config_data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                # Try case-insensitive match
                if isinstance(current, dict):
                    for key in current.keys():
                        if key.lower() == part.lower():
                            current = current[key]
                            break
                    else:
                        return {}
                else:
                    return {}
        
        return current if isinstance(current, dict) else {}
    
    def generate_mitigation_plan(self, report: ImpactReport) -> MitigationPlan:
        """
        Generate a mitigation plan for affected breaking changes.
        
        Args:
            report: Impact report with affected changes
        
        Returns:
            MitigationPlan with required, recommended, and optional actions
        """
        plan = MitigationPlan(changes=report.get_sorted_changes())
        
        # Generate actions for each affected change
        for change in report.get_sorted_changes():
            action = f"[{change.component}] {change.title}: {change.mitigation}"
            plan.add_action(action, change.severity)
        
        return plan
    
    def prioritize_changes(
        self,
        changes: List[BreakingChange]
    ) -> List[BreakingChange]:
        """
        Sort breaking changes by priority (severity).
        
        Args:
            changes: List of breaking changes
        
        Returns:
            Sorted list (critical first, low last)
        """
        return sorted(changes, key=lambda x: x.priority)
