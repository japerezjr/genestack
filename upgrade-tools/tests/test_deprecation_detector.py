"""Tests for deprecation detector."""

import pytest
import tempfile
from pathlib import Path

from src.validation.deprecation_detector import (
    DeprecationDetector,
    DeprecationRule,
    DeprecationIssue
)


class TestDeprecationDetector:
    """Test suite for DeprecationDetector."""
    
    @pytest.fixture
    def sample_rules_file(self):
        """Create a temporary rules file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
deprecations:
  - component: oslo.messaging
    deprecated_options:
      - option: "conf.*.oslo_messaging_rabbit.heartbeat_in_pthread"
        replacement: "Remove this option"
        severity: high
        description: "Deprecated option"
      
      - option: "conf.*.oslo_messaging_rabbit.kombu_ssl_version"
        replacement: "Use ssl_version instead"
        severity: medium
        description: "Use non-prefixed option"

patterns:
  - pattern: "linuxbridge"
    component: "neutron"
    replacement: "Use OVS or OVN"
    severity: high
    description: "Linux Bridge removed"
""")
            f.flush()
            yield f.name
        Path(f.name).unlink()
    
    @pytest.fixture
    def detector(self, sample_rules_file):
        """Create a detector with sample rules."""
        return DeprecationDetector(sample_rules_file)
    
    @pytest.fixture
    def config_with_deprecated_options(self):
        """Sample configuration with deprecated options."""
        return {
            "conf": {
                "keystone": {
                    "oslo_messaging_rabbit": {
                        "heartbeat_in_pthread": True,
                        "heartbeat_rate": 3
                    }
                }
            }
        }
    
    def test_load_rules(self, sample_rules_file):
        """Test loading deprecation rules."""
        detector = DeprecationDetector(sample_rules_file)
        
        assert len(detector.rules) > 0
        
        # Check that both explicit and pattern rules were loaded
        explicit_rules = [r for r in detector.rules if not r.is_pattern]
        pattern_rules = [r for r in detector.rules if r.is_pattern]
        
        assert len(explicit_rules) > 0
        assert len(pattern_rules) > 0
    
    def test_rule_matches_exact(self):
        """Test exact rule matching."""
        rule = DeprecationRule(
            component="test",
            option="conf.keystone.oslo_messaging_rabbit.heartbeat_in_pthread",
            replacement="Remove",
            severity="high",
            description="Test",
            is_pattern=False
        )
        
        assert rule.matches("conf.keystone.oslo_messaging_rabbit.heartbeat_in_pthread") is True
        assert rule.matches("conf.keystone.oslo_messaging_rabbit.other_option") is False
    
    def test_rule_matches_wildcard(self):
        """Test wildcard rule matching."""
        rule = DeprecationRule(
            component="test",
            option="conf.*.oslo_messaging_rabbit.heartbeat_in_pthread",
            replacement="Remove",
            severity="high",
            description="Test",
            is_pattern=False
        )
        
        assert rule.matches("conf.keystone.oslo_messaging_rabbit.heartbeat_in_pthread") is True
        assert rule.matches("conf.nova.oslo_messaging_rabbit.heartbeat_in_pthread") is True
        assert rule.matches("conf.keystone.other_section.heartbeat_in_pthread") is False
    
    def test_rule_matches_pattern(self):
        """Test pattern-based rule matching."""
        rule = DeprecationRule(
            component="test",
            option="linuxbridge",
            replacement="Use OVS",
            severity="high",
            description="Test",
            is_pattern=True
        )
        
        assert rule.matches("conf.neutron.mechanism_drivers.linuxbridge") is True
        assert rule.matches("conf.neutron.linuxbridge.enabled") is True
        assert rule.matches("conf.neutron.ovs.enabled") is False
    
    def test_scan_config_finds_deprecated_options(self, detector, config_with_deprecated_options):
        """Test scanning configuration for deprecated options."""
        issues = detector.scan_config(config_with_deprecated_options, "test.yaml")
        
        assert len(issues) > 0
        
        # Should find heartbeat_in_pthread
        heartbeat_issues = [i for i in issues if "heartbeat_in_pthread" in i.key_path]
        assert len(heartbeat_issues) > 0
    
    def test_scan_config_no_issues(self, detector):
        """Test scanning configuration with no deprecated options."""
        clean_config = {
            "conf": {
                "keystone": {
                    "oslo_messaging_rabbit": {
                        "heartbeat_rate": 3,
                        "heartbeat_timeout_threshold": 60
                    }
                }
            }
        }
        
        issues = detector.scan_config(clean_config, "test.yaml")
        
        assert len(issues) == 0
    
    def test_scan_nested_config(self, detector):
        """Test scanning deeply nested configuration."""
        nested_config = {
            "conf": {
                "nova": {
                    "oslo_messaging_rabbit": {
                        "kombu_ssl_version": "TLSv1.2"
                    }
                }
            }
        }
        
        issues = detector.scan_config(nested_config, "test.yaml")
        
        assert len(issues) > 0
        assert any("kombu_ssl_version" in i.key_path for i in issues)
    
    def test_get_issues_by_severity(self, detector, config_with_deprecated_options):
        """Test filtering issues by severity."""
        detector.scan_config(config_with_deprecated_options, "test.yaml")
        
        high_issues = detector.get_issues(severity="high")
        medium_issues = detector.get_issues(severity="medium")
        
        assert len(high_issues) > 0
        assert all(i.rule.severity == "high" for i in high_issues)
    
    def test_get_issues_by_file(self, detector):
        """Test grouping issues by file."""
        config1 = {
            "conf": {
                "keystone": {
                    "oslo_messaging_rabbit": {
                        "heartbeat_in_pthread": True
                    }
                }
            }
        }
        config2 = {
            "conf": {
                "nova": {
                    "oslo_messaging_rabbit": {
                        "kombu_ssl_version": "TLSv1.2"
                    }
                }
            }
        }
        
        detector.scan_config(config1, "file1.yaml")
        detector.scan_config(config2, "file2.yaml")
        
        by_file = detector.get_issues_by_file()
        
        assert "file1.yaml" in by_file
        assert "file2.yaml" in by_file
        assert len(by_file["file1.yaml"]) > 0
        assert len(by_file["file2.yaml"]) > 0
    
    def test_get_issues_by_component(self, detector, config_with_deprecated_options):
        """Test grouping issues by component."""
        detector.scan_config(config_with_deprecated_options, "test.yaml")
        
        by_component = detector.get_issues_by_component()
        
        assert "oslo.messaging" in by_component
        assert len(by_component["oslo.messaging"]) > 0
    
    def test_get_summary(self, detector, config_with_deprecated_options):
        """Test summary generation."""
        detector.scan_config(config_with_deprecated_options, "test.yaml")
        
        summary = detector.get_summary()
        
        assert "total_issues" in summary
        assert "files_affected" in summary
        assert "components_affected" in summary
        assert "by_severity" in summary
        
        assert summary["total_issues"] > 0
        assert summary["files_affected"] == 1
    
    def test_generate_remediation_plan(self, detector, config_with_deprecated_options):
        """Test remediation plan generation."""
        detector.scan_config(config_with_deprecated_options, "test.yaml")
        
        plan = detector.generate_remediation_plan()
        
        assert len(plan) > 0
        assert all("file" in item for item in plan)
        assert all("key" in item for item in plan)
        assert all("action" in item for item in plan)
        assert all("severity" in item for item in plan)
        
        # Check that plan is sorted by severity (critical first)
        severities = [item["severity"] for item in plan]
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        severity_values = [severity_order.get(s, 4) for s in severities]
        assert severity_values == sorted(severity_values)
    
    def test_has_critical_issues(self, detector):
        """Test checking for critical issues."""
        # No critical issues initially
        assert detector.has_critical_issues() is False
        
        # Add a critical issue manually
        critical_rule = DeprecationRule(
            component="test",
            option="test.option",
            replacement="Fix it",
            severity="critical",
            description="Critical issue"
        )
        critical_issue = DeprecationIssue(
            file_path="test.yaml",
            key_path="test.option",
            current_value="value",
            rule=critical_rule
        )
        detector.issues.append(critical_issue)
        
        assert detector.has_critical_issues() is True
    
    def test_clear_issues(self, detector, config_with_deprecated_options):
        """Test clearing issues."""
        detector.scan_config(config_with_deprecated_options, "test.yaml")
        
        assert len(detector.issues) > 0
        
        detector.clear_issues()
        
        assert len(detector.issues) == 0
    
    def test_deprecation_issue_str(self):
        """Test DeprecationIssue string representation."""
        rule = DeprecationRule(
            component="oslo.messaging",
            option="test.option",
            replacement="Remove it",
            severity="high",
            description="Test deprecation"
        )
        issue = DeprecationIssue(
            file_path="test.yaml",
            key_path="conf.keystone.test.option",
            current_value=True,
            rule=rule
        )
        
        issue_str = str(issue)
        
        assert "HIGH" in issue_str
        assert "test.yaml" in issue_str
        assert "oslo.messaging" in issue_str
        assert "Remove it" in issue_str
