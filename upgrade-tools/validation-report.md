# Configuration Validation Report

**Generated:** 2026-02-03 16:38:28
**Base Path:** ../base-helm-configs

## Summary

- **Total Files Scanned:** 62
- **Files with Issues:** 22
- **Total Issues:** 244
- **Has Errors:** Yes
- **Has Critical Issues:** No

### Issue Breakdown

- **YAML Errors:** 1
- **YAML Warnings:** 4
- **Image Tag Issues:** 206
- **Deprecated Options:** 33

## YAML Validation Errors

The following files have YAML syntax or structure errors:

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/openstack-api-exporter-chart/templates/all.yaml
**Line 10:** Invalid YAML syntax: expected a single document in the stream
  in "<unicode string>", line 2, column 1:
    apiVersion: v1
    ^
but found another document
  in "<unicode string>", line 10, column 1:
    ---
    ^
**Remediation:** Fix YAML syntax errors. Check for proper indentation, quotes, and structure.

## Image Tag Updates Required

The following image tags contain Caracal version strings and should be updated:

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/cinder/cinder-helm-overrides.yaml

- **images.tags.bootstrap**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.cinder_api**
  - Current: `ghcr.io/rackerlabs/genestack-images/cinder:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/cinder:2025.1-latest`
- **images.tags.cinder_backup**
  - Current: `ghcr.io/rackerlabs/genestack-images/cinder:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/cinder:2025.1-latest`
- **images.tags.cinder_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/cinder:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/cinder:2025.1-latest`
- **images.tags.cinder_scheduler**
  - Current: `ghcr.io/rackerlabs/genestack-images/cinder:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/cinder:2025.1-latest`
- **images.tags.cinder_volume**
  - Current: `ghcr.io/rackerlabs/genestack-images/cinder:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/cinder:2025.1-latest`
- **images.tags.cinder_volume_usage_audit**
  - Current: `ghcr.io/rackerlabs/genestack-images/cinder:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/cinder:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/gnocchi/gnocchi-helm-overrides.yaml

- **images.tags.db_init**
  - Current: `quay.io/rackspace/rackerlabs-gnocchi:2024.1-ubuntu_jammy`
  - Recommended: `quay.io/rackspace/rackerlabs-gnocchi:2025.1-ubuntu_jammy`
- **images.tags.db_sync**
  - Current: `quay.io/rackspace/rackerlabs-gnocchi:2024.1-ubuntu_jammy`
  - Recommended: `quay.io/rackspace/rackerlabs-gnocchi:2025.1-ubuntu_jammy`
- **images.tags.gnocchi_api**
  - Current: `quay.io/rackspace/rackerlabs-gnocchi:2024.1-ubuntu_jammy`
  - Recommended: `quay.io/rackspace/rackerlabs-gnocchi:2025.1-ubuntu_jammy`
- **images.tags.gnocchi_metricd**
  - Current: `quay.io/rackspace/rackerlabs-gnocchi:2024.1-ubuntu_jammy`
  - Recommended: `quay.io/rackspace/rackerlabs-gnocchi:2025.1-ubuntu_jammy`
- **images.tags.gnocchi_resources_cleaner**
  - Current: `quay.io/rackspace/rackerlabs-gnocchi:2024.1-ubuntu_jammy`
  - Recommended: `quay.io/rackspace/rackerlabs-gnocchi:2025.1-ubuntu_jammy`
- **images.tags.gnocchi_statsd**
  - Current: `quay.io/rackspace/rackerlabs-gnocchi:2024.1-ubuntu_jammy`
  - Recommended: `quay.io/rackspace/rackerlabs-gnocchi:2025.1-ubuntu_jammy`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/heat/heat-helm-overrides.yaml

- **images.tags.bootstrap**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.heat_api**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.heat_cfn**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.heat_cloudwatch**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.heat_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.heat_engine**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.heat_engine_cleaner**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.heat_purge_deleted**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/manila/manila-helm-overrides.yaml

- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.manila**
  - Current: `ghcr.io/rackerlabs/genestack-images/manila:2024.1-1763166117`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/manila:2025.1-1763166117`
- **images.tags.manila_api**
  - Current: `ghcr.io/rackerlabs/genestack-images/manila-api:2024.1-1763166117`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/manila-api:2025.1-1763166117`
- **images.tags.manila_data**
  - Current: `ghcr.io/rackerlabs/genestack-images/manila-data:2024.1-1763166117`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/manila-data:2025.1-1763166117`
- **images.tags.manila_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/manila:2024.1-1763166117`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/manila:2025.1-1763166117`
- **images.tags.manila_scheduler**
  - Current: `ghcr.io/rackerlabs/genestack-images/manila-scheduler:2024.1-1763166117`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/manila-scheduler:2025.1-1763166117`
