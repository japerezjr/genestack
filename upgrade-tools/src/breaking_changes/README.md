# Breaking Change Detection Module

This module provides comprehensive breaking change detection and analysis for OpenStack upgrades from Caracal (2024.1/2024.2) to Epoxy (2025.1).

## Overview

The Breaking Change Detector identifies configuration incompatibilities, deprecated options, and other breaking changes that could prevent a successful upgrade. It analyzes helm override configurations and generates detailed reports with mitigation steps.

## Components

### Models (`models.py`)

Data structures for representing breaking changes and analysis results:

- **BreakingChange**: Represents a single breaking change with metadata
- **ImpactReport**: Aggregates affected/unaffected changes with severity counts
- **MitigationPlan**: Organizes mitigation actions by priority

### Catalog (`catalog.py`)

Manages the catalog of known breaking changes:

- Loads breaking changes from YAML configuration
- Provides filtering by component, severity, service, type
- Generates statistics about the catalog

### Analyzer (`analyzer.py`)

Analyzes configurations for breaking changes:

- Pattern matching against configuration data
- Section-specific detection
- Impact assessment across entire deployment
- Mitigation plan generation

### Reporter (`reporter.py`)

Generates formatted reports:

- Multiple output formats (markdown, text, JSON)
- Impact reports showing affected changes
- Mitigation plans with actionable steps

### Detector (`detector.py`)

Main interface orchestrating all components:

- High-level API for detection and reporting
- Simplified usage for common workflows

## Usage

### Basic Detection

```python
from src.breaking_changes import BreakingChangeDetector

# Initialize detector
detector = BreakingChangeDetector()

# Analyze a configuration
config = {
    'conf': {
        'nova': {
            'oslo_messaging_rabbit': {
                'heartbeat_in_pthread': True
            }
        }
    }
}

# Detect breaking changes
report = detector.detect_in_configuration(config, 'nova')

# Check results
if report.has_critical_issues:
    print(f"Found {report.critical_count} critical issues!")
    for change in report.get_sorted_changes():
        print(f"- {change.title}: {change.mitigation}")
```

### Deployment Analysis

```python
# Analyze entire deployment
override_configs = {
    'nova': load_yaml('nova-helm-overrides.yaml'),
    'neutron': load_yaml('neutron-helm-overrides.yaml'),
    # ... more services
}

report = detector.detect_in_deployment(override_configs)

# Generate reports
detector.generate_report(report, output_path='breaking-changes.md')
detector.generate_mitigation_plan(report, output_path='mitigation-plan.md')
```

### CLI Tool

```bash
# Analyze configurations
python scripts/detect_breaking_changes.py --config-dir ../base-helm-configs

# Analyze specific service
python scripts/detect_breaking_changes.py --service nova

# Generate reports
python scripts/detect_breaking_changes.py \
    --output report.md \
    --format markdown \
    --mitigation-plan plan.md

# Show catalog info
python scripts/detect_breaking_changes.py --show-stats --list-critical
```

## Breaking Changes Catalog

The catalog (`config/breaking-changes.yaml`) includes 14 documented breaking changes:

### Critical Issues
- AMQP 1.0 driver removed
- PostgreSQL support removed (Ironic)
- Linux Bridge driver removed (Neutron)
- Python 3.8 support removed
- kombu_ssl_* options removed

### High Priority
- Configuration options moved to [oslo_messaging_rabbit]

### Medium Priority
- heartbeat_in_pthread deprecated
- Legacy quota driver removed (Nova)
- Volume drivers deprecated (Cinder)
- Registry service removed (Glance)

### Low Priority
- Firewall v2 API changes
- XenAPI driver deprecated
- Token provider config simplified
- File-based logging discouraged

## Report Formats

### Markdown Report

```markdown
# Breaking Changes Impact Report

## Summary
- Total Breaking Changes Affecting Deployment: 3
- Critical Issues: 1
- High Priority Issues: 1
- Medium Priority Issues: 1

## Affected Breaking Changes

### CRITICAL Priority

#### BC002: kombu_ssl_* options removed
**Component:** oslo.messaging
**Type:** config
**Description:** The kombu_ssl_* options have been removed
**Impact:** SSL configuration will fail
**Mitigation:** Replace with non-prefixed ssl_* options
```

### Text Report

```
================================================================================
BREAKING CHANGES IMPACT REPORT
================================================================================
Generated: 2025-02-04 12:00:00

SUMMARY
--------------------------------------------------------------------------------
Total Breaking Changes Affecting Deployment: 3
  Critical Issues: 1
  High Priority Issues: 1
  Medium Priority Issues: 1
```

### JSON Report

```json
{
  "generated": "2025-02-04T12:00:00",
  "summary": {
    "total_affected": 3,
    "critical_count": 1,
    "high_count": 1,
    "medium_count": 1,
    "has_critical_issues": true
  },
  "affected_changes": [...]
}
```

## Extending the Catalog

To add new breaking changes, edit `config/breaking-changes.yaml`:

```yaml
breaking_changes:
  - id: "BC015"
    component: "nova"
    change_type: "config"
    title: "New breaking change"
    description: "Description of the change"
    impact: "What will happen"
    mitigation: "How to fix it"
    severity: "high"
    affects_services:
      - nova
      - neutron
    detection_pattern: "config_option_name"
    detection_section: "section_name"
```

## Testing

Run the test suite:

```bash
python -m pytest tests/test_breaking_changes.py -v
```

All 26 tests should pass, covering:
- Model validation
- Catalog loading and filtering
- Impact analysis
- Report generation
- End-to-end detection

## Integration

The Breaking Change Detector integrates with the upgrade workflow:

1. **Pre-Upgrade Validation** - Detect issues before starting
2. **Configuration Updates** - Identify deprecated options
3. **Impact Assessment** - Determine affected services
4. **Mitigation Planning** - Generate action items

## API Reference

### BreakingChangeDetector

```python
detector = BreakingChangeDetector(config_path=None)

# Detection methods
report = detector.detect_in_configuration(config_data, service_name)
report = detector.detect_in_deployment(override_configs, deployed_services)

# Report generation
report_str = detector.generate_report(report, output_path, format)
plan = detector.generate_mitigation_plan(report, output_path, format)

# Catalog queries
stats = detector.get_catalog_statistics()
critical = detector.get_critical_changes()
changes = detector.get_changes_by_component(component)
changes = detector.get_changes_by_service(service)
```

### ImpactReport

```python
# Properties
report.total_affected          # Number of affected changes
report.critical_count          # Number of critical issues
report.has_critical_issues     # Boolean
report.has_blocking_issues     # Critical or high severity

# Methods
sorted_changes = report.get_sorted_changes()  # By priority
```

### MitigationPlan

```python
# Properties
plan.required_actions          # Critical/high severity
plan.recommended_actions       # Medium severity
plan.optional_actions          # Low severity
plan.has_required_actions      # Boolean
```

## License

Part of the Genestack OpenStack upgrade tooling.
