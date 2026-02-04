# Files That Need Updates for Caracal → Epoxy Upgrade

## Critical Issues (Must Fix Before Upgrade)

### 1. YAML Syntax Error ⚠️ CRITICAL

**File:** `base-helm-configs/openstack-api-exporter-chart/templates/all.yaml`

**Issue:** Invalid multi-document YAML syntax at line 10

**Fix:** This file has multiple YAML documents but isn't properly formatted. You need to either:
- Separate into multiple files, OR
- Ensure proper YAML multi-document format with `---` separators

---

## Image Tag Updates (206 tags across 18 files)

These files have image tags referencing Caracal (2024.1) that need updating to Epoxy (2025.1):

### Core Services

1. **`base-helm-configs/cinder/cinder-helm-overrides.yaml`**
   - 12 image tags: bootstrap, cinder_api, cinder_backup, cinder_db_sync, cinder_scheduler, cinder_volume, etc.
   - Change: `2024.1-latest` → `2025.1-latest`

2. **`base-helm-configs/glance/glance-helm-overrides.yaml`**
   - 9 image tags: glance_api, glance_db_sync, glance_metadefs_load, db_init, db_drop, ks_* tags
   - Change: `2024.1-latest` → `2025.1-latest`

3. **`base-helm-configs/keystone/keystone-helm-overrides.yaml`**
   - 12 image tags: keystone_api, keystone_db_sync, keystone_fernet_setup, keystone_credential_*, etc.
   - Change: `2024.1-latest` → `2025.1-latest`

4. **`base-helm-configs/neutron/neutron-helm-overrides.yaml`**
   - 23 image tags: neutron_server, neutron_dhcp, neutron_l3, neutron_metadata, neutron_ovn_*, etc.
   - Change: `2024.1-latest` → `2025.1-latest`

5. **`base-helm-configs/nova/nova-helm-overrides.yaml`**
   - 20 image tags: nova_api, nova_compute, nova_conductor, nova_scheduler, nova_novncproxy, etc.
   - Change: `2024.1-latest` → `2025.1-latest`

6. **`base-helm-configs/placement/placement-helm-overrides.yaml`**
   - 7 image tags: placement, placement_db_sync, db_init, db_drop, ks_* tags
   - Change: `2024.1-latest` → `2025.1-latest`

7. **`base-helm-configs/horizon/horizon-helm-overrides.yaml`**
   - 4 image tags: horizon, horizon_db_sync, db_init, db_drop
   - Change: `2024.1-latest` → `2025.1-latest`

### Optional Services

8. **`base-helm-configs/barbican/barbican-helm-overrides.yaml`**
   - 9 image tags: barbican_api, barbican_db_sync, bootstrap, db_*, ks_* tags
   - Change: `2024.1-latest` → `2025.1-latest`

9. **`base-helm-configs/ceilometer/ceilometer-helm-overrides.yaml`**
   - 7 image tags: ceilometer_central, ceilometer_compute, ceilometer_notification, etc.
   - Change: `2024.1-ubuntu_jammy` → `2025.1-ubuntu_jammy`

10. **`base-helm-configs/cloudkitty/cloudkitty-helm-overrides.yaml`**
    - 9 image tags: cloudkitty_api, cloudkitty_processor, cloudkitty_db_sync, etc.
    - Change: `2024.1-latest` → `2025.1-latest`

11. **`base-helm-configs/designate/designate-helm-overrides.yaml`**
    - 13 image tags: designate_api, designate_central, designate_worker, designate_producer, etc.
    - Change: `2024.1-latest` → `2025.1-latest`

12. **`base-helm-configs/gnocchi/gnocchi-helm-overrides.yaml`**
    - 9 image tags: gnocchi_api, gnocchi_metricd, gnocchi_statsd, etc.
    - Change: `2024.1-ubuntu_jammy` → `2025.1-ubuntu_jammy`

13. **`base-helm-configs/heat/heat-helm-overrides.yaml`**
    - 13 image tags: heat_api, heat_engine, heat_cfn, heat_cloudwatch, etc.
    - Change: `2024.1-latest` → `2025.1-latest`

14. **`base-helm-configs/ironic/ironic-helm-overrides.yaml`**
    - 16 image tags: ironic_api, ironic_conductor, ironic_inspector, ironic_pxe, etc.
    - Change: `2024.1-latest` → `2025.1-latest`

15. **`base-helm-configs/magnum/magnum-helm-overrides.yaml`**
    - 9 image tags: magnum_api, magnum_conductor, magnum_db_sync, etc.
    - Change: `2024.1-latest` → `2025.1-latest`

16. **`base-helm-configs/manila/manila-helm-overrides.yaml`**
    - 13 image tags: manila_api, manila_share, manila_scheduler, manila_data, etc.
    - Change: `2024.1-1763166117` → `2025.1-1763166117`

17. **`base-helm-configs/masakari/masakari-helm-overrides.yaml`**
    - 8 image tags: masakari_api, masakari_engine, db_sync, etc.
    - Change: `2024.1-latest` → `2025.1-latest`