- **images.tags.manila_share**
  - Current: `ghcr.io/rackerlabs/genestack-images/manila-share:2024.1-1763166117`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/manila-share:2025.1-1763166117`
- **images.tags.manila_processor**
  - Current: `ghcr.io/rackerlabs/genestack-images/manila:2024.1-1763166117`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/manila:2025.1-1763166117`
- **images.tags.manila_storage_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/manila:2024.1-1763166117`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/manila:2025.1-1763166117`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/octavia/octavia-helm-overrides.yaml

- **images.tags.bootstrap**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.octavia_api**
  - Current: `ghcr.io/rackerlabs/genestack-images/octavia:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/octavia:2025.1-latest`
- **images.tags.octavia_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/octavia:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/octavia:2025.1-latest`
- **images.tags.octavia_health_manager**
  - Current: `ghcr.io/rackerlabs/genestack-images/octavia:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/octavia:2025.1-latest`
- **images.tags.octavia_health_manager_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.octavia_housekeeping**
  - Current: `ghcr.io/rackerlabs/genestack-images/octavia:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/octavia:2025.1-latest`
- **images.tags.octavia_worker_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.octavia_worker**
  - Current: `ghcr.io/rackerlabs/genestack-images/octavia:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/octavia:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/barbican/barbican-helm-overrides.yaml

- **images.tags.barbican_api**
  - Current: `ghcr.io/rackerlabs/genestack-images/barbican:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/barbican:2025.1-latest`
- **images.tags.barbican_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/barbican:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/barbican:2025.1-latest`
- **images.tags.bootstrap**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.scripted_test**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/designate/designate-helm-overrides.yaml

- **images.tags.bootstrap**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.designate_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/designate:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/designate:2025.1-latest`
- **images.tags.designate_api**
  - Current: `ghcr.io/rackerlabs/genestack-images/designate:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/designate:2025.1-latest`
- **images.tags.designate_central**
  - Current: `ghcr.io/rackerlabs/genestack-images/designate:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/designate:2025.1-latest`
- **images.tags.designate_mdns**
  - Current: `ghcr.io/rackerlabs/genestack-images/designate:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/designate:2025.1-latest`
- **images.tags.designate_worker**
  - Current: `ghcr.io/rackerlabs/genestack-images/designate:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/designate:2025.1-latest`
- **images.tags.designate_producer**
  - Current: `ghcr.io/rackerlabs/genestack-images/designate:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/designate:2025.1-latest`
- **images.tags.designate_sink**
  - Current: `ghcr.io/rackerlabs/genestack-images/designate:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/designate:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/ceilometer/ceilometer-helm-overrides.yaml

- **images.tags.ceilometer_db_sync**
  - Current: `quay.io/rackspace/rackerlabs-ceilometer:2024.1-ubuntu_jammy`
  - Recommended: `quay.io/rackspace/rackerlabs-ceilometer:2025.1-ubuntu_jammy`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ceilometer_central**
  - Current: `quay.io/rackspace/rackerlabs-ceilometer:2024.1-ubuntu_jammy`
  - Recommended: `quay.io/rackspace/rackerlabs-ceilometer:2025.1-ubuntu_jammy`
- **images.tags.ceilometer_compute**
  - Current: `quay.io/rackspace/rackerlabs-ceilometer:2024.1-ubuntu_jammy`
  - Recommended: `quay.io/rackspace/rackerlabs-ceilometer:2025.1-ubuntu_jammy`
- **images.tags.ceilometer_ipmi**
  - Current: `quay.io/rackspace/rackerlabs-ceilometer:2024.1-ubuntu_jammy`
  - Recommended: `quay.io/rackspace/rackerlabs-ceilometer:2025.1-ubuntu_jammy`
- **images.tags.ceilometer_notification**
  - Current: `quay.io/rackspace/rackerlabs-ceilometer:2024.1-ubuntu_jammy`
  - Recommended: `quay.io/rackspace/rackerlabs-ceilometer:2025.1-ubuntu_jammy`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/masakari/masakari-helm-overrides.yaml

- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/masakari:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/masakari:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.masakari_api**
  - Current: `ghcr.io/rackerlabs/genestack-images/masakari:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/masakari:2025.1-latest`
- **images.tags.masakari_engine**
  - Current: `ghcr.io/rackerlabs/genestack-images/masakari:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/masakari:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/nova/nova-helm-overrides.yaml

- **images.tags.bootstrap**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.nova_api**
  - Current: `ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest`
- **images.tags.nova_archive_deleted_rows**
  - Current: `ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest`
- **images.tags.nova_cell_setup**
  - Current: `ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest`
- **images.tags.nova_cell_setup_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.nova_compute**
  - Current: `ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest`
- **images.tags.nova_compute_ironic**
  - Current: `ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest`
- **images.tags.nova_compute_ssh**
  - Current: `ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest`
