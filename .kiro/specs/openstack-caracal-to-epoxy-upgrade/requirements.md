# Requirements Document: OpenStack Caracal to Epoxy Upgrade

## Introduction

This document specifies the requirements for upgrading a Genestack OpenStack deployment from the Caracal (2024.1/2024.2) release to the Epoxy (2025.1) release. Genestack uses OpenStack-Helm charts deployed on Kubernetes to manage OpenStack services. Epoxy is a SLURP (Skip Level Upgrade Release Process) release, which allows direct upgrades from the previous SLURP release (Caracal), skipping intermediate releases.

The upgrade involves updating helm chart versions, validating configuration overrides for compatibility, identifying breaking changes, and ensuring service continuity throughout the process.

## Glossary

- **Upgrade_System**: The automated tooling and processes that perform the OpenStack upgrade
- **Chart_Version_Manager**: Component responsible for updating helm chart version specifications
- **Configuration_Validator**: Component that validates helm configuration overrides against new chart versions
- **Breaking_Change_Detector**: Component that identifies incompatible changes between releases
- **Service_Health_Monitor**: Component that monitors OpenStack service health during and after upgrade
- **Rollback_Manager**: Component that handles reverting to previous state if upgrade fails
- **Helm_Chart**: Kubernetes package containing OpenStack service definitions
- **Override_Configuration**: Custom YAML configuration that modifies default helm chart values
- **SLURP_Release**: Skip Level Upgrade Release Process - a stable OpenStack release supporting direct upgrades
- **Caracal**: OpenStack 2024.1/2024.2 release (current version)
- **Epoxy**: OpenStack 2025.1 release (target version)

## Requirements

### Requirement 1: Chart Version Updates

**User Story:** As a platform operator, I want to update all OpenStack helm chart versions from Caracal to Epoxy, so that the deployment uses the latest stable release.

#### Acceptance Criteria

1. WHEN the upgrade process begins, THE Chart_Version_Manager SHALL read the current helm-chart-versions.yaml file
2. WHEN updating chart versions, THE Chart_Version_Manager SHALL identify all OpenStack service charts that require version updates
3. WHEN a chart version is updated, THE Chart_Version_Manager SHALL replace the Caracal version string with the corresponding Epoxy version string
4. THE Chart_Version_Manager SHALL update versions for all core services (keystone, glance, cinder, neutron, nova, placement, horizon, libvirt)
5. THE Chart_Version_Manager SHALL update versions for all optional services (barbican, blazar, ceilometer, cloudkitty, freezer, gnocchi, heat, ironic, magnum, manila, masakari, octavia, trove, zaqar)
6. THE Chart_Version_Manager SHALL update versions for supporting infrastructure (memcached, mariadb-operator, postgres-operator, rabbitmq)
7. WHEN all versions are updated, THE Chart_Version_Manager SHALL write the updated helm-chart-versions.yaml file
8. WHEN version updates are complete, THE Chart_Version_Manager SHALL generate a summary report of all version changes

### Requirement 2: Configuration Override Validation

**User Story:** As a platform operator, I want to validate all helm configuration overrides against the new Epoxy chart versions, so that incompatible configurations are identified before deployment.

#### Acceptance Criteria

1. WHEN validation begins, THE Configuration_Validator SHALL enumerate all override files in base-helm-configs/
2. WHEN processing an override file, THE Configuration_Validator SHALL parse the YAML structure
3. WHEN validating image tags, THE Configuration_Validator SHALL identify any references to Caracal version strings (2024.1, 2024.2)
4. WHEN Caracal image tags are found, THE Configuration_Validator SHALL flag them for update to Epoxy versions (2025.1)
5. WHEN validating configuration sections, THE Configuration_Validator SHALL check for deprecated configuration options
6. WHEN deprecated options are found, THE Configuration_Validator SHALL document the deprecated option and its recommended replacement
7. WHEN validating oslo.messaging settings, THE Configuration_Validator SHALL check for the deprecated heartbeat_in_pthread option
8. WHEN validation completes, THE Configuration_Validator SHALL generate a report listing all required configuration changes
9. WHEN validation finds no issues, THE Configuration_Validator SHALL report successful validation