18. **`base-helm-configs/octavia/octavia-helm-overrides.yaml`**
    - 13 image tags: octavia_api, octavia_worker, octavia_health_manager, octavia_housekeeping, etc.
    - Change: `2024.1-latest` → `2025.1-latest`

---

## Deprecated Configuration Options (33 instances across 16 files)

These files have deprecated `oslo.messaging` configuration that should be removed:

### Files with `heartbeat_in_pthread` (deprecated in 2024.2)

1. **`base-helm-configs/barbican/barbican-helm-overrides.yaml`**
   - Remove: `conf.barbican.oslo_messaging_rabbit.heartbeat_in_pthread: True`

2. **`base-helm-configs/blazar/blazar-helm-overrides.yaml`**
   - Remove: `conf.blazar.oslo_messaging_rabbit.heartbeat_in_pthread: True`

3. **`base-helm-configs/ceilometer/ceilometer-helm-overrides.yaml`**
   - Remove: `conf.ceilometer.oslo_messaging_rabbit.heartbeat_in_pthread: True`

4. **`base-helm-configs/cinder/cinder-helm-overrides.yaml`**
   - Remove: `conf.cinder.oslo_messaging_rabbit.heartbeat_in_pthread: True`

5. **`base-helm-configs/designate/designate-helm-overrides.yaml`**
   - Remove: `conf.designate.oslo_messaging_rabbit.heartbeat_in_pthread: True`

6. **`base-helm-configs/glance/glance-helm-overrides.yaml`**
   - Remove: `conf.glance.oslo_messaging_rabbit.heartbeat_in_pthread: True`

7. **`base-helm-configs/heat/heat-helm-overrides.yaml`**
   - Remove: `conf.heat.oslo_messaging_rabbit.heartbeat_in_pthread: True`

8. **`base-helm-configs/ironic/ironic-helm-overrides.yaml`**
   - Remove: `conf.ironic.oslo_messaging_rabbit.heartbeat_in_pthread: True`

9. **`base-helm-configs/keystone/keystone-helm-overrides.yaml`**
   - Remove: `conf.keystone.oslo_messaging_rabbit.heartbeat_in_pthread: True`

10. **`base-helm-configs/magnum/magnum-helm-overrides.yaml`**
    - Remove: `conf.magnum.oslo_messaging_rabbit.heartbeat_in_pthread: True`

11. **`base-helm-configs/masakari/masakari-helm-overrides.yaml`**
    - Remove: `conf.masakari.oslo_messaging_rabbit.heartbeat_in_pthread: True`

12. **`base-helm-configs/neutron/neutron-helm-overrides.yaml`**
    - Remove: `conf.neutron.oslo_messaging_rabbit.heartbeat_in_pthread: True`
    - **ALSO:** Remove `images.tags.neutron_linuxbridge_agent` (Linux Bridge driver removed in Epoxy)

13. **`base-helm-configs/nova/nova-helm-overrides.yaml`**
    - Remove: `conf.nova.oslo_messaging_rabbit.heartbeat_in_pthread: True`

14. **`base-helm-configs/octavia/octavia-helm-overrides.yaml`**
    - Remove: `conf.octavia.oslo_messaging_rabbit.heartbeat_in_pthread: True`

15. **`base-helm-configs/trove/trove-helm-overrides.yaml`**
    - Remove: `conf.trove.oslo_messaging_rabbit.heartbeat_in_pthread: True`

16. **`base-helm-configs/zaqar/zaqar-helm-overrides.yaml`**
    - Remove: `conf.zaqar.oslo_messaging_rabbit.heartbeat_in_pthread: True`

---

## Summary

### Total Files Requiring Updates: 22 files

**By Priority:**

1. **CRITICAL (1 file):** Fix YAML syntax error
   - `base-helm-configs/openstack-api-exporter-chart/templates/all.yaml`

2. **HIGH (18 files):** Update image tags from 2024.1 → 2025.1
   - All core and optional service override files listed above

3. **HIGH (16 files):** Remove deprecated oslo.messaging options
   - All service override files with `heartbeat_in_pthread`

**Note:** Some files appear in multiple categories (e.g., cinder needs both image tag updates AND deprecated option removal).

---

## How to Apply These Updates

### Option 1: Manual Updates
Edit each file individually to make the changes listed above.

### Option 2: Automated Updates (Recommended)
The upgrade tools can help automate these updates:

```bash
# For image tag updates - the validator can generate recommendations
cd upgrade-tools
python scripts/validate_configs.py ../base-helm-configs --report validation-report.md

# The image validator has an apply_recommendations() method that can automate updates
# (This functionality is built into the code but needs a CLI wrapper)
```

### Option 3: Search and Replace
Use your editor's search/replace across files:

1. **Image tags:** Search for `2024.1` and replace with `2025.1`
2. **Deprecated options:** Search for `heartbeat_in_pthread` and remove those lines
3. **Linux Bridge:** Search for `neutron_linuxbridge_agent` and remove

---

## Verification

After making updates, re-run the validation:

```bash
cd upgrade-tools
python scripts/validate_configs.py ../base-helm-configs --verbose
```

You should see:
- ✅ 0 YAML errors
- ✅ 0 Image tag issues  
- ✅ 0 Deprecated options
