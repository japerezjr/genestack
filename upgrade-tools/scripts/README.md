# Upgrade Scripts

This directory contains Bash wrapper scripts for the OpenStack Caracal to Epoxy upgrade process.

## Wrapper Scripts

### pre-upgrade-validate.sh

Pre-upgrade validation script that checks system health and readiness before upgrade.

**Usage:**
```bash
./pre-upgrade-validate.sh [OPTIONS]
```

**Options:**
- `-n, --namespace NAMESPACE` - Kubernetes namespace (default: openstack)
- `-o, --output FILE` - Write report to file instead of stdout
- `-f, --format FORMAT` - Output format: text, json, markdown (default: text)
- `--skip-endpoints` - Skip OpenStack API endpoint checks
- `--in-cluster` - Use in-cluster Kubernetes configuration
- `-v, --verbose` - Enable verbose output
- `-h, --help` - Show help message

**Examples:**
```bash
# Basic validation
./pre-upgrade-validate.sh

# Save validation report to file
./pre-upgrade-validate.sh --output validation-report.md --format markdown

# Skip endpoint checks
./pre-upgrade-validate.sh --skip-endpoints
```

**Exit Codes:**
- `0` - All validations passed
- `1` - One or more validations failed
- `2` - Script error or invalid arguments

---

### upgrade-execute.sh

Upgrade execution script that performs the full OpenStack upgrade from Caracal to Epoxy.

**Usage:**
```bash
./upgrade-execute.sh [OPTIONS]
```

**Options:**
- `-n, --namespace NAMESPACE` - Kubernetes namespace (default: openstack)
- `-o, --output FILE` - Write upgrade report to file
- `-f, --format FORMAT` - Output format: text, json, markdown (default: text)
- `--dry-run` - Show what would be changed without making changes
- `--skip-optional` - Skip optional services (only upgrade core services)
- `--skip-pre-validation` - Skip pre-upgrade validation (not recommended)
- `--skip-post-validation` - Skip post-upgrade validation
- `--skip-endpoints` - Skip OpenStack API endpoint checks
- `--in-cluster` - Use in-cluster Kubernetes configuration
- `--timeout SECONDS` - Timeout per service in seconds (default: 600)
- `--no-halt-on-failure` - Continue upgrade even if a service fails
- `--services SERVICE...` - Specific services to upgrade (space-separated)
- `--source-release VERSION` - Source OpenStack release (default: 2024.2)
- `--target-release VERSION` - Target OpenStack release (default: 2025.1)
- `-v, --verbose` - Enable verbose output
- `-h, --help` - Show help message

**Examples:**
```bash
# Dry-run to see what would be changed
./upgrade-execute.sh --dry-run

# Full upgrade with default settings
./upgrade-execute.sh

# Upgrade only core services
./upgrade-execute.sh --skip-optional

# Upgrade specific services
./upgrade-execute.sh --services keystone glance nova

# Save upgrade report to file
./upgrade-execute.sh --output upgrade-report.md --format markdown
```

**Exit Codes:**
- `0` - Upgrade completed successfully
- `1` - Upgrade failed
- `2` - Script error or invalid arguments
- `130` - Upgrade interrupted by user

**Notes:**
- Pre-upgrade validation is strongly recommended
- A backup is automatically created before upgrade
- Use `--dry-run` to preview changes before executing
- Upgrade can be interrupted with Ctrl+C
- Use `rollback.sh` if upgrade fails

---

### rollback.sh

Rollback script that reverts OpenStack to the previous version after a failed upgrade.

**Usage:**
```bash
./rollback.sh [OPTIONS]
```

**Options:**
- `-n, --namespace NAMESPACE` - Kubernetes namespace (default: openstack)
- `-o, --output FILE` - Write rollback report to file
- `-f, --format FORMAT` - Output format: text, json, markdown (default: text)
- `--dry-run` - Show what would be done without making changes
- `--backup-path PATH` - Path to backup directory (default: /var/backups/openstack)
- `--in-cluster` - Use in-cluster Kubernetes configuration
- `--force` - Skip confirmation prompt
- `-v, --verbose` - Enable verbose output
- `-h, --help` - Show help message

