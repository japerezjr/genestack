# Configuration Validation

The Configuration Validator is a comprehensive tool for validating OpenStack helm configuration files before upgrading from Caracal (2024.1/2024.2) to Epoxy (2025.1).

## Features

The validator performs the following checks:

1. **YAML Syntax Validation**
   - Validates YAML syntax and structure
   - Reports parsing errors with line numbers
   - Checks for required configuration sections

2. **Image Tag Validation**
   - Detects Caracal version strings (2024.1, 2024.2) in image tags
   - Generates recommendations for updating to Epoxy (2025.1)
   - Supports nested configuration structures

3. **Deprecated Option Detection**
   - Scans for deprecated configuration options
   - Provides replacement recommendations
   - Categorizes issues by severity (critical, high, medium, low)
   - Supports pattern-based and exact matching

4. **Comprehensive Reporting**
   - Generates detailed validation reports
   - Supports multiple output formats (Markdown, JSON, text)
   - Groups issues by file, component, and severity
   - Provides actionable remediation steps

## Usage

### Command Line

```bash
# Basic usage
python scripts/validate_configs.py ../base-helm-configs

# Save report to file
python scripts/validate_configs.py ../base-helm-configs --report validation-report.md

# Use custom deprecation rules
python scripts/validate_configs.py ../base-helm-configs \
    --deprecation-rules custom-rules.yaml

# Generate JSON report
python scripts/validate_configs.py ../base-helm-configs \
    --report validation-report.json \
    --format json

# Enable verbose logging
python scripts/validate_configs.py ../base-helm-configs --verbose
```

### Python API

```python
from validation.validator import ConfigurationValidator

# Create validator
validator = ConfigurationValidator(
    base_path="base-helm-configs/",
    deprecation_rules_file="config/deprecation-rules.yaml"
)

# Run validation
report = validator.validate_all()

# Check results
if report.has_errors():
    print("Validation failed with errors")
    for error in report.yaml_errors:
        print(f"  {error}")

if report.has_critical_issues():
    print("Critical deprecation issues found")
    for issue in report.deprecation_issues:
        if issue.rule.severity == "critical":
            print(f"  {issue}")

# Save report
report.save_to_file("validation-report.md", format="markdown")
```

## Components

### ConfigurationScanner

Recursively scans directories for YAML configuration files.

```python
from validation.scanner import ConfigurationScanner

scanner = ConfigurationScanner("base-helm-configs/")
files = scanner.scan()

# Filter by pattern
helm_overrides = scanner.filter_by_pattern("*-helm-overrides.yaml")

# Group by service
by_service = scanner.get_files_by_service()
```

### YAMLValidator

Validates YAML syntax and structure.

```python
from validation.yaml_validator import YAMLValidator

validator = YAMLValidator()
is_valid, content = validator.validate_file("config.yaml")

if not is_valid:
    errors = validator.get_issues(severity="error")
    for error in errors:
        print(error)
```

### ImageTagValidator

Detects and recommends updates for Caracal version strings in image tags.

```python
from validation.image_validator import ImageTagValidator

validator = ImageTagValidator()
issues = validator.validate_config(config, "keystone-helm-overrides.yaml")

# Generate recommendations
recommendations = validator.generate_update_recommendations()

# Apply recommendations
updated_config = validator.apply_recommendations(config, "keystone-helm-overrides.yaml")
```

### DeprecationDetector

Detects deprecated configuration options based on rules.

```python
from validation.deprecation_detector import DeprecationDetector

detector = DeprecationDetector("config/deprecation-rules.yaml")
issues = detector.scan_config(config, "keystone-helm-overrides.yaml")

# Get critical issues
critical = detector.get_issues(severity="critical")

# Generate remediation plan
plan = detector.generate_remediation_plan()
```

## Deprecation Rules

Deprecation rules are defined in YAML format:

