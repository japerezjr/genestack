# Logging and Reporting System

This module provides comprehensive logging, reporting, and documentation generation for OpenStack upgrade operations.

## Components

### 1. UpgradeLogger (`logger.py`)

Structured logging system that captures all upgrade actions with timestamps, action types, components, and details.

**Features:**
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Dual output (file and console) with independent log levels
- Structured action logging for programmatic analysis
- Specialized logging methods for different action types
- JSON export of action log

**Usage:**

```python
from src.logging import UpgradeLogger, LogLevel, ActionType

# Initialize logger
logger = UpgradeLogger(
    log_file="upgrade.log",
    console_level=LogLevel.INFO,
    file_level=LogLevel.DEBUG
)

# Log version update
logger.log_version_update("keystone", "2024.1", "2025.1")

# Log configuration change
logger.log_config_update("config.yaml", {"image_tag": "2025.1"})

# Log service upgrade
logger.log_service_upgrade("keystone", "success", duration=45.5)

# Log validation
logger.log_validation("config_validation", "passed")

# Log health check
logger.log_health_check("keystone", "healthy", {"pods": 3})

# Log rollback
logger.log_rollback("nova", "success")

# Save action log to JSON
logger.save_action_log("action_log.json")
```

### 2. SummaryReportGenerator (`report_generator.py`)

Generates comprehensive summary reports of upgrade operations, aggregating version changes, configuration changes, duration, and issues.

**Features:**
- Tracks version changes, config changes, and service upgrades
- Records issues encountered with severity levels
- Calculates upgrade duration
- Determines overall success/failure
- Generates both text and JSON reports
- Can populate from action log

**Usage:**

```python
from src.logging import SummaryReportGenerator

# Initialize generator
report_gen = SummaryReportGenerator()

# Start upgrade
report_gen.start_upgrade()

# Add changes
report_gen.add_version_change("keystone", "2024.1", "2025.1")
report_gen.add_config_change("config.yaml", {"key": "value"})

# Track service upgrades
report_gen.add_service_upgraded("keystone")
report_gen.add_service_failed("nova")

# Add issues
report_gen.add_issue("high", "nova", "Service upgrade failed")

# Mark rollback if needed
report_gen.mark_rollback()

# End upgrade
report_gen.end_upgrade()

# Generate reports
text_report = report_gen.generate_text_report()
json_report = report_gen.generate_json_report()

# Save reports
report_gen.save_report("output_dir", format="both")

# Or populate from action log
report_gen.from_action_log(logger.get_action_log())
```

### 3. UpgradeDocGenerator (`doc_generator.py`)

Generates markdown documentation for upgrade operations, including all changes made, manual steps required, and updates to the docs/ directory.

**Features:**
- Documents version changes in table format
- Groups configuration changes by file
- Documents breaking changes with mitigation
- Tracks manual steps with commands
- Adds warnings and notes
- Generates changelog entries
- Updates project documentation

**Usage:**

```python
from src.logging import UpgradeDocGenerator

# Initialize generator
doc_gen = UpgradeDocGenerator()

# Add version changes
doc_gen.add_version_change("keystone", "2024.1", "2025.1")

# Add configuration changes
doc_gen.add_config_change(
    "config.yaml",
    "modified",
    "Updated image tag",
    old_value="2024.1",
    new_value="2025.1"
)

# Add breaking changes
doc_gen.add_breaking_change(
    "oslo.messaging",
    "heartbeat_in_pthread deprecated",
    "Removed deprecated option from configs"
)

# Add manual steps
doc_gen.add_manual_step(
    "Verify compute agents",
    "nova",
    "Required after upgrade",
    commands=["openstack compute service list"]
)

# Add warnings and notes
doc_gen.add_warning("Database backup recommended")
doc_gen.add_note("Upgrade completed successfully")

# Generate documentation
markdown = doc_gen.generate_markdown()

# Save documentation
doc_gen.save_documentation("upgrade_doc.md", update_docs_dir=True)

# Generate changelog entry
changelog_entry = doc_gen.generate_changelog_entry()

# Append to changelog
doc_gen.append_to_changelog("CHANGELOG.md")
```

## Complete Workflow Example

Here's how to use all three components together:

