"""YAML validation logic for configuration files."""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a configuration file."""
    
    severity: str  # "error", "warning", "info"
    file_path: str
    line_number: Optional[int]
    description: str
    remediation: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of the issue."""
        location = f"{self.file_path}"
        if self.line_number:
            location += f":{self.line_number}"
        
        msg = f"[{self.severity.upper()}] {location}: {self.description}"
        if self.remediation:
            msg += f"\n  Remediation: {self.remediation}"
        return msg


class YAMLValidator:
    """
    Validator for YAML configuration files.
    
    This class parses YAML files with error handling and validates
    structure against expected schemas.
    """
    
    def __init__(self):
        """Initialize the YAML validator."""
        self.issues: List[ValidationIssue] = []
    
    def validate_file(self, file_path: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate a single YAML file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Tuple of (is_valid, parsed_content)
            - is_valid: True if file is valid YAML
            - parsed_content: Parsed YAML content or None if invalid
        """
        path = Path(file_path)
        
        # Check file exists
        if not path.exists():
            issue = ValidationIssue(
                severity="error",
                file_path=file_path,
                line_number=None,
                description="File does not exist",
                remediation="Ensure the file path is correct"
            )
            self.issues.append(issue)
            logger.error(str(issue))
            return False, None
        
        # Check file is readable
        if not path.is_file():
            issue = ValidationIssue(
                severity="error",
                file_path=file_path,
                line_number=None,
                description="Path is not a file",
                remediation="Ensure the path points to a file, not a directory"
            )
            self.issues.append(issue)
            logger.error(str(issue))
            return False, None
        
        # Try to read and parse the file
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file is empty
            if not content.strip():
                issue = ValidationIssue(
                    severity="warning",
                    file_path=file_path,
                    line_number=None,
                    description="File is empty",
                    remediation="Add configuration content or remove the file"
                )
                self.issues.append(issue)
                logger.warning(str(issue))
                return True, {}
            
            # Parse YAML
            try:
                parsed = yaml.safe_load(content)
                
                # Handle None result (empty YAML document)
                if parsed is None:
                    issue = ValidationIssue(
                        severity="warning",
                        file_path=file_path,
                        line_number=None,
                        description="YAML document is empty or contains only comments",
                        remediation="Add configuration content"
                    )
                    self.issues.append(issue)
                    logger.warning(str(issue))
                    return True, {}
                
                logger.debug(f"Successfully parsed YAML file: {file_path}")
                return True, parsed
            
            except yaml.YAMLError as e:
                # Extract line number from error if available
                line_number = None
                if hasattr(e, 'problem_mark'):
                    line_number = e.problem_mark.line + 1
                
                issue = ValidationIssue(
                    severity="error",
                    file_path=file_path,
                    line_number=line_number,
                    description=f"Invalid YAML syntax: {str(e)}",
                    remediation="Fix YAML syntax errors. Check for proper indentation, quotes, and structure."
                )
                self.issues.append(issue)
                logger.error(str(issue))
                return False, None
        
        except PermissionError:
            issue = ValidationIssue(
                severity="error",
                file_path=file_path,
                line_number=None,
                description="Permission denied reading file",
                remediation="Check file permissions"
            )
            self.issues.append(issue)
            logger.error(str(issue))
            return False, None
        
        except UnicodeDecodeError as e:
            issue = ValidationIssue(
                severity="error",
                file_path=file_path,
                line_number=None,
                description=f"File encoding error: {str(e)}",
                remediation="Ensure file is UTF-8 encoded"
            )
            self.issues.append(issue)
            logger.error(str(issue))
            return False, None
        
        except Exception as e:
            issue = ValidationIssue(
                severity="error",
                file_path=file_path,
                line_number=None,
                description=f"Unexpected error reading file: {str(e)}",
                remediation="Check file integrity and format"
            )
            self.issues.append(issue)
            logger.error(str(issue))
            return False, None
    
    def validate_structure(
        self,
        content: Dict[str, Any],
        file_path: str,
        required_keys: Optional[List[str]] = None,
        expected_types: Optional[Dict[str, type]] = None
    ) -> bool:
        """
        Validate the structure of parsed YAML content.
        
        Args:
            content: Parsed YAML content
            file_path: Path to the file (for error reporting)
            required_keys: List of required top-level keys
            expected_types: Dictionary mapping keys to expected types
            
        Returns:
            True if structure is valid
        """
        is_valid = True
        
        # Check required keys
        if required_keys:
            for key in required_keys:
                if key not in content:
                    issue = ValidationIssue(
                        severity="error",
                        file_path=file_path,
                        line_number=None,
                        description=f"Missing required key: '{key}'",
                        remediation=f"Add the '{key}' section to the configuration"
                    )
                    self.issues.append(issue)
                    logger.error(str(issue))
                    is_valid = False
        
        # Check expected types
        if expected_types:
            for key, expected_type in expected_types.items():
                if key in content:
                    actual_value = content[key]
                    if not isinstance(actual_value, expected_type):
                        issue = ValidationIssue(
                            severity="error",
                            file_path=file_path,
                            line_number=None,
                            description=f"Key '{key}' has wrong type: expected {expected_type.__name__}, got {type(actual_value).__name__}",
                            remediation=f"Ensure '{key}' is of type {expected_type.__name__}"
                        )
                        self.issues.append(issue)
                        logger.error(str(issue))
                        is_valid = False
        
        return is_valid
    
    def validate_helm_override(self, file_path: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate a helm override configuration file.
        
        This checks for common helm override structure and validates
        against expected schema.
        
        Args:
            file_path: Path to the helm override file
            
        Returns:
            Tuple of (is_valid, parsed_content)
        """
        # First validate YAML syntax
        is_valid, content = self.validate_file(file_path)
        
        if not is_valid or content is None:
            return False, None
        
        # Validate structure (helm overrides should be a dict)
        if not isinstance(content, dict):
            issue = ValidationIssue(
                severity="error",
                file_path=file_path,
                line_number=None,
                description="Helm override must be a YAML dictionary/mapping",
                remediation="Ensure the file contains a valid YAML dictionary structure"
            )
            self.issues.append(issue)
            logger.error(str(issue))
            return False, content
        
        # Check for common helm override sections (informational)
        common_sections = ['images', 'conf', 'pod', 'endpoints', 'manifests']
        found_sections = [s for s in common_sections if s in content]
        
        if not found_sections:
            issue = ValidationIssue(
                severity="info",
                file_path=file_path,
                line_number=None,
                description="No common helm override sections found (images, conf, pod, endpoints, manifests)",
                remediation="Verify this is a valid helm override file"
            )
            self.issues.append(issue)
            logger.info(str(issue))
        
        return True, content
    
    def get_issues(self, severity: Optional[str] = None) -> List[ValidationIssue]:
        """
        Get validation issues, optionally filtered by severity.
        
        Args:
            severity: Filter by severity ("error", "warning", "info")
            
        Returns:
            List of validation issues
        """
        if severity:
            return [i for i in self.issues if i.severity == severity]
        return self.issues
    
    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(i.severity == "error" for i in self.issues)
    
    def clear_issues(self) -> None:
        """Clear all validation issues."""
        self.issues = []
    
    def get_summary(self) -> Dict[str, int]:
        """
        Get a summary of validation issues by severity.
        
        Returns:
            Dictionary with counts by severity
        """
        summary = {"error": 0, "warning": 0, "info": 0}
        for issue in self.issues:
            if issue.severity in summary:
                summary[issue.severity] += 1
        return summary
