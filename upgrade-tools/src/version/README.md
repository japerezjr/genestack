# Chart Version Manager

The Chart Version Manager provides tools for managing OpenStack helm chart version updates during upgrades.

## Components

### VersionParser
Parses helm-chart-versions.yaml and identifies charts that need updating.

**Key Features:**
- Load chart versions from YAML
- Identify OpenStack services
- Detect Caracal (2024.1/2024.2) and Epoxy (2025.1) versions
- Categorize charts (core, optional, infrastructure, non-openstack)
- Identify version updates needed

### VersionUpdater
Applies version updates to helm-chart-versions.yaml.

**Key Features:**
- Replace Caracal versions with Epoxy versions
- Preserve non-OpenStack chart versions
- Support dry-run mode
- Validate updates before applying
- Handle edge cases (missing versions, invalid formats)

### VersionReporter
Generates reports of version changes.

**Key Features:**
- Create structured version reports
- Generate markdown, text, or JSON output
- Include dependency information
- Track errors and warnings
- Save reports to files

### ChartVersionManager
High-level interface that orchestrates the entire version management workflow.

**Key Features:**
- Load current versions
- Identify updates
- Apply updates
- Generate reports
- Complete upgrade workflow in one call

## Usage

### Basic Usage

```python
from src.version import ChartVersionManager

# Create manager
manager = ChartVersionManager('helm-chart-versions.yaml')

# Run complete upgrade workflow
report = manager.upgrade_caracal_to_epoxy(
    dry_run=False,
    generate_report=True,
    report_path='upgrade-report.md',
    report_format='markdown'
)

print(f"Updated {report.updated_charts} charts")
```

### Step-by-Step Usage

```python
from src.version import ChartVersionManager

# Create manager
manager = ChartVersionManager('helm-chart-versions.yaml')

# Load current versions
versions = manager.load_current_versions()
print(f"Loaded {len(versions)} charts")

# Identify updates
updates = manager.identify_updates(target_release='2025.1')
print(f"Found {len(updates)} charts to update")

# Apply updates (dry run first)
updated = manager.apply_updates(target_release='2025.1', dry_run=True)
print(f"Would update {len(updated)} charts")

# Apply updates for real
updated = manager.apply_updates(target_release='2025.1', dry_run=False)
print(f"Updated {len(updated)} charts")

# Generate report
report = manager.generate_report(
    source_release='2024.1',
    target_release='2025.1'
)

# Save report
report.save_to_file('upgrade-report.md', format='markdown')
```

### CLI Usage

A command-line script is provided for convenience:

```bash
# Dry run (show what would change)
python scripts/update_chart_versions.py \
    --versions-file helm-chart-versions.yaml \
    --dry-run \
    --report-path report.md

# Apply updates
python scripts/update_chart_versions.py \
    --versions-file helm-chart-versions.yaml \
    --report-path report.md

# Generate JSON report
python scripts/update_chart_versions.py \
    --versions-file helm-chart-versions.yaml \
    --report-format json \
    --report-path report.json
```

## Version Detection

The version manager uses regex patterns to detect OpenStack versions:

- **Caracal**: Versions containing `2024.1` or `2024.2`
- **Epoxy**: Versions containing `2025.1`

Examples:
- `2024.1.386+13651f45-628a320c` → Caracal
- `2024.2.555+13651f45-628a320c` → Caracal
- `2025.1.15+b1e463122` → Epoxy

## Chart Categories

Charts are categorized as:

- **Core Services**: keystone, glance, cinder, neutron, nova, placement, horizon, libvirt
- **Optional Services**: barbican, blazar, ceilometer, cloudkitty, freezer, gnocchi, heat, ironic, magnum, manila, masakari, octavia, trove, zaqar
- **Infrastructure**: memcached, mariadb-operator, postgres-operator, rabbitmq
- **Non-OpenStack**: All other charts (cert-manager, metallb, etc.)

Only OpenStack services with Caracal versions are updated.

## Dependencies

The version manager tracks dependencies between services to ensure proper upgrade order:

- Infrastructure services have no dependencies
- Core services depend on infrastructure
- Optional services depend on core services

Example dependency chain:
```
mariadb-operator → keystone → glance
                            → placement → nova
```

## Report Formats

### Markdown
Human-readable report with tables and sections:
- Summary statistics
- Version updates by category
- Dependency information
- Errors and warnings

### Text
Simple plain-text report for console output or logs.

### JSON
Structured data format for programmatic processing:
```json
{
  "timestamp": "2026-02-03T15:58:50",
  "source_release": "2024.1",
  "target_release": "2025.1",
  "total_charts": 46,
  "updated_charts": 13,
  "updates": [...]
}
```

## Testing

Run tests with pytest:

```bash
cd upgrade-tools
python -m pytest tests/test_version_manager.py -v
```

Tests cover:
- Version parsing and detection
- OpenStack service identification
- Version updates (dry-run and actual)
- Report generation
- Complete upgrade workflow

## Error Handling

The version manager handles various error conditions:

- Missing or invalid YAML files
- Version mismatches
- Missing charts
- Invalid version formats
- File write errors

All errors are logged and included in the report.