### Requirement 3: Breaking Change Detection

**User Story:** As a platform operator, I want to identify all breaking changes between Caracal and Epoxy, so that I can plan mitigation strategies before the upgrade.

#### Acceptance Criteria

1. THE Breaking_Change_Detector SHALL document all API changes between Caracal and Epoxy
2. THE Breaking_Change_Detector SHALL document all configuration option changes between releases
3. THE Breaking_Change_Detector SHALL document all database schema changes between releases
4. WHEN a breaking change affects deployed services, THE Breaking_Change_Detector SHALL document the impact and required actions
5. WHEN breaking changes are identified, THE Breaking_Change_Detector SHALL prioritize them by severity (critical, high, medium, low)
6. THE Breaking_Change_Detector SHALL document any new service dependencies introduced in Epoxy
7. THE Breaking_Change_Detector SHALL document any removed or deprecated features in Epoxy
8. WHEN detection completes, THE Breaking_Change_Detector SHALL generate a comprehensive breaking changes report

### Requirement 4: Pre-Upgrade Validation

**User Story:** As a platform operator, I want to validate the system state before starting the upgrade, so that the upgrade has the best chance of success.

#### Acceptance Criteria

1. WHEN pre-upgrade validation begins, THE Upgrade_System SHALL verify all OpenStack services are healthy
2. WHEN checking service health, THE Upgrade_System SHALL verify all pods are in Running state
3. WHEN checking service health, THE Upgrade_System SHALL verify all OpenStack API endpoints are responding
4. WHEN validating the environment, THE Upgrade_System SHALL verify no active migrations or jobs are running
5. WHEN validating the environment, THE Upgrade_System SHALL verify sufficient cluster resources are available
6. WHEN validating backups, THE Upgrade_System SHALL verify database backups exist and are recent (within 24 hours)
7. WHEN validating backups, THE Upgrade_System SHALL verify configuration backups exist
8. IF any pre-upgrade validation fails, THEN THE Upgrade_System SHALL halt the upgrade and report the failure
9. WHEN all validations pass, THE Upgrade_System SHALL proceed to the upgrade phase

### Requirement 5: Upgrade Execution

**User Story:** As a platform operator, I want to execute the upgrade in a controlled manner, so that service disruption is minimized and issues can be detected early.

#### Acceptance Criteria

1. WHEN the upgrade begins, THE Upgrade_System SHALL apply updates in dependency order (infrastructure first, then core services, then optional services)
2. WHEN upgrading a service, THE Upgrade_System SHALL apply the updated helm chart with new version and configurations
3. WHEN a helm chart is applied, THE Upgrade_System SHALL wait for the deployment to stabilize before proceeding
4. WHEN waiting for stabilization, THE Upgrade_System SHALL monitor pod status and readiness probes
5. WHEN a service upgrade completes, THE Service_Health_Monitor SHALL verify the service API is responding correctly
6. WHEN upgrading database-backed services, THE Upgrade_System SHALL run database migrations (db-sync) before starting the service
7. WHEN upgrading Nova, THE Upgrade_System SHALL delete existing Nova jobs before applying the upgrade
8. IF a service upgrade fails, THEN THE Upgrade_System SHALL halt the upgrade and preserve the current state
9. WHEN all services are upgraded, THE Upgrade_System SHALL perform a final health check of all services

### Requirement 6: Post-Upgrade Verification

**User Story:** As a platform operator, I want to verify that all services are functioning correctly after the upgrade, so that I can confirm the upgrade was successful.

#### Acceptance Criteria

