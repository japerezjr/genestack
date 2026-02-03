"""Tests for YAML validator."""

import pytest
import tempfile
from pathlib import Path

from src.validation.yaml_validator import YAMLValidator, ValidationIssue


class TestYAMLValidator:
    """Test suite for YAMLValidator."""
    
    @pytest.fixture
    def validator(self):
        """Create a fresh validator instance."""
        return YAMLValidator()
    
    @pytest.fixture
    def valid_yaml_file(self):
        """Create a temporary valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
images:
  tags:
    keystone_api: "ghcr.io/rackerlabs/genestack-images/keystone:2024.1-latest"
conf:
  keystone:
    DEFAULT:
      max_token_size: 300
pod:
  resources:
    enabled: true
""")
            f.flush()
            yield f.name
        Path(f.name).unlink()
    
    @pytest.fixture
    def invalid_yaml_file(self):
        """Create a temporary invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
images:
  tags:
    keystone_api: "test
    # Missing closing quote - invalid YAML
""")
            f.flush()
            yield f.name
        Path(f.name).unlink()
    
    @pytest.fixture
    def empty_yaml_file(self):
        """Create a temporary empty YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            f.flush()
            yield f.name
        Path(f.name).unlink()
    
    def test_validate_valid_yaml(self, validator, valid_yaml_file):
        """Test validation of valid YAML file."""
        is_valid, content = validator.validate_file(valid_yaml_file)
        
        assert is_valid is True
        assert content is not None
        assert isinstance(content, dict)
        assert 'images' in content
        assert not validator.has_errors()
    
    def test_validate_invalid_yaml(self, validator, invalid_yaml_file):
        """Test validation of invalid YAML file."""
        is_valid, content = validator.validate_file(invalid_yaml_file)
        
        assert is_valid is False
        assert content is None
        assert validator.has_errors()
        
        errors = validator.get_issues(severity="error")
        assert len(errors) > 0
        assert "Invalid YAML syntax" in errors[0].description
    
    def test_validate_empty_yaml(self, validator, empty_yaml_file):
        """Test validation of empty YAML file."""
        is_valid, content = validator.validate_file(empty_yaml_file)
        
        assert is_valid is True
        assert content == {}
        
        warnings = validator.get_issues(severity="warning")
        assert len(warnings) > 0
        assert "empty" in warnings[0].description.lower()
    
    def test_validate_nonexistent_file(self, validator):
        """Test validation of nonexistent file."""
        is_valid, content = validator.validate_file("/nonexistent/file.yaml")
        
        assert is_valid is False
        assert content is None
        assert validator.has_errors()
        
        errors = validator.get_issues(severity="error")
        assert "does not exist" in errors[0].description
    
    def test_validate_structure_required_keys(self, validator):
        """Test structure validation with required keys."""
        content = {"images": {}, "conf": {}}
        file_path = "test.yaml"
        
        # Should pass with required keys present
        is_valid = validator.validate_structure(
            content,
            file_path,
            required_keys=["images", "conf"]
        )
        assert is_valid is True
        
        # Should fail with missing required key
        validator.clear_issues()
        is_valid = validator.validate_structure(
            content,
            file_path,
            required_keys=["images", "conf", "pod"]
        )
        assert is_valid is False
        assert validator.has_errors()
    
    def test_validate_structure_expected_types(self, validator):
        """Test structure validation with expected types."""
        content = {
            "images": {},
            "enabled": True,
            "count": 5
        }
        file_path = "test.yaml"
        
        # Should pass with correct types
        is_valid = validator.validate_structure(
            content,
            file_path,
            expected_types={"images": dict, "enabled": bool, "count": int}
        )
        assert is_valid is True
        
        # Should fail with wrong type
        validator.clear_issues()
        is_valid = validator.validate_structure(
            content,
            file_path,
            expected_types={"images": list}  # Wrong type
        )
        assert is_valid is False
        assert validator.has_errors()
    
    def test_validate_helm_override(self, validator, valid_yaml_file):
        """Test helm override validation."""
        is_valid, content = validator.validate_helm_override(valid_yaml_file)
        
        assert is_valid is True
        assert content is not None
        assert isinstance(content, dict)
    
    def test_validate_helm_override_invalid_structure(self, validator):
        """Test helm override validation with invalid structure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            # Write a YAML list instead of dict
            f.write("- item1\n- item2\n")
            f.flush()
            
            is_valid, content = validator.validate_helm_override(f.name)
            
            assert is_valid is False
            assert validator.has_errors()
            
            Path(f.name).unlink()
    
    def test_get_issues_filtered(self, validator):
        """Test getting issues filtered by severity."""
        # Add issues of different severities
        validator.issues.append(ValidationIssue(
            severity="error",
            file_path="test1.yaml",
            line_number=1,
            description="Error 1"
        ))
        validator.issues.append(ValidationIssue(
            severity="warning",
            file_path="test2.yaml",
            line_number=2,
            description="Warning 1"
        ))
        validator.issues.append(ValidationIssue(
            severity="error",
            file_path="test3.yaml",
            line_number=3,
            description="Error 2"
        ))
        
        errors = validator.get_issues(severity="error")
        warnings = validator.get_issues(severity="warning")
        all_issues = validator.get_issues()
        
        assert len(errors) == 2
        assert len(warnings) == 1
        assert len(all_issues) == 3
    
    def test_get_summary(self, validator):
        """Test getting summary of issues."""
        validator.issues.append(ValidationIssue(
            severity="error",
            file_path="test1.yaml",
            line_number=1,
            description="Error 1"
        ))
        validator.issues.append(ValidationIssue(
            severity="error",
            file_path="test2.yaml",
            line_number=2,
            description="Error 2"
        ))
        validator.issues.append(ValidationIssue(
            severity="warning",
            file_path="test3.yaml",
            line_number=3,
            description="Warning 1"
        ))
        
        summary = validator.get_summary()
        
        assert summary["error"] == 2
        assert summary["warning"] == 1
        assert summary["info"] == 0
    
    def test_clear_issues(self, validator):
        """Test clearing issues."""
        validator.issues.append(ValidationIssue(
            severity="error",
            file_path="test.yaml",
            line_number=1,
            description="Error"
        ))
        
        assert len(validator.issues) > 0
        
        validator.clear_issues()
        
        assert len(validator.issues) == 0
    
    def test_validation_issue_str(self):
        """Test ValidationIssue string representation."""
        issue = ValidationIssue(
            severity="error",
            file_path="test.yaml",
            line_number=42,
            description="Test error",
            remediation="Fix it"
        )
        
        issue_str = str(issue)
        
        assert "ERROR" in issue_str
        assert "test.yaml:42" in issue_str
        assert "Test error" in issue_str
        assert "Fix it" in issue_str