```yaml
deprecations:
  - component: oslo.messaging
    deprecated_options:
      - option: "conf.*.oslo_messaging_rabbit.heartbeat_in_pthread"
        replacement: "Remove this option"
        severity: high
        description: "Deprecated in 2024.2"

patterns:
  - pattern: "linuxbridge"
    component: "neutron"
    replacement: "Use OVS or OVN"
    severity: high
    description: "Linux Bridge driver removed"
```

### Rule Types

1. **Explicit Rules**: Match exact configuration paths with wildcard support
   - Example: `conf.*.oslo_messaging_rabbit.heartbeat_in_pthread`
   - Wildcards (`*`) match any single path component

2. **Pattern Rules**: Match any occurrence of a pattern in the configuration
   - Example: `linuxbridge` matches anywhere in the config
   - Uses substring and regex matching

### Severity Levels

- **critical**: Must be fixed before upgrade (e.g., removed features)
- **high**: Should be fixed before upgrade (e.g., deprecated options)
- **medium**: Recommended to fix (e.g., renamed options)
- **low**: Optional improvements (e.g., discouraged practices)

## Exit Codes

The validation script uses the following exit codes:

- `0`: Validation passed with no issues
- `1`: Validation failed with YAML errors
- `2`: Validation found critical deprecation issues
- `3`: Validation found non-critical issues

## Examples

### Example 1: Validate All Configurations

```bash
python scripts/validate_configs.py ../base-helm-configs \
    --report validation-report.md
```

Output:
```
================================================================================
VALIDATION SUMMARY
================================================================================
Files scanned: 45
Files with issues: 12
Total issues: 28
  - YAML errors: 0
  - YAML warnings: 2
  - Image tag issues: 18
  - Deprecated options: 8
================================================================================
Report saved to: validation-report.md
```

### Example 2: Check Specific Service

```python
from validation.validator import ConfigurationValidator

validator = ConfigurationValidator("base-helm-configs/keystone")
report = validator.validate_all()

print(f"Issues found: {report.get_total_issues()}")
```

### Example 3: Custom Deprecation Rules

Create a custom rules file:

```yaml
# custom-rules.yaml
deprecations:
  - component: custom
    deprecated_options:
      - option: "conf.*.custom.old_option"
        replacement: "Use new_option instead"
        severity: medium
        description: "Custom deprecation"
```

Run validation:

```bash
python scripts/validate_configs.py ../base-helm-configs \
    --deprecation-rules custom-rules.yaml
```

## Testing

Run the test suite:

```bash
# Run all validation tests
pytest tests/test_config_scanner.py -v
pytest tests/test_yaml_validator.py -v
pytest tests/test_image_validator.py -v
pytest tests/test_deprecation_detector.py -v
pytest tests/test_configuration_validator.py -v

# Run all tests
pytest tests/ -v
```

## Integration with Upgrade Workflow

The Configuration Validator is designed to be used as part of the complete upgrade workflow:

1. **Pre-Upgrade Validation**: Run validator before starting upgrade
2. **Fix Issues**: Address all errors and critical issues
3. **Update Configurations**: Apply recommended changes
4. **Re-Validate**: Confirm all issues are resolved
5. **Proceed with Upgrade**: Execute helm chart updates

## Troubleshooting

### Common Issues

**Issue**: "No deprecation rules file found"
- **Solution**: Specify rules file with `--deprecation-rules` or ensure `config/deprecation-rules.yaml` exists

**Issue**: "Permission denied accessing directory"
- **Solution**: Check file permissions or run with appropriate privileges

**Issue**: "YAML parsing error"
- **Solution**: Fix YAML syntax errors reported in the validation output

### Debug Mode

Enable verbose logging for detailed information:

```bash
python scripts/validate_configs.py ../base-helm-configs --verbose
```

## Future Enhancements

Planned improvements:

- Automatic configuration updates
- Integration with CI/CD pipelines
- Support for custom validation rules
- Performance optimization for large deployments
- Interactive remediation mode