- **images.tags.nova_conductor**
  - Current: `ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest`
- **images.tags.nova_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest`
- **images.tags.nova_novncproxy**
  - Current: `ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest`
- **images.tags.nova_novncproxy_assets**
  - Current: `ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest`
- **images.tags.nova_scheduler**
  - Current: `ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest`
- **images.tags.nova_spiceproxy**
  - Current: `ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest`
- **images.tags.nova_spiceproxy_assets**
  - Current: `ghcr.io/rackerlabs/genestack-images/nova:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/nova:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/cloudkitty/cloudkitty-helm-overrides.yaml

- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.cloudkitty_api**
  - Current: `ghcr.io/rackerlabs/genestack-images/cloudkitty:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/cloudkitty:2025.1-latest`
- **images.tags.cloudkitty_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/cloudkitty:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/cloudkitty:2025.1-latest`
- **images.tags.cloudkitty_processor**
  - Current: `ghcr.io/rackerlabs/genestack-images/cloudkitty:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/cloudkitty:2025.1-latest`
- **images.tags.cloudkitty_storage_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/cloudkitty:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/cloudkitty:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/neutron/neutron-helm-overrides.yaml

- **images.tags.bootstrap**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.neutron_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_dhcp**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_l3**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_l2gw**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_linuxbridge_agent**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_metadata**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_ovn_metadata**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_ovn_vpn**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_openvswitch_agent**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_server**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_rpc_server**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_bagpipe_bgp**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_netns_cleanup_cron**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_sriov_agent**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_sriov_agent_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_bgp_dragent**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`
- **images.tags.neutron_ironic_agent**
  - Current: `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/neutron:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/keystone/keystone-helm-overrides.yaml

- **images.tags.bootstrap**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.keystone_api**
  - Current: `ghcr.io/rackerlabs/genestack-images/keystone:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/keystone:2025.1-latest`
- **images.tags.keystone_credential_cleanup**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.keystone_credential_rotate**
  - Current: `ghcr.io/rackerlabs/genestack-images/keystone:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/keystone:2025.1-latest`
- **images.tags.keystone_credential_setup**
  - Current: `ghcr.io/rackerlabs/genestack-images/keystone:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/keystone:2025.1-latest`
- **images.tags.keystone_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/keystone:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/keystone:2025.1-latest`
- **images.tags.keystone_domain_manage**
  - Current: `ghcr.io/rackerlabs/genestack-images/keystone:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/keystone:2025.1-latest`
- **images.tags.keystone_fernet_rotate**
  - Current: `ghcr.io/rackerlabs/genestack-images/keystone:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/keystone:2025.1-latest`
- **images.tags.keystone_fernet_setup**
  - Current: `ghcr.io/rackerlabs/genestack-images/keystone:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/keystone:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/horizon/horizon-helm-overrides.yaml

- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.horizon_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/horizon:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/horizon:2025.1-latest`
- **images.tags.horizon**
  - Current: `ghcr.io/rackerlabs/genestack-images/horizon:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/horizon:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/ironic/ironic-helm-overrides.yaml

- **images.tags.ironic_manage_cleaning_network**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ironic_retrive_cleaning_network**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ironic_retrive_swift_config**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.bootstrap**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ironic_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/ironic-api:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/ironic-api:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ironic_api**
  - Current: `ghcr.io/rackerlabs/genestack-images/ironic-api:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/ironic-api:2025.1-latest`
- **images.tags.ironic_conductor**
  - Current: `ghcr.io/rackerlabs/genestack-images/ironic-conductor:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/ironic-conductor:2025.1-latest`
- **images.tags.ironic_pxe**
  - Current: `ghcr.io/rackerlabs/genestack-images/ironic-pxe:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/ironic-pxe:2025.1-latest`
- **images.tags.ironic_pxe_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/ironic-pxe:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/ironic-pxe:2025.1-latest`
- **images.tags.ironic_inspector**
  - Current: `ghcr.io/rackerlabs/genestack-images/ironic-inspector:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/ironic-inspector:2025.1-latest`
- **images.tags.ironic_inspector_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/ironic-inspector:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/ironic-inspector:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/glance/glance-helm-overrides.yaml

- **images.tags.glance_metadefs_load**
  - Current: `ghcr.io/rackerlabs/genestack-images/glance:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/glance:2025.1-latest`
- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.glance_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/glance:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/glance:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.glance_api**
  - Current: `ghcr.io/rackerlabs/genestack-images/glance:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/glance:2025.1-latest`
- **images.tags.bootstrap**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/magnum/magnum-helm-overrides.yaml

- **images.tags.bootstrap**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.magnum_api**
  - Current: `ghcr.io/rackerlabs/genestack-images/magnum:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/magnum:2025.1-latest`
