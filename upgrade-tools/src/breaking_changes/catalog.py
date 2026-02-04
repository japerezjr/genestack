"""Breaking change catalog loader and manager."""

import os
import yaml
from typing import List, Dict, Any
from pathlib import Path

from .models import BreakingChange


class BreakingChangeCatalog:
    """Manages the catalog of known breaking changes."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the breaking change catalog.
        
        Args:
            config_path: Path to breaking-changes.yaml file.
                        If None, uses default location.
        """
        if config_path is None:
            # Default to config/breaking-changes.yaml relative to this file
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "breaking-changes.yaml"
        
        self.config_path = Path(config_path)
        self.breaking_changes: List[BreakingChange] = []
        self.severity_levels: Dict[str, Any] = {}
        self.change_types: Dict[str, Any] = {}
        
        if self.config_path.exists():
            self._load_catalog()
    
    def _load_catalog(self):
        """Load breaking changes from YAML configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Load severity levels and change types
            self.severity_levels = data.get('severity_levels', {})
            self.change_types = data.get('change_types', {})
            
            # Load breaking changes
            changes_data = data.get('breaking_changes', [])
            for change_data in changes_data:
                change = BreakingChange(
                    id=change_data['id'],
                    component=change_data['component'],
                    change_type=change_data['change_type'],
                    title=change_data['title'],
                    description=change_data['description'],
                    impact=change_data['impact'],
                    mitigation=change_data['mitigation'],
                    severity=change_data['severity'],
                    affects_services=change_data['affects_services'],
                    detection_pattern=change_data.get('detection_pattern'),
                    detection_section=change_data.get('detection_section')
                )
                self.breaking_changes.append(change)
        
        except FileNotFoundError:
            raise FileNotFoundError(f"Breaking changes configuration not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in breaking changes configuration: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field in breaking changes configuration: {e}")
    
    def get_all_changes(self) -> List[BreakingChange]:
        """Get all breaking changes in the catalog."""
        return self.breaking_changes.copy()
    
    def get_changes_by_component(self, component: str) -> List[BreakingChange]:
        """
        Get breaking changes for a specific component.
        
        Args:
            component: Component name (e.g., 'nova', 'neutron', 'oslo.messaging')
        
        Returns:
            List of breaking changes for the component
        """
        return [
            change for change in self.breaking_changes
            if change.component == component
        ]
    
    def get_changes_by_severity(self, severity: str) -> List[BreakingChange]:
        """
        Get breaking changes by severity level.
        
        Args:
            severity: Severity level ('critical', 'high', 'medium', 'low')
        
        Returns:
            List of breaking changes with the specified severity
        """
        return [
            change for change in self.breaking_changes
            if change.severity == severity
        ]
    
    def get_changes_by_service(self, service: str) -> List[BreakingChange]:
        """
        Get breaking changes that affect a specific service.
        
        Args:
            service: Service name (e.g., 'nova', 'neutron')
        
        Returns:
            List of breaking changes affecting the service
        """
        return [
            change for change in self.breaking_changes
            if change.matches_service(service)
        ]
    
    def get_critical_changes(self) -> List[BreakingChange]:
        """Get all critical breaking changes."""
        return self.get_changes_by_severity('critical')
    
    def get_high_priority_changes(self) -> List[BreakingChange]:
        """Get all critical and high severity breaking changes."""
        critical = self.get_changes_by_severity('critical')
        high = self.get_changes_by_severity('high')
        return critical + high
    
    def get_changes_by_type(self, change_type: str) -> List[BreakingChange]:
        """
        Get breaking changes by type.
        
        Args:
            change_type: Type of change ('config', 'api', 'database', 'dependency')
        
        Returns:
            List of breaking changes of the specified type
        """
        return [
            change for change in self.breaking_changes
            if change.change_type == change_type
        ]
    
    def get_severity_description(self, severity: str) -> str:
        """Get description for a severity level."""
        level = self.severity_levels.get(severity, {})
        return level.get('description', 'No description available')
    
    def get_severity_priority(self, severity: str) -> int:
        """Get numeric priority for a severity level."""
        level = self.severity_levels.get(severity, {})
        return level.get('priority', 99)
    
    def get_change_type_description(self, change_type: str) -> str:
        """Get description for a change type."""
        ctype = self.change_types.get(change_type, {})
        return ctype.get('description', 'No description available')
    
    @property
    def total_changes(self) -> int:
        """Total number of breaking changes in catalog."""
        return len(self.breaking_changes)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about breaking changes in catalog."""
        stats = {
            'total': self.total_changes,
            'by_severity': {},
            'by_component': {},
            'by_type': {}
        }
        
        for change in self.breaking_changes:
            # Count by severity
            stats['by_severity'][change.severity] = \
                stats['by_severity'].get(change.severity, 0) + 1
            
            # Count by component
            stats['by_component'][change.component] = \
                stats['by_component'].get(change.component, 0) + 1
            
            # Count by type
            stats['by_type'][change.change_type] = \
                stats['by_type'].get(change.change_type, 0) + 1
        
        return stats