1. WHEN post-upgrade verification begins, THE Service_Health_Monitor SHALL check all pod statuses across all namespaces
2. WHEN verifying services, THE Service_Health_Monitor SHALL verify all OpenStack API endpoints are accessible
3. WHEN verifying compute services, THE Service_Health_Monitor SHALL run "openstack compute service list" and verify all services are up
4. WHEN verifying network services, THE Service_Health_Monitor SHALL run "openstack network agent list" and verify all agents are alive
5. WHEN verifying storage services, THE Service_Health_Monitor SHALL run "openstack volume service list" and verify all services are enabled
6. WHEN verifying functionality, THE Service_Health_Monitor SHALL test key operations (instance creation, network creation, volume creation)
7. WHEN monitoring logs, THE Service_Health_Monitor SHALL check for critical errors in service logs
8. IF any verification fails, THEN THE Service_Health_Monitor SHALL report the failure with detailed diagnostics
9. WHEN all verifications pass, THE Service_Health_Monitor SHALL report successful upgrade completion

### Requirement 7: Rollback Capability

**User Story:** As a platform operator, I want the ability to rollback to the previous version if the upgrade fails, so that service can be restored quickly.

#### Acceptance Criteria

1. WHEN a rollback is initiated, THE Rollback_Manager SHALL restore the previous helm-chart-versions.yaml file
2. WHEN rolling back configurations, THE Rollback_Manager SHALL restore all previous helm override configurations
3. WHEN rolling back services, THE Rollback_Manager SHALL apply the previous helm chart versions in reverse dependency order
4. WHEN rolling back databases, THE Rollback_Manager SHALL restore database backups if schema changes occurred
5. WHEN a service is rolled back, THE Rollback_Manager SHALL verify the service returns to healthy state
6. IF rollback fails for a service, THEN THE Rollback_Manager SHALL document the failure and provide manual recovery steps
7. WHEN rollback completes, THE Rollback_Manager SHALL verify all services are operational
8. WHEN rollback is complete, THE Rollback_Manager SHALL generate a rollback report documenting all actions taken

### Requirement 8: Documentation and Reporting

**User Story:** As a platform operator, I want comprehensive documentation of the upgrade process and results, so that I can understand what changed and troubleshoot any issues.

#### Acceptance Criteria

1. THE Upgrade_System SHALL maintain a detailed log of all upgrade actions performed
2. WHEN a chart version is updated, THE Upgrade_System SHALL log the old version, new version, and timestamp
3. WHEN a configuration is modified, THE Upgrade_System SHALL log the file path and changes made
4. WHEN a service is upgraded, THE Upgrade_System SHALL log the service name, status, and any errors encountered
5. WHEN the upgrade completes, THE Upgrade_System SHALL generate a summary report including all version changes
6. WHEN the upgrade completes, THE Upgrade_System SHALL generate a summary report including all configuration changes
7. WHEN the upgrade completes, THE Upgrade_System SHALL generate a summary report including upgrade duration and any issues encountered
8. THE Upgrade_System SHALL update or create upgrade documentation in docs/ directory
9. THE Upgrade_System SHALL document any manual steps required post-upgrade

### Requirement 9: Testing and Validation

**User Story:** As a platform operator, I want to test the upgrade process in a non-production environment, so that I can identify issues before upgrading production.

#### Acceptance Criteria

1. THE Upgrade_System SHALL support execution in a test/staging environment
2. WHEN running in test mode, THE Upgrade_System SHALL perform all upgrade steps without requiring production credentials
3. WHEN testing the upgrade, THE Upgrade_System SHALL validate all chart version updates
4. WHEN testing the upgrade, THE Upgrade_System SHALL validate all configuration changes
5. WHEN testing the upgrade, THE Upgrade_System SHALL simulate the upgrade process and report potential issues
6. THE Upgrade_System SHALL provide a dry-run mode that shows what would be changed without making changes
7. WHEN dry-run completes, THE Upgrade_System SHALL generate a report of all planned changes
8. THE Upgrade_System SHALL support automated testing of upgraded services
9. WHEN automated tests run, THE Upgrade_System SHALL verify basic OpenStack operations (create/delete instances, networks, volumes)