- **images.tags.magnum_conductor**
  - Current: `ghcr.io/rackerlabs/genestack-images/magnum:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/magnum:2025.1-latest`
- **images.tags.magnum_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/magnum:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/magnum:2025.1-latest`

### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/placement/placement-helm-overrides.yaml

- **images.tags.db_drop**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.db_init**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_endpoints**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_service**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.ks_user**
  - Current: `ghcr.io/rackerlabs/genestack-images/heat:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/heat:2025.1-latest`
- **images.tags.placement**
  - Current: `ghcr.io/rackerlabs/genestack-images/placement:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/placement:2025.1-latest`
- **images.tags.placement_db_sync**
  - Current: `ghcr.io/rackerlabs/genestack-images/placement:2024.1-latest`
  - Recommended: `ghcr.io/rackerlabs/genestack-images/placement:2025.1-latest`

## Deprecated Configuration Options

The following deprecated options were found:

### HIGH Severity

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/cinder/cinder-helm-overrides.yaml
- **Option:** `conf.cinder.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/cinder/cinder-helm-overrides.yaml
- **Option:** `conf.cinder.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/heat/heat-helm-overrides.yaml
- **Option:** `conf.heat.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/heat/heat-helm-overrides.yaml
- **Option:** `conf.heat.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/octavia/octavia-helm-overrides.yaml
- **Option:** `conf.octavia.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/octavia/octavia-helm-overrides.yaml
- **Option:** `conf.octavia.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/barbican/barbican-helm-overrides.yaml
- **Option:** `conf.barbican.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/barbican/barbican-helm-overrides.yaml
- **Option:** `conf.barbican.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/designate/designate-helm-overrides.yaml
- **Option:** `conf.designate.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/designate/designate-helm-overrides.yaml
- **Option:** `conf.designate.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/ceilometer/ceilometer-helm-overrides.yaml
- **Option:** `conf.ceilometer.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/ceilometer/ceilometer-helm-overrides.yaml
- **Option:** `conf.ceilometer.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/masakari/masakari-helm-overrides.yaml
- **Option:** `conf.masakari.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/masakari/masakari-helm-overrides.yaml
- **Option:** `conf.masakari.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/trove/trove-helm-overrides.yaml
- **Option:** `conf.trove.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/trove/trove-helm-overrides.yaml
- **Option:** `conf.trove.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/nova/nova-helm-overrides.yaml
- **Option:** `conf.nova.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/nova/nova-helm-overrides.yaml
- **Option:** `conf.nova.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/zaqar/zaqar-helm-overrides.yaml
- **Option:** `conf.zaqar.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/zaqar/zaqar-helm-overrides.yaml
- **Option:** `conf.zaqar.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/neutron/neutron-helm-overrides.yaml
- **Option:** `images.tags.neutron_linuxbridge_agent`
- **Component:** neutron
- **Current Value:** `ghcr.io/rackerlabs/genestack-images/neutron:2024.1-latest`
- **Issue:** Linux Bridge driver removed in Epoxy
- **Action:** Use OVS or OVN mechanism driver

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/neutron/neutron-helm-overrides.yaml
- **Option:** `conf.neutron.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/neutron/neutron-helm-overrides.yaml
- **Option:** `conf.neutron.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/keystone/keystone-helm-overrides.yaml
- **Option:** `conf.keystone.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/keystone/keystone-helm-overrides.yaml
- **Option:** `conf.keystone.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/ironic/ironic-helm-overrides.yaml
- **Option:** `conf.ironic.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/ironic/ironic-helm-overrides.yaml
- **Option:** `conf.ironic.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/blazar/blazar-helm-overrides.yaml
- **Option:** `conf.blazar.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/blazar/blazar-helm-overrides.yaml
- **Option:** `conf.blazar.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/glance/glance-helm-overrides.yaml
- **Option:** `conf.glance.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/glance/glance-helm-overrides.yaml
- **Option:** `conf.glance.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/magnum/magnum-helm-overrides.yaml
- **Option:** `conf.magnum.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** The heartbeat_in_pthread option is deprecated as of 2024.2 and will be removed in a future release. Heartbeat threading is now handled automatically.
- **Action:** Remove this option - heartbeat threading is now automatic

#### /Users/jorge.perez/Projects/genestack/genestack-upgrade/upgrade-tools/../base-helm-configs/magnum/magnum-helm-overrides.yaml
- **Option:** `conf.magnum.oslo_messaging_rabbit.heartbeat_in_pthread`
- **Component:** oslo.messaging
- **Current Value:** `True`
- **Issue:** Deprecated in 2024.2, will be removed in future release
- **Action:** Remove this option

## Recommendations

⚠️ **CRITICAL:** Fix YAML errors before proceeding with upgrade.

1. Update all image tags to use Epoxy (2025.1) versions

2. Remove or update deprecated configuration options
