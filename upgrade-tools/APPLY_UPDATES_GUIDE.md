# Configuration Update Automation Guide

## About the all.yaml "Error"

**Good news!** The YAML error in `base-helm-configs/openstack-api-exporter-chart/templates/all.yaml` is a **FALSE POSITIVE**.

### Why the validator flagged it:
The file contains multiple Kubernetes resources separated by `---` (which is valid multi-document YAML). However, the validator tried to parse it as a single YAML document, which caused the error.

### The truth:
This is a **Helm template file** with multiple Kubernetes resources (ConfigMap, Deployment, Service, ServiceMonitor). The `---` separators on lines 1, 10, 92, 107, and 113 are **correct and required** for Helm templates.

**No action needed** - this file is fine as-is!

---

## Automated Update Script

I've created `scripts/apply_config_updates.py` to automate the configuration updates.

### What it does:

1. **Updates image tags:** Changes all `2024.1` and `2024.2` versions to `2025.1`
2. **Removes deprecated options:** Removes `heartbeat_in_pthread` and `neutron_linuxbridge_agent`
3. **Creates backups:** Automatically backs up all modified files before making changes
4. **Provides detailed reporting:** Shows exactly what was changed

---

## Usage

### Step 1: Dry Run (Recommended First)

See what would be changed without actually modifying files:

```bash
cd upgrade-tools
python scripts/apply_config_updates.py ../base-helm-configs --dry-run --verbose
```

This will show you:
- Which files will be updated
- How many image tags will be changed in each file
- How many deprecated options will be removed
- Total summary of all changes

### Step 2: Apply Updates

Once you're satisfied with the dry run results, apply the updates:

```bash
cd upgrade-tools
python scripts/apply_config_updates.py ../base-helm-configs
```

This will:
- Create backups in `upgrade-tools/backups/config_backup_YYYYMMDD_HHMMSS/`
- Update all configuration files
- Print a summary of changes

### Step 3: Verify Updates

Re-run the validation to confirm all issues are resolved:

```bash
cd upgrade-tools
python scripts/validate_configs.py ../base-helm-configs --verbose
```

You should see:
- ✅ Image tag issues: 0 (down from 206)
- ✅ Deprecated options: 0 (down from 33)
- ⚠️ YAML errors: 1 (this is the false positive in all.yaml - ignore it)

---

## Advanced Usage

### Custom Backup Location

```bash
python scripts/apply_config_updates.py ../base-helm-configs \
  --backup-dir /path/to/my/backups
```

### Process Specific Files Only

```bash
# Only update nova configs
python scripts/apply_config_updates.py ../base-helm-configs \
  --pattern "nova/*.yaml"

# Update multiple specific services
python scripts/apply_config_updates.py ../base-helm-configs \
  --pattern "nova/*.yaml" \
  --pattern "neutron/*.yaml" \
  --pattern "cinder/*.yaml"
```

### Verbose Output

```bash
python scripts/apply_config_updates.py ../base-helm-configs \
  --verbose
```

---

## What Gets Updated

### Image Tag Updates (206 total)

**Before:**
```yaml
images:
  tags:
    nova_api: ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest
    cinder_api: ghcr.io/rackerlabs/genestack-images/cinder:2024.2-latest
    gnocchi_api: quay.io/rackspace/rackerlabs-gnocchi:2024.1-ubuntu_jammy
```

**After:**
```yaml
images:
  tags:
    nova_api: ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest
    cinder_api: ghcr.io/rackerlabs/genestack-images/cinder:2025.1-latest
    gnocchi_api: quay.io/rackspace/rackerlabs-gnocchi:2025.1-ubuntu_jammy
```

### Deprecated Option Removal (33 instances)

**Before:**
```yaml
conf:
  nova:
    oslo_messaging_rabbit:
      heartbeat_in_pthread: True
      rabbit_ha_queues: True
```

**After:**
```yaml
conf:
  nova:
    oslo_messaging_rabbit:
      rabbit_ha_queues: True
```

### Linux Bridge Removal (neutron only)

**Before:**
```yaml
images:
  tags:
    neutron_linuxbridge_agent: ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest
    neutron_server: ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest
```

**After:**
```yaml
images:
  tags:
    neutron_server: ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest
```

---

## Backup and Rollback

### Backup Location

Backups are automatically created in:
```
upgrade-tools/backups/config_backup_YYYYMMDD_HHMMSS/
```

The backup preserves the exact directory structure of your configs.

### Rollback if Needed

If you need to rollback the changes:

```bash
# Find your backup directory
ls -la upgrade-tools/backups/

# Restore from backup
cp -r upgrade-tools/backups/config_backup_YYYYMMDD_HHMMSS/* ../base-helm-configs/
```

---

## Expected Results

After running the script, you should see output like:

```
2026-02-03 16:45:00 - __main__ - INFO - Found 62 files to process
2026-02-03 16:45:00 - __main__ - INFO - Updating cinder-helm-overrides.yaml: 12 image tags, 2 deprecated options
2026-02-03 16:45:00 - __main__ - INFO - Updating nova-helm-overrides.yaml: 20 image tags, 2 deprecated options
2026-02-03 16:45:00 - __main__ - INFO - Updating neutron-helm-overrides.yaml: 23 image tags, 3 deprecated options
...

================================================================================
UPDATE SUMMARY
================================================================================
Files processed: 62
Files updated: 18
Image tags updated: 206
Deprecated options removed: 33
Errors: 0

Backups saved to: upgrade-tools/backups/config_backup_20260203_164500
================================================================================
```

---

## Troubleshooting

### Script fails with import error

Make sure you're running from the upgrade-tools directory:
```bash
cd upgrade-tools
python scripts/apply_config_updates.py ../base-helm-configs
```

### Permission denied

Ensure you have write permissions to the base-helm-configs directory:
```bash
ls -la ../base-helm-configs/
```

### Want to undo changes

Restore from the backup directory:
```bash
cp -r backups/config_backup_YYYYMMDD_HHMMSS/* ../base-helm-configs/
```

---

## Next Steps

After applying the updates:

1. **Verify the changes:**
   ```bash
   python scripts/validate_configs.py ../base-helm-configs
   ```

2. **Review the updated files:**
   ```bash
   git diff ../base-helm-configs/
   ```

3. **Test in a lab environment** before applying to production

4. **Proceed with the upgrade** using the version manager:
   ```bash
   python scripts/update_chart_versions.py --versions-file ../helm-chart-versions.yaml
   ```