**Examples:**
```bash
# Rollback with confirmation
./rollback.sh

# Dry-run to see what would be done
./rollback.sh --dry-run

# Rollback with custom backup path
./rollback.sh --backup-path /custom/backup/path

# Force rollback without confirmation
./rollback.sh --force

# Save rollback report to file
./rollback.sh --output rollback-report.md --format markdown
```

**Exit Codes:**
- `0` - Rollback completed successfully
- `1` - Rollback failed
- `2` - Script error or invalid arguments
- `130` - Rollback interrupted by user

**Notes:**
- Rollback restores from the most recent backup
- All services will be reverted to previous versions
- Database backups will be restored if schema changes occurred
- Service health is verified after rollback
- Use `--dry-run` to preview rollback actions

**Warning:**
Rollback is a critical operation. Ensure you understand the implications before proceeding.

---

### post-upgrade-verify.sh

Post-upgrade verification script that validates service functionality after upgrade.

**Usage:**
```bash
./post-upgrade-verify.sh [OPTIONS]
```

**Options:**
- `-n, --namespace NAMESPACE` - Kubernetes namespace (default: openstack)
- `-o, --output FILE` - Write verification report to file
- `-f, --format FORMAT` - Output format: text, json, markdown (default: text)
- `--skip-endpoints` - Skip OpenStack API endpoint checks
- `--skip-operations` - Skip functional operation tests
- `--quick-check` - Run quick checks only (pod status and endpoints)
- `--in-cluster` - Use in-cluster Kubernetes configuration
- `-v, --verbose` - Enable verbose output
- `-h, --help` - Show help message

**Verification Checks:**
1. Pod Status Check - Verify all pods are Running
2. API Endpoint Check - Verify all OpenStack APIs are accessible
3. Service List Check - Verify compute, network, volume services
4. Functional Tests - Test key operations (create/delete resources)
5. Log Analysis - Check for critical errors in service logs
6. Performance Baseline - Compare API response times

**Examples:**
```bash
# Full verification
./post-upgrade-verify.sh

# Quick check (pod status and endpoints only)
./post-upgrade-verify.sh --quick-check

# Verification without functional tests
./post-upgrade-verify.sh --skip-operations

# Save verification report to file
./post-upgrade-verify.sh --output verification-report.md --format markdown
```

**Exit Codes:**
- `0` - All verifications passed
- `1` - One or more verifications failed
- `2` - Script error or invalid arguments

**Notes:**
- Functional tests create temporary resources that are cleaned up
- Use `--quick-check` for fast health verification
- Use `--skip-operations` if you want to test manually
- Verification can take 5-10 minutes for full checks

---

## Python Helper Scripts

These Python scripts provide specific functionality used by the wrapper scripts:

- `apply_config_updates.py` - Apply configuration updates to override files
- `detect_breaking_changes.py` - Detect breaking changes between releases
- `update_chart_versions.py` - Update helm chart versions
- `validate_configs.py` - Validate configuration files
- `validate_pre_upgrade.py` - Run pre-upgrade validation checks

## Workflow

The typical upgrade workflow using these scripts:

1. **Pre-Upgrade Validation**
   ```bash
   ./pre-upgrade-validate.sh --output pre-validation.md --format markdown
   ```

2. **Dry-Run Upgrade**
   ```bash
   ./upgrade-execute.sh --dry-run
   ```

3. **Execute Upgrade**
   ```bash
   ./upgrade-execute.sh --output upgrade-report.md --format markdown
   ```

4. **Post-Upgrade Verification**
   ```bash
   ./post-upgrade-verify.sh --output post-verification.md --format markdown
   ```

5. **Rollback (if needed)**
   ```bash
   ./rollback.sh --output rollback-report.md --format markdown
   ```

## Requirements

- Python 3.9+
- kubectl configured with cluster access
- OpenStack CLI (optional, for service verification)
- Helm 3.x
- Sufficient permissions to manage resources in the target namespace

## Environment Variables

- `NAMESPACE` - Default Kubernetes namespace (default: openstack)

## Exit Codes

All scripts follow a consistent exit code convention:
- `0` - Success
- `1` - Operation failed
- `2` - Script error or invalid arguments
- `130` - Interrupted by user (Ctrl+C)
