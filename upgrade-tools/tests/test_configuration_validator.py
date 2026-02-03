"""Tests for main configuration validator."""

import pytest
import tempfile
from pathlib import Path

from src.validation.validator import ConfigurationValidator, ValidationReport


class TestConfigurationValidator:
    """Test suite for ConfigurationValidator."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory with test configurations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            # Create a valid config with Caracal versions
            (base / "keystone").mkdir()
            (base / "keystone" / "keystone-helm-overrides.yaml").write_text("""
images:
  tags:
    keystone_api: "ghcr.io/rackerlabs/genestack-images/keystone:2024.1-latest"
conf:
  keystone:
    oslo_messaging_rabbit:
      heartbeat_in_pthread: true
      heartbeat_rate: 3
""")
            
            # Create a config with only image issues
            (base / "nova").mkdir()
            (base / "nova" / "nova-helm-overrides.yaml").write_text("""
images:
  tags:
    nova_api: "ghcr.io/rackerlabs/genestack-images/nova:2024.2-latest"
conf:
  nova:
    DEFAULT:
      max_instances: 100
""")
            
            # Create an invalid YAML file
            (base / "neutron").mkdir()
            (base / "neutron" / "neutron-helm-overrides.yaml").write_text("""
images:
  tags:
    neutron_api: "test
    # Missing closing quote
""")
            
            # Create a clean config
            (base / "glance").mkdir()
            (base / "glance" / "glance-helm-overrides.yaml").write_text("""
images:
  tags:
    glance_api: "ghcr.io/rackerlabs/genestack-images/glance:2025.1-latest"
conf:
  glance:
    DEFAULT:
      workers: 4
""")
            
            yield base
    
    @pytest.fixture
    def deprecation_rules_file(self):
        """Create a temporary deprecation rules file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
deprecations:
  - component: oslo.messaging
    deprecated_options:
      - option: "conf.*.oslo_messaging_rabbit.heartbeat_in_pthread"
        replacement: "Remove this option"
        severity: high
        description: "Deprecated option"

patterns:
  - pattern: "heartbeat_in_pthread"
    component: "oslo.messaging"
    replacement: "Remove this option"
    severity: high
    description: "Deprecated in 2024.2"
