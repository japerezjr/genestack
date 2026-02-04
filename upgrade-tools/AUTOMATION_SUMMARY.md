# Configuration Update Automation - Summary

## ✅ Automation Script Created

**Location:** `upgrade-tools/scripts/apply_config_updates.py`

## About the YAML "Error"

### The all.yaml File is Actually CORRECT! ✅

**File:** `base-helm-configs/openstack-api-exporter-chart/templates/all.yaml`

**What the validator said:**
> "Invalid YAML syntax: expected a single document but found another document at line 10"

**The truth:**
This is a **Helm template file** with multiple Kubernetes resources (ConfigMap, Deployment, Service, ServiceMonitor). The `---` separators are **correct and required** for Helm templates.

**Why the false positive?**
The YAML validator tried to parse it as a single YAML document, but Helm templates are multi-document YAML files by design. This is perfectly valid.

**Action needed:** None - the file is correct as-is!

---

## What the Script Does

### 1. Updates Image Tags (206 changes)
Changes all Caracal versions to Epoxy:
- `2024.1-latest` → `2025.1-latest`
- `2024.2-latest` → `2025.1-latest`
- `2024.1-ubuntu_jammy` → `2025.1-ubuntu_jammy`

### 2. Removes Deprecated Options (28 changes)
Removes deprecated oslo.messaging configuration:
- `heartbeat_in_pthread: True` (deprecated in 2024.2)
- `neutron_linuxbridge_agent` image tag (Linux Bridge removed in Epoxy)

### 3. Creates Automatic Backups
Before making any changes, creates timestamped backups in:
```
upgrade-tools/backups/config_backup_YYYYMMDD_HHMMSS/
```

---

## Dry Run Results

```
Files processed: 49
Files updated: 21
Image tags updated: 206
Deprecated options removed: 28
Errors: 0
```

### Files That Will Be Updated:

**Core Services (7 files):**
- cinder-helm-overrides.yaml (12 image tags, 2 deprecated options)
- glance-helm-overrides.yaml (9 image tags, 2 deprecated options)
- horizon-helm-overrides.yaml (4 image tags)
- keystone-helm-overrides.yaml (12 image tags, 2 deprecated options)
- neutron-helm-overrides.yaml (23 image tags, 2 deprecated options)
- nova-helm-overrides.yaml (20 image tags, 2 deprecated options)
- placement-helm-overrides.yaml (7 image tags)

**Optional Services (14 files):**
- barbican-helm-overrides.yaml (9 image tags, 2 deprecated options)
- blazar-helm-overrides.yaml (1 deprecated option)
- ceilometer-helm-overrides.yaml (7 image tags, 2 deprecated options)
- cloudkitty-helm-overrides.yaml (9 image tags)
- designate-helm-overrides.yaml (13 image tags, 2 deprecated options)
- gnocchi-helm-overrides.yaml (9 image tags)
- heat-helm-overrides.yaml (13 image tags, 2 deprecated options)
- ironic-helm-overrides.yaml (16 image tags, 1 deprecated option)
- magnum-helm-overrides.yaml (9 image tags, 2 deprecated options)
- manila-helm-overrides.yaml (13 image tags)
- masakari-helm-overrides.yaml (8 image tags, 2 deprecated options)
- octavia-helm-overrides.yaml (13 image tags, 2 deprecated options)
- trove-helm-overrides.yaml (1 deprecated option)
- zaqar-helm-overrides.yaml (1 deprecated option)

---

## How to Use

### Step 1: Review What Will Change (Dry Run)

```bash
cd upgrade-tools
python scripts/apply_config_updates.py ../base-helm-configs --dry-run --verbose
```

### Step 2: Apply the Updates

```bash
cd upgrade-tools
python scripts/apply_config_updates.py ../base-helm-configs
```

This will:
- ✅ Create backups automatically
- ✅ Update 206 image tags
- ✅ Remove 28 deprecated options
- ✅ Update 21 configuration files
- ✅ Print detailed summary

### Step 3: Verify the Updates

```bash
cd upgrade-tools
python scripts/validate_configs.py ../base-helm-configs --verbose
```

Expected results:
- ✅ Image tag issues: 0 (down from 206)
- ✅ Deprecated options: 0 (down from 28)
- ⚠️ YAML errors: 1 (false positive in all.yaml - ignore it)

---

## Safety Features

### Automatic Backups
Every file is backed up before modification to:
```
upgrade-tools/backups/config_backup_YYYYMMDD_HHMMSS/
```

### Dry Run Mode
Test the script without making changes:
```bash
python scripts/apply_config_updates.py ../base-helm-configs --dry-run
```

### Rollback Support
If needed, restore from backup:
```bash
cp -r upgrade-tools/backups/config_backup_YYYYMMDD_HHMMSS/* ../base-helm-configs/
```

### Detailed Logging
See exactly what's being changed:
```bash
python scripts/apply_config_updates.py ../base-helm-configs --verbose
```

---

## Example Output

```
2026-02-04 09:05:16 - INFO - Found 49 files to process
2026-02-04 09:05:16 - INFO - Updating cinder-helm-overrides.yaml: 12 image tags, 2 deprecated options
2026-02-04 09:05:16 - INFO - Updating nova-helm-overrides.yaml: 20 image tags, 2 deprecated options
2026-02-04 09:05:16 - INFO - Updating neutron-helm-overrides.yaml: 23 image tags, 2 deprecated options
...

================================================================================
UPDATE SUMMARY
================================================================================
Files processed: 49
Files updated: 21
Image tags updated: 206
Deprecated options removed: 28
Errors: 0

Backups saved to: upgrade-tools/backups/config_backup_20260204_090516
================================================================================
```

---

## Documentation

- **Usage Guide:** `upgrade-tools/APPLY_UPDATES_GUIDE.md`
- **Files to Update:** `upgrade-tools/FILES_TO_UPDATE.md`
- **Script Location:** `upgrade-tools/scripts/apply_config_updates.py`

---

## Next Steps

1. **Review the dry run output** to understand what will change
2. **Run the script** to apply updates (backups created automatically)
3. **Verify the changes** with the validation script
4. **Test in lab environment** before production
5. **Proceed with upgrade** using the version manager
