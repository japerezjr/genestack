"""Data models for breaking changes."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BreakingChange:
    """Represents a breaking change between OpenStack releases."""
    
    id: str
    component: str
    change_type: str
    title: str
    description: str
    impact: str
    mitigation: str
    severity: str
    affects_services: List[str]
    detection_pattern: Optional[str] = None
    detection_section: Optional[str] = None
    affects_deployment: bool = False  # Set during impact analysis
    
    def __post_init__(self):
        """Validate severity level."""
        valid_severities = ['critical', 'high', 'medium', 'low']
        if self.severity not in valid_severities:
            raise ValueError(f"Invalid severity: {self.severity}. Must be one of {valid_severities}")
        
        valid_types = ['config', 'api', 'database', 'dependency']
        if self.change_type not in valid_types:
            raise ValueError(f"Invalid change_type: {self.change_type}. Must be one of {valid_types}")
    
    @property
    def priority(self) -> int:
        """Get numeric priority based on severity."""
        severity_priority = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        }
        return severity_priority.get(self.severity, 5)
    
    def matches_service(self, service: str) -> bool:
        """Check if this breaking change affects a specific service."""
        return 'all' in self.affects_services or service in self.affects_services


@dataclass
class ImpactReport:
    """Report of breaking changes that affect the current deployment."""
    
    affected_changes: List[BreakingChange] = field(default_factory=list)
    unaffected_changes: List[BreakingChange] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    def add_affected_change(self, change: BreakingChange):
        """Add a breaking change that affects the deployment."""
        change.affects_deployment = True
        self.affected_changes.append(change)
        self._update_counts(change)
    
    def add_unaffected_change(self, change: BreakingChange):
        """Add a breaking change that does not affect the deployment."""
        change.affects_deployment = False
        self.unaffected_changes.append(change)
    
    def _update_counts(self, change: BreakingChange):
        """Update severity counts."""
        if change.severity == 'critical':
            self.critical_count += 1
        elif change.severity == 'high':
            self.high_count += 1
        elif change.severity == 'medium':
            self.medium_count += 1
        elif change.severity == 'low':
            self.low_count += 1
    
    @property
    def total_affected(self) -> int:
        """Total number of breaking changes affecting deployment."""
        return len(self.affected_changes)
    
    @property
    def has_critical_issues(self) -> bool:
        """Check if there are any critical breaking changes."""
        return self.critical_count > 0
    
    @property
    def has_blocking_issues(self) -> bool:
        """Check if there are critical or high severity issues."""
        return self.critical_count > 0 or self.high_count > 0
    
    def get_sorted_changes(self) -> List[BreakingChange]:
        """Get affected changes sorted by priority (critical first)."""
        return sorted(self.affected_changes, key=lambda x: x.priority)


@dataclass
class MitigationPlan:
    """Plan for addressing breaking changes."""
    
    changes: List[BreakingChange]
    required_actions: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    optional_actions: List[str] = field(default_factory=list)
    
    def add_action(self, action: str, severity: str):
        """Add an action to the appropriate list based on severity."""
        if severity in ['critical', 'high']:
            self.required_actions.append(action)
        elif severity == 'medium':
            self.recommended_actions.append(action)
        else:
            self.optional_actions.append(action)
    
    @property
    def has_required_actions(self) -> bool:
        """Check if there are required actions."""
        return len(self.required_actions) > 0
