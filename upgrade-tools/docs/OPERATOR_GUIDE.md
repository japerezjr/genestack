# OpenStack Upgrade Tool - Operator Guide

## Overview

This guide provides comprehensive documentation for operators using the `openstack-upgrade` tool to upgrade Genestack deployments from Caracal (2024.1/2024.2) to Epoxy (2025.1).

The upgrade tool provides:
- Automated pre-upgrade validation
- Chart version management
- Configuration validation
- Breaking change detection
- Service health monitoring
- Rollback capability
- Comprehensive logging and reporting

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Command Reference](#command-reference)
4. [Usage Examples](#usage-examples)
5. [Configuration Options](#configuration-options)
6. [Log Files](#log-files)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

## Installation

### Prerequisites

- Python 3.9 or later
- kubectl configured with cluster access
- helm 3.x installed
- OpenStack CLI tools installed
- Administrative access to Kubernetes cluster

### Setup

```bash
# Navigate to upgrade tools directory
cd /opt/genestack/upgrade-tools

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
./openstack-upgrade --help
```

### Verify Installation

```bash
# Check Python version
python --version
# Should show Python 3.9 or later

# Check kubectl access
kubectl get nodes
# Should show cluster nodes

# Check helm
helm version
# Should show helm 3.x

# Check OpenStack CLI
openstack --version
# Should show OpenStack CLI version
```

## Configuration

### Configuration File

The upgrade tool uses a YAML configuration file located at `config/upgrade-config.yaml`.

**Default configuration:**

```yaml
# Source and target releases
source_release: "2024.1"  # or "2024.2"
target_release: "2025.1"

# File paths
chart_versions_path: "../helm-chart-versions.yaml"
overrides_base_path: "../base-helm-configs/"
backup_path: "./backups/"

# Kubernetes configuration
namespace: "openstack"

# Upgrade behavior
dry_run: false
skip_optional_services: false
timeout_per_service: 600  # seconds (10 minutes)
```

### Customizing Configuration

Create a custom configuration file:

```bash
# Copy default configuration
cp config/upgrade-config.yaml config/my-upgrade-config.yaml

# Edit configuration
vi config/my-upgrade-config.yaml

# Use custom configuration
./openstack-upgrade --config config/my-upgrade-config.yaml
```

### Environment Variables

The tool respects standard Kubernetes and OpenStack environment variables:

```bash
# Kubernetes configuration
export KUBECONFIG=/path/to/kubeconfig

# OpenStack credentials
export OS_AUTH_URL=https://keystone.example.com:5000/v3
export OS_PROJECT_NAME=admin
export OS_USERNAME=admin
export OS_PASSWORD=secret
export OS_USER_DOMAIN_NAME=Default
export OS_PROJECT_DOMAIN_NAME=Default
```

## Command Reference

### Main Command

```bash
./openstack-upgrade [OPTIONS]
```

### Mode Selection Options

**Mutually exclusive - choose one:**

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would be changed without making changes |
| `--validate-only` | Run pre-upgrade validation only |
| `--rollback` | Rollback to previous version |
| (none) | Execute full upgrade |

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--config PATH` | None | Path to upgrade configuration file (YAML) |
| `--chart-versions PATH` | `../helm-chart-versions.yaml` | Path to helm-chart-versions.yaml |
| `--overrides-path PATH` | `../base-helm-configs` | Path to base-helm-configs directory |
| `--backup-path PATH` | `/var/backups/openstack` | Path to backup directory |

### Kubernetes Options

| Option | Default | Description |
|--------|---------|-------------|
| `--namespace NAME` | `openstack` | Kubernetes namespace |
| `--in-cluster` | False | Use in-cluster Kubernetes configuration |

### Upgrade Options

| Option | Default | Description |
|--------|---------|-------------|
| `--skip-optional` | False | Skip optional services (only upgrade core) |
| `--services SERVICE [SERVICE ...]` | All | Specific services to upgrade |
| `--timeout SECONDS` | 600 | Timeout per service in seconds |
| `--no-halt-on-failure` | False | Continue even if a service fails |

### Validation Options

| Option | Default | Description |
|--------|---------|-------------|
| `--skip-pre-validation` | False | Skip pre-upgrade validation (not recommended) |
| `--skip-post-validation` | False | Skip post-upgrade validation |
| `--skip-endpoints` | False | Skip OpenStack API endpoint checks |

### Output Options

| Option | Default | Description |
|--------|---------|-------------|
| `--output PATH` | stdout | Path to write upgrade report |
| `--format FORMAT` | `text` | Output format: text, json, or markdown |
| `--verbose, -v` | False | Enable verbose output |
| `--quiet, -q` | False | Suppress non-error output |

### Release Options

| Option | Default | Description |
|--------|---------|-------------|
| `--source-release VERSION` | `2024.2` | Source OpenStack release |
| `--target-release VERSION` | `2025.1` | Target OpenStack release |

### Help

```bash
./openstack-upgrade --help
```

## Usage Examples

### Example 1: Pre-Upgrade Validation

Validate system readiness before upgrade:

```bash
./openstack-upgrade --validate-only
```

**Output:**
```
======================================================================
Pre-Upgrade Validation
======================================================================
✓ All pods in Running state
✓ All OpenStack API endpoints responding
✓ Database backups exist and are recent
✓ Sufficient cluster resources available
✓ No active migrations or jobs running

Validation passed - system ready for upgrade
```

**If validation fails:**
```
✗ Pre-upgrade validation failed:
  - Pod nova-compute-node1 in CrashLoopBackOff state
  - Database backup is 3 days old (should be < 24 hours)
  - Active migration detected: instance-123

Please fix these issues before upgrading.
```

### Example 2: Dry-Run Mode

Test upgrade without making changes:

```bash
./openstack-upgrade --dry-run
```

**Output:**
```
======================================================================
Phase 1: Pre-Upgrade Validation
======================================================================
✓ Pre-upgrade validation passed

======================================================================
Phase 2: Chart and Configuration Updates
======================================================================
[DRY-RUN] Would update 15 chart versions:
  keystone: 0.2.0 → 0.3.0
  glance: 0.2.0 → 0.3.0
  nova: 0.2.0 → 0.3.0
  neutron: 0.2.0 → 0.3.0
  cinder: 0.2.0 → 0.3.0
  ...

✓ Configuration validation passed

⚠ Critical breaking changes detected:
  - oslo.messaging: heartbeat_in_pthread deprecated

[DRY-RUN] Upgrade preparation complete
[DRY-RUN] Would proceed to upgrade execution

Estimated duration: 45-60 minutes
```

### Example 3: Full Upgrade

Execute complete upgrade:

```bash
./openstack-upgrade
```

**Output:**
```
======================================================================
Phase 1: Pre-Upgrade Validation
======================================================================
✓ Pre-upgrade validation passed

======================================================================
Phase 2: Chart and Configuration Updates
======================================================================
Updating chart versions...
✓ Updated 15 chart versions

Validating configurations...
✓ Configuration validation passed

Detecting breaking changes...
⚠ Critical breaking changes detected:
  - oslo.messaging: heartbeat_in_pthread deprecated

Continue with upgrade? (yes/no): yes

======================================================================
Phase 3: Creating Backup
======================================================================
✓ Backup created: /var/backups/openstack/backup-20250115-143022.tar.gz

======================================================================
Phase 4: Upgrade Execution
======================================================================
Starting service upgrades...
✓ memcached upgraded (15s)
✓ mariadb-operator upgraded (30s)
✓ rabbitmq upgraded (45s)
✓ keystone upgraded (120s)
✓ glance upgraded (90s)
✓ placement upgraded (60s)
✓ cinder upgraded (150s)
✓ neutron upgraded (180s)
✓ nova upgraded (240s)
✓ horizon upgraded (60s)

✓ All services upgraded successfully
Total duration: 950.3 seconds (15.8 minutes)

======================================================================
Phase 5: Post-Upgrade Verification
======================================================================
✓ Post-upgrade validation passed

======================================================================
Upgrade Complete
======================================================================
Upgrade completed successfully in 16.2 minutes

Upgrade report written to upgrade-report.txt
```

### Example 4: Upgrade Core Services Only

Skip optional services:

```bash
./openstack-upgrade --skip-optional
```

This upgrades only:
- Infrastructure services (memcached, mariadb, rabbitmq)
- Core services (keystone, glance, placement, cinder, neutron, nova, horizon)

Optional services (octavia, heat, magnum, etc.) are skipped.

### Example 5: Upgrade Specific Services

Upgrade only specific services:

```bash
./openstack-upgrade --services keystone glance nova
```

**Use case:** Upgrade only services that need updates, or retry failed services.

### Example 6: Rollback

Rollback to previous version:

```bash
./openstack-upgrade --rollback
```

**Output:**
```
======================================================================
Rollback to Previous Version
======================================================================
Finding latest backup...
Found backup: /var/backups/openstack/backup-20250115-143022.tar.gz

This will rollback to the previous version. Continue? (yes/no): yes

Restoring from backup...
✓ Configuration files restored
✓ Helm releases rolled back
✓ Services verified

Verifying rollback...
✓ All pods in Running state
✓ All services operational
✓ APIs responding correctly

✓ Rollback completed successfully
```

### Example 7: Custom Configuration

Use custom configuration file:

```bash
./openstack-upgrade --config /path/to/custom-config.yaml
```

### Example 8: Verbose Output

Enable detailed logging:

```bash
./openstack-upgrade --verbose
```

**Output includes:**
- Detailed progress for each step
- Pod status changes
- Helm command output
- Health check details
- Timing information

### Example 9: Save Report to File

Save upgrade report to file:

```bash
./openstack-upgrade --output upgrade-report-$(date +%Y%m%d).txt
```

### Example 10: JSON Output

Generate JSON report for automation:

```bash
./openstack-upgrade --dry-run --format json --output dry-run.json
```

**Use case:** Parse output in CI/CD pipelines or monitoring systems.

## Configuration Options

### Service Categories

Services are organized into three categories:

**Core Services** (always upgraded):
- keystone (Identity)
- glance (Image)
- placement (Placement)
- cinder (Block Storage)
- neutron (Networking)
- nova (Compute)
- horizon (Dashboard)
- libvirt (Virtualization)

**Optional Services** (skipped with `--skip-optional`):
- barbican (Key Management)
- blazar (Reservation)
- ceilometer (Telemetry)
- cloudkitty (Rating)
- freezer (Backup)
- gnocchi (Metrics)
- heat (Orchestration)
- ironic (Bare Metal)
- magnum (Container Orchestration)
- manila (Shared Filesystem)
- masakari (Instance HA)
- octavia (Load Balancer)
- trove (Database as a Service)
- zaqar (Messaging)

**Infrastructure Services** (always upgraded first):
- memcached
- mariadb-operator
- postgres-operator
- rabbitmq

### Service Dependencies

The tool respects service dependencies and upgrades in correct order:

```yaml
dependencies:
  keystone: []                          # No dependencies
  glance: [keystone]                    # Requires keystone
  placement: [keystone]                 # Requires keystone
  cinder: [keystone, glance]            # Requires keystone and glance
  neutron: [keystone]                   # Requires keystone
  nova: [keystone, glance, placement, neutron]  # Requires all core services
  horizon: [keystone]                   # Requires keystone
  octavia: [keystone, neutron]          # Requires keystone and neutron
  heat: [keystone, neutron]             # Requires keystone and neutron
  magnum: [keystone, neutron, heat]     # Requires keystone, neutron, and heat
```

### Timeout Configuration

Configure timeouts for different operations:

```yaml
# Per-service upgrade timeout (seconds)
timeout_per_service: 600  # 10 minutes

# Health check timeout (seconds)
health_check_timeout: 300  # 5 minutes

# Backup timeout (seconds)
backup_timeout: 1800  # 30 minutes
```

**Adjust timeouts based on:**
- Deployment size
- Network speed
- Storage performance
- Image pull times

### Breaking Changes Configuration

Known breaking changes are configured in `config/breaking-changes.yaml`:

```yaml
breaking_changes:
  oslo_messaging:
    - option: "heartbeat_in_pthread"
      status: "deprecated"
      severity: "medium"
      description: "Deprecated in 2024.2, will be removed in future release"
      mitigation: "Remove from configuration"
```

**Severity levels:**
- `critical`: Must be addressed before upgrade
- `high`: Should be addressed before upgrade
- `medium`: Can be addressed during upgrade
- `low`: Can be addressed after upgrade

### Deprecation Rules

Deprecated options are configured in `config/deprecation-rules.yaml`:

```yaml
deprecated_options:
  - option: "[DEFAULT]/heartbeat_in_pthread"
    replacement: "Remove this option"
    services: ["nova", "neutron", "cinder"]
  
  - option: "[oslo_messaging_rabbit]/kombu_ssl_*"
    replacement: "Use non-prefixed ssl_* options"
    services: ["all"]
```

## Log Files

### Log Locations

| Log File | Location | Description |
|----------|----------|-------------|
| Upgrade log | `upgrade-tools/upgrade.log` | Main upgrade log with all actions |
| Execution log | `upgrade-execution.log` | Console output from upgrade run |
| Validation report | `validation-report.md` | Pre-upgrade validation results |
| Version report | `version-update-report.md` | Chart version changes |
| Upgrade report | `upgrade-report.txt` | Final upgrade summary |

### Log Format

Logs use structured format with timestamps:

```
2025-01-15 14:30:22 [INFO] upgrade_started: {"source": "2024.2", "target": "2025.1"}
2025-01-15 14:30:25 [INFO] validation_started: {}
2025-01-15 14:30:30 [INFO] validation_completed: {"passed": true, "issues": 0}
2025-01-15 14:30:35 [INFO] version_update_started: {}
2025-01-15 14:30:40 [INFO] version_updated: {"chart": "keystone", "old": "0.2.0", "new": "0.3.0"}
...
```

### Log Levels

| Level | Description | Example |
|-------|-------------|---------|
| DEBUG | Detailed diagnostic information | Pod status changes, API calls |
| INFO | General informational messages | Service upgraded, validation passed |
| WARNING | Warning messages | Deprecated option found, timeout extended |
| ERROR | Error messages | Service upgrade failed, API unreachable |
| CRITICAL | Critical errors | Upgrade halted, rollback required |

### Viewing Logs

```bash
# View main upgrade log
tail -f upgrade-tools/upgrade.log

# View last 100 lines
tail -100 upgrade-tools/upgrade.log

# Search for errors
grep ERROR upgrade-tools/upgrade.log

# Search for specific service
grep "keystone" upgrade-tools/upgrade.log

# View logs with timestamps
cat upgrade-tools/upgrade.log | grep "2025-01-15 14:"
```

### Log Rotation

Logs are automatically rotated:
- Maximum size: 100MB
- Backup count: 5
- Compression: gzip

Old logs are stored as:
- `upgrade.log.1.gz`
- `upgrade.log.2.gz`
- etc.

## Troubleshooting

### Common Issues

#### Issue: Module Not Found Error

**Symptom:**
```
ModuleNotFoundError: No module named 'config.schema'
```

**Cause:** Virtual environment not activated or dependencies not installed

**Solution:**
```bash
cd /opt/genestack/upgrade-tools
source venv/bin/activate
pip install -r requirements.txt
```

#### Issue: Validation Fails - Pods Not Running

**Symptom:**
```
✗ Pre-upgrade validation failed:
  - Pod nova-compute-node1 in CrashLoopBackOff state
```

**Cause:** Service pod is unhealthy

**Solution:**
```bash
# Check pod status
kubectl describe pod nova-compute-node1 -n openstack

# Check pod logs
kubectl logs nova-compute-node1 -n openstack --tail=100

# Restart pod
kubectl delete pod nova-compute-node1 -n openstack

# Wait for pod to be Running
kubectl get pod nova-compute-node1 -n openstack -w
```

#### Issue: Validation Fails - Old Backup

**Symptom:**
```
✗ Pre-upgrade validation failed:
  - Database backup is 3 days old (should be < 24 hours)
```

**Cause:** Backup is too old

**Solution:**
```bash
# Create new backup manually
kubectl exec -n openstack mariadb-server-0 -- \
  mysqldump --all-databases > /var/backups/openstack/databases/backup-$(date +%Y%m%d).sql

# Or trigger automated backup
./scripts/backup-mariadb.sh
```

#### Issue: Service Upgrade Timeout

**Symptom:**
```
ERROR: Service nova upgrade timed out after 600 seconds
```

**Cause:** Service taking longer than timeout to deploy

**Solution:**
```bash
# Increase timeout
./openstack-upgrade --timeout 1200  # 20 minutes

# Or check why service is slow
kubectl get pods -n openstack -l application=nova
kubectl describe pod <nova-pod> -n openstack
```

#### Issue: Helm Release Not Found

**Symptom:**
```
ERROR: Helm release 'keystone' not found
```

**Cause:** Service not deployed or wrong namespace

**Solution:**
```bash
# Check helm releases
helm list -n openstack

# Check namespace
kubectl get namespaces

# Use correct namespace
./openstack-upgrade --namespace <correct-namespace>
```

#### Issue: Permission Denied

**Symptom:**
```
ERROR: Permission denied: /var/backups/openstack
```

**Cause:** Insufficient permissions for backup directory

**Solution:**
```bash
# Create backup directory with correct permissions
sudo mkdir -p /var/backups/openstack
sudo chown $(whoami):$(whoami) /var/backups/openstack

# Or use different backup path
./openstack-upgrade --backup-path ./backups
```

#### Issue: Rollback Fails

**Symptom:**
```
✗ Rollback failed: Backup not found
```

**Cause:** Backup was deleted or not created

**Solution:**
```bash
# Check for backups
ls -lh /var/backups/openstack/

# If no backup, manual rollback required
# See UPGRADE_RUNBOOK.md for manual rollback procedure
```

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG

# Run with verbose output
./openstack-upgrade --verbose
```

### Getting Help

If issues persist:

1. **Check logs:**
   ```bash
   cat upgrade-tools/upgrade.log
   ```

2. **Check documentation:**
   - README.md
   - UPGRADE_RUNBOOK.md
   - docs/2024.1-to-2025.1.md

3. **Check Kubernetes:**
   ```bash
   kubectl get pods -n openstack
   kubectl get events -n openstack --sort-by='.lastTimestamp'
   ```

4. **Check OpenStack:**
   ```bash
   openstack compute service list
   openstack network agent list
   ```

5. **Contact support:**
   - GitHub Issues
   - Genestack community
   - Professional support

## FAQ

### General Questions

**Q: How long does the upgrade take?**

A: Depends on deployment size:
- Small (3 nodes, core only): 30-60 minutes
- Medium (5-10 nodes, core + optional): 1-2 hours
- Large (10+ nodes, all services): 2-4 hours

**Q: Is there downtime during upgrade?**

A: Yes, brief API downtime:
- Infrastructure services: No downtime
- Core services: 5-15 minutes per service
- Total: 30-60 minutes for core services

**Q: Can I upgrade only some services?**

A: Yes, use `--services` option:
```bash
./openstack-upgrade --services keystone glance nova
```

**Q: Can I skip optional services?**

A: Yes, use `--skip-optional`:
```bash
./openstack-upgrade --skip-optional
```

**Q: What if upgrade fails?**

A: The tool will halt and preserve state. You can:
1. Fix the issue and retry
2. Rollback using `--rollback`
3. Manual intervention if needed

### Pre-Upgrade Questions

**Q: What should I backup before upgrade?**

A: The tool automatically backs up:
- helm-chart-versions.yaml
- base-helm-configs/
- Database backups (if configured)

**Q: How do I test upgrade without making changes?**

A: Use dry-run mode:
```bash
./openstack-upgrade --dry-run
```

**Q: What are the prerequisites?**

A: See [Prerequisites](#prerequisites) section:
- Python 3.9+
- kubectl access
- helm 3.x
- OpenStack CLI
- Admin access

### Configuration Questions

**Q: Where is the configuration file?**

A: Default location: `config/upgrade-config.yaml`

**Q: Can I use custom configuration?**

A: Yes:
```bash
./openstack-upgrade --config /path/to/config.yaml
```

**Q: How do I change timeout?**

A: Use `--timeout` option:
```bash
./openstack-upgrade --timeout 1200  # 20 minutes
```

**Q: How do I change namespace?**

A: Use `--namespace` option:
```bash
./openstack-upgrade --namespace my-openstack
```

### Upgrade Questions

**Q: What order are services upgraded?**

A: Dependency order:
1. Infrastructure (memcached, mariadb, rabbitmq)
2. Core services (keystone, glance, placement, cinder, neutron, nova, horizon)
3. Optional services (octavia, heat, magnum, etc.)

**Q: Can I pause upgrade between services?**

A: No, but you can upgrade services individually:
```bash
./openstack-upgrade --services keystone
# Verify keystone
./openstack-upgrade --services glance
# etc.
```

**Q: What if one service fails?**

A: By default, upgrade halts. You can:
- Fix issue and retry
- Continue with `--no-halt-on-failure` (not recommended)
- Rollback

**Q: How do I monitor upgrade progress?**

A: Watch logs in real-time:
```bash
tail -f upgrade-tools/upgrade.log
```

Or in separate terminal:
```bash
watch -n 5 'kubectl get pods -n openstack'
```

### Post-Upgrade Questions

**Q: How do I verify upgrade succeeded?**

A: Check:
1. All pods Running
2. All services operational
3. APIs responding
4. Functional tests pass

```bash
kubectl get pods -n openstack
openstack compute service list
openstack network agent list
```

**Q: Where is the upgrade report?**

A: Default: stdout, or use `--output`:
```bash
./openstack-upgrade --output upgrade-report.txt
```

**Q: How do I check for errors?**

A: Check logs:
```bash
grep ERROR upgrade-tools/upgrade.log
```

**Q: What if I find issues after upgrade?**

A: You can:
1. Fix in place (for minor issues)
2. Rollback (for major issues)

### Rollback Questions

**Q: How do I rollback?**

A: Use rollback mode:
```bash
./openstack-upgrade --rollback
```

**Q: When should I rollback?**

A: Rollback if:
- Multiple core services failed
- Critical services non-functional
- Data corruption detected
- Severe performance issues

**Q: What does rollback do?**

A: Rollback:
1. Restores previous chart versions
2. Restores previous configurations
3. Reapplies previous helm releases
4. Verifies service health

**Q: Can I rollback specific services?**

A: No, rollback is all-or-nothing. For specific services, use helm:
```bash
helm rollback <service> -n openstack
```

**Q: What if rollback fails?**

A: Manual rollback required. See UPGRADE_RUNBOOK.md for procedure.

### Troubleshooting Questions

**Q: Where are the logs?**

A: Main log: `upgrade-tools/upgrade.log`

**Q: How do I enable debug logging?**

A: Use verbose mode:
```bash
./openstack-upgrade --verbose
```

**Q: Service won't start after upgrade, what do I do?**

A: Check:
1. Pod logs: `kubectl logs <pod> -n openstack`
2. Pod events: `kubectl describe pod <pod> -n openstack`
3. Service configuration
4. Database connectivity

**Q: How do I get help?**

A: See [Getting Help](#getting-help) section.

---

## Additional Resources

- **Main Documentation:** `docs/2024.1-to-2025.1.md`
- **Upgrade Runbook:** `docs/UPGRADE_RUNBOOK.md`
- **Lab Setup Guide:** `docs/LAB_ENVIRONMENT_SETUP.md`
- **Integration Testing:** `docs/INTEGRATION_TESTING.md`
- **Genestack Docs:** https://docs.rackspacecloud.com/genestack/
- **OpenStack-Helm Docs:** https://docs.openstack.org/openstack-helm/latest/

---

**End of Operator Guide**