""")
            f.flush()
            yield f.name
        Path(f.name).unlink()
    
    def test_validate_all(self, temp_config_dir, deprecation_rules_file):
        """Test complete validation workflow."""
        validator = ConfigurationValidator(
            str(temp_config_dir),
            deprecation_rules_file
        )
        
        report = validator.validate_all()
        
        assert report is not None
        assert report.total_files_scanned == 4
        assert report.files_with_issues > 0
        assert report.get_total_issues() > 0
    
    def test_validation_finds_yaml_errors(self, temp_config_dir, deprecation_rules_file):
        """Test that validation finds YAML errors."""
        validator = ConfigurationValidator(
            str(temp_config_dir),
            deprecation_rules_file
        )
        
        report = validator.validate_all()
        
        # Should find the invalid YAML in neutron config
        assert len(report.yaml_errors) > 0
        assert report.has_errors() is True
    
    def test_validation_finds_image_issues(self, temp_config_dir, deprecation_rules_file):
        """Test that validation finds image tag issues."""
        validator = ConfigurationValidator(
            str(temp_config_dir),
            deprecation_rules_file
        )
        
        report = validator.validate_all()
        
        # Should find Caracal versions in keystone and nova
        assert len(report.image_tag_issues) >= 2
    
    def test_validation_finds_deprecations(self, temp_config_dir, deprecation_rules_file):
        """Test that validation finds deprecated options."""
        validator = ConfigurationValidator(
            str(temp_config_dir),
            deprecation_rules_file
        )
        
        report = validator.validate_all()
        
        # Should find heartbeat_in_pthread in keystone config
        assert len(report.deprecation_issues) > 0
    
    def test_validation_report_to_dict(self, temp_config_dir, deprecation_rules_file):
        """Test converting report to dictionary."""
        validator = ConfigurationValidator(
            str(temp_config_dir),
            deprecation_rules_file
        )
        
        report = validator.validate_all()
        report_dict = report.to_dict()
        
        assert "timestamp" in report_dict
        assert "total_files_scanned" in report_dict
        assert "total_issues" in report_dict
        assert "has_errors" in report_dict
        assert "summary" in report_dict
    
    def test_validation_report_to_markdown(self, temp_config_dir, deprecation_rules_file):
        """Test generating markdown report."""
        validator = ConfigurationValidator(
            str(temp_config_dir),
            deprecation_rules_file
        )
        
        report = validator.validate_all()
        markdown = report.to_markdown()
        
        assert "# Configuration Validation Report" in markdown
        assert "## Summary" in markdown
        assert "Total Files Scanned" in markdown
        
        # Should include sections for issues found
        if report.yaml_errors:
            assert "## YAML Validation Errors" in markdown
        if report.image_tag_issues:
            assert "## Image Tag Updates Required" in markdown
        if report.deprecation_issues:
            assert "## Deprecated Configuration Options" in markdown
    
    def test_validation_report_save_to_file(self, temp_config_dir, deprecation_rules_file):
        """Test saving report to file."""
        validator = ConfigurationValidator(
            str(temp_config_dir),
            deprecation_rules_file
        )
        
        report = validator.validate_all()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.md"
            report.save_to_file(str(report_path), format="markdown")
            
            assert report_path.exists()
            content = report_path.read_text()
            assert "# Configuration Validation Report" in content
    
    def test_validation_report_save_json(self, temp_config_dir, deprecation_rules_file):
        """Test saving report as JSON."""
        validator = ConfigurationValidator(
            str(temp_config_dir),
            deprecation_rules_file
        )
        
        report = validator.validate_all()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            report.save_to_file(str(report_path), format="json")
            
            assert report_path.exists()
            
            import json
            with open(report_path) as f:
                data = json.load(f)
            
            assert "timestamp" in data
            assert "total_files_scanned" in data
    
    def test_validation_without_deprecation_rules(self, temp_config_dir):
        """Test validation without deprecation rules file."""
        validator = ConfigurationValidator(str(temp_config_dir))
        
        report = validator.validate_all()
        
        # Should still work, just no deprecation detection
        assert report is not None
        assert report.total_files_scanned > 0
    
    def test_has_critical_issues(self, temp_config_dir):
        """Test checking for critical issues."""
        # Create a config with critical deprecation
        critical_rules = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        critical_rules.write("""
deprecations:
  - component: test
    deprecated_options:
      - option: "conf.*.test.critical_option"
        replacement: "Fix immediately"
        severity: critical
        description: "Critical issue"
""")
        critical_rules.flush()
        
        # Add a file with the critical option
        (temp_config_dir / "test").mkdir()
        (temp_config_dir / "test" / "test-helm-overrides.yaml").write_text("""
conf:
  service:
    test:
      critical_option: true
""")
        
        validator = ConfigurationValidator(
            str(temp_config_dir),
            critical_rules.name
        )
        
        report = validator.validate_all()
        
        assert report.has_critical_issues() is True
        
        Path(critical_rules.name).unlink()


class TestValidationReport:
    """Test suite for ValidationReport."""
    
    def test_get_total_issues(self):
        """Test calculating total issues."""
        from datetime import datetime
        from src.validation.yaml_validator import ValidationIssue
        from src.validation.image_validator import ImageTagIssue
        from src.validation.deprecation_detector import DeprecationIssue, DeprecationRule
        
        report = ValidationReport(
            timestamp=datetime.now(),
            base_path="/test",
            total_files_scanned=5,
            files_with_issues=2
        )
        
        # Add some issues
        report.yaml_errors.append(ValidationIssue(
            severity="error",
            file_path="test.yaml",
            line_number=1,
            description="Error"
        ))
        
        report.image_tag_issues.append(ImageTagIssue(
            file_path="test.yaml",
            image_key="test",
            current_tag="old",
            recommended_tag="new",
            description="Update"
        ))
        
        rule = DeprecationRule(
            component="test",
            option="test",
            replacement="fix",
            severity="high",
            description="test"
        )
        report.deprecation_issues.append(DeprecationIssue(
            file_path="test.yaml",
            key_path="test",
            current_value="value",
            rule=rule
        ))
        
        assert report.get_total_issues() == 3