```python
from pathlib import Path
from src.logging import (
    UpgradeLogger,
    LogLevel,
    SummaryReportGenerator,
    UpgradeDocGenerator
)

# Initialize all components
logger = UpgradeLogger(
    log_file="upgrade.log",
    console_level=LogLevel.INFO,
    file_level=LogLevel.DEBUG
)
report_gen = SummaryReportGenerator()
doc_gen = UpgradeDocGenerator()

# Start upgrade
report_gen.start_upgrade()
logger.info("Starting upgrade")

# Perform upgrade actions
# 1. Version updates
logger.log_version_update("keystone", "2024.1", "2025.1")
report_gen.add_version_change("keystone", "2024.1", "2025.1")
doc_gen.add_version_change("keystone", "2024.1", "2025.1")

# 2. Configuration changes
logger.log_config_update("config.yaml", {"image_tag": "2025.1"})
report_gen.add_config_change("config.yaml", {"image_tag": "2025.1"})
doc_gen.add_config_change("config.yaml", "modified", "Updated image tag", 
                          new_value="2025.1")

# 3. Service upgrades
logger.log_service_upgrade("keystone", "success", duration=45.5)
report_gen.add_service_upgraded("keystone")

# 4. Breaking changes
doc_gen.add_breaking_change(
    "oslo.messaging",
    "heartbeat_in_pthread deprecated",
    "Removed from configs"
)

# 5. Manual steps
doc_gen.add_manual_step(
    "Verify services",
    "keystone",
    "Required after upgrade",
    commands=["openstack service list"]
)

# End upgrade
report_gen.end_upgrade()
logger.info("Upgrade completed")

# Generate all outputs
output_dir = Path("upgrade_output")
output_dir.mkdir(exist_ok=True)

# Save action log
logger.save_action_log(output_dir / "action_log.json")

# Save reports
report_gen.save_report(output_dir, format="both")

# Save documentation
doc_gen.save_documentation(output_dir / "upgrade_doc.md", update_docs_dir=True)

# Update changelog
doc_gen.append_to_changelog("CHANGELOG.md")
```

## Output Files

The logging system generates several output files:

1. **upgrade.log** - Detailed log file with all actions and messages
2. **action_log.json** - Structured JSON log of all actions for programmatic analysis
3. **upgrade_summary_TIMESTAMP.txt** - Human-readable summary report
4. **upgrade_summary_TIMESTAMP.json** - Machine-readable summary report
5. **upgrade_documentation.md** - Comprehensive markdown documentation
6. **CHANGELOG.md** - Updated changelog with upgrade entry

## Action Types

The logger supports the following action types:

- `VERSION_UPDATE` - Chart version updates
- `CONFIG_UPDATE` - Configuration file changes
- `SERVICE_UPGRADE` - Service upgrade operations
- `VALIDATION` - Validation checks
- `HEALTH_CHECK` - Health check operations
- `ROLLBACK` - Rollback operations
- `BACKUP` - Backup operations
- `RESTORE` - Restore operations

## Log Levels

Available log levels (in order of severity):

- `DEBUG` - Detailed diagnostic information
- `INFO` - General informational messages
- `WARNING` - Warning messages for potential issues
- `ERROR` - Error messages for failures
- `CRITICAL` - Critical errors requiring immediate attention

## Report Sections

### Summary Report Includes:

- **Overview** - Start/end time, duration, status, rollback status
- **Version Changes** - All chart version updates
- **Configuration Changes** - All config file modifications
- **Services** - Successfully upgraded and failed services
- **Issues** - All issues encountered, grouped by severity

### Documentation Includes:

- **Version Changes** - Table of all version updates
- **Configuration Changes** - Grouped by file with change types
- **Breaking Changes** - With component, description, and mitigation
- **Manual Steps** - Numbered steps with commands
- **Warnings** - Important warnings for operators
- **Notes** - Additional notes and observations

## Testing

Run the tests:

```bash
# Run all logging tests
pytest tests/test_logger.py tests/test_report_generator.py tests/test_doc_generator.py -v

# Run integration tests
pytest tests/test_logging_integration.py -v
```

## Example

See `examples/logging_example.py` for a complete working example:

```bash
python examples/logging_example.py
```

This will generate example output in the `example_output/` directory.

## Requirements

- Python 3.9+
- No external dependencies (uses only standard library)

## Design

The logging system follows these design principles:

1. **Separation of Concerns** - Logger, reporter, and doc generator are independent
2. **Structured Data** - All actions are logged with structured data for analysis
3. **Multiple Formats** - Supports both human-readable and machine-readable outputs
4. **Comprehensive Coverage** - Captures all aspects of the upgrade process
5. **Ease of Use** - Simple API with sensible defaults
6. **Testability** - Fully tested with unit and integration tests

## Integration

The logging system integrates with other upgrade components:

- **Version Manager** - Logs version updates
- **Configuration Validator** - Logs validation results
- **Service Upgrader** - Logs service upgrades
- **Health Monitor** - Logs health checks
- **Rollback Manager** - Logs rollback operations

All components can use the same logger instance for consistent logging throughout the upgrade process.
