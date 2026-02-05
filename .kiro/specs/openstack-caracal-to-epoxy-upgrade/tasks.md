# Implementation Plan: OpenStack Caracal to Epoxy Upgrade

## Overview

This implementation plan breaks down the OpenStack Caracal to Epoxy upgrade into discrete, actionable tasks. The implementation is primarily Python-based with Bash wrapper scripts for execution convenience. The tooling is located in the `upgrade-tools/` directory and provides a comprehensive CLI interface for all upgrade operations. Each task builds incrementally, with testing integrated throughout to catch issues early.

The project uses **bd** (beads) for issue tracking. Tasks 1-13 have been completed, and tasks 14-17 are tracked as bd issues for remaining work.

## Tasks

- [x] 1. Set up project structure and core utilities
  - Create directory structure for upgrade tooling
  - Set up Python virtual environment and dependencies
  - Create configuration file schema for upgrade settings
  - Implement YAML file reading and writing utilities
  - _Requirements: 1.1, 1.7_

- [ ]* 1.1 Write property test for YAML round-trip
  - **Property 1: YAML Round-Trip Consistency**
  - **Validates: Requirements 1.1, 1.7**

- [x] 2. Implement Chart Version Manager
  - [x] 2.1 Create version parsing and comparison logic
    - Parse version strings from helm-chart-versions.yaml
    - Implement version comparison (Caracal vs Epoxy detection)
    - Create data structures for version updates
    - _Requirements: 1.1, 1.2_

  - [ ]* 2.2 Write property test for OpenStack service identification
    - **Property 2: OpenStack Service Identification**
    - **Validates: Requirements 1.2**

  - [x] 2.3 Implement version update logic
    - Create function to replace Caracal versions with Epoxy versions
    - Preserve non-OpenStack chart versions
    - Handle edge cases (missing versions, invalid formats)
    - _Requirements: 1.3_

  - [ ]* 2.4 Write property test for version string replacement
    - **Property 3: Version String Replacement**
    - **Validates: Requirements 1.3**

  - [x] 2.5 Implement version report generation
    - Create report data structure
    - Generate summary of all version changes
    - Format report for human readability
    - _Requirements: 1.8_

  - [ ]* 2.6 Write property test for version report completeness
    - **Property 4: Version Report Completeness**
    - **Validates: Requirements 1.8**

- [x] 3. Implement Configuration Validator
  - [x] 3.1 Create configuration file scanner
    - Recursively scan base-helm-configs/ directory
    - Filter for YAML files
    - Handle symbolic links and permissions
    - _Requirements: 2.1_

  - [ ]* 3.2 Write property test for override file discovery
    - **Property 5: Override File Discovery**
    - **Validates: Requirements 2.1**

  - [x] 3.3 Implement YAML validation logic
    - Parse YAML files with error handling
    - Validate structure against expected schema
    - Report parsing errors with line numbers
    - _Requirements: 2.2_

  - [ ]* 3.4 Write property test for YAML parsing robustness
    - **Property 6: YAML Parsing Robustness**
    - **Validates: Requirements 2.2**

  - [x] 3.5 Implement image tag validation
    - Extract image tags from configuration
    - Detect Caracal version strings (2024.1, 2024.2)
    - Generate update recommendations
    - _Requirements: 2.3, 2.4_

  - [ ]* 3.6 Write property tests for Caracal version detection and mapping
    - **Property 7: Caracal Version Detection**
    - **Property 8: Version Flag Mapping**
    - **Validates: Requirements 2.3, 2.4**

  - [x] 3.7 Implement deprecated option detection
    - Load deprecation rules from configuration
    - Scan configurations for deprecated options
    - Map deprecated options to replacements
    - _Requirements: 2.5, 2.6, 2.7_

  - [ ]* 3.8 Write property tests for deprecated option detection
    - **Property 9: Deprecated Option Detection**
    - **Property 10: Deprecation Documentation Completeness**
    - **Validates: Requirements 2.5, 2.6**

  - [x] 3.9 Implement validation report generation
    - Aggregate all validation issues
    - Categorize by severity
    - Generate actionable report with remediation steps
    - _Requirements: 2.8, 2.9_

  - [ ]* 3.10 Write property test for validation report completeness
    - **Property 11: Validation Report Completeness**
    - **Validates: Requirements 2.8**

- [x] 4. Checkpoint - Ensure validation tools work correctly
  - Run all tests for version manager and configuration validator
  - Test with sample helm-chart-versions.yaml and override files
  - Verify reports are generated correctly
  - Ask the user if questions arise

- [x] 5. Implement Breaking Change Detector
  - [x] 5.1 Create breaking change catalog
    - Define breaking change data structure
    - Load known Epoxy breaking changes from configuration
    - Include oslo.messaging, Ironic, Neutron changes
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [x] 5.2 Implement impact analysis
    - Match breaking changes against current configuration
    - Determine which changes affect the deployment
    - Prioritize by severity
    - _Requirements: 3.4, 3.5_

  - [x] 5.3 Generate breaking change report
    - Format report with component, description, impact, mitigation
    - Include severity and priority
    - Provide actionable remediation steps
    - _Requirements: 3.8_

  - [ ]* 5.4 Write property test for breaking change catalog completeness
    - **Property 12: Breaking Change Catalog Completeness**
    - **Validates: Requirements 3.1-3.8**

- [x] 6. Implement Pre-Upgrade Validation
  - [x] 6.1 Create Kubernetes pod status checker
    - Query Kubernetes API for pod status
    - Classify pods by state (Running, Pending, Failed)
    - Aggregate status across namespaces
    - _Requirements: 4.2_

  - [ ]* 6.2 Write property test for pod status classification
    - **Property 14: Pod Status Classification**
    - **Validates: Requirements 4.2**

  - [x] 6.3 Create OpenStack API endpoint checker
    - Test connectivity to all OpenStack API endpoints
    - Verify HTTP 200 responses
    - Handle authentication
    - _Requirements: 4.3_

  - [ ]* 6.4 Write property test for endpoint reachability check
    - **Property 15: Endpoint Reachability Check**
    - **Validates: Requirements 4.3**

  - [x] 6.5 Implement service health aggregation
    - Combine pod status, API checks, and service lists
    - Determine overall health status
    - Generate health report
    - _Requirements: 4.1_

  - [ ]* 6.6 Write property test for service health aggregation
    - **Property 13: Service Health Aggregation**
    - **Validates: Requirements 4.1**

  - [x] 6.7 Implement resource and backup validation
    - Check cluster resources (CPU, memory, storage)
    - Verify database backups exist and are recent
    - Check for active migrations or jobs
    - _Requirements: 4.4, 4.5, 4.6, 4.7_

  - [x] 6.8 Implement validation failure handling
    - Halt upgrade if any validation fails
    - Generate detailed failure report
    - Provide remediation steps
    - _Requirements: 4.8, 4.9_

  - [ ]* 6.9 Write property test for validation failure halts upgrade
    - **Property 16: Validation Failure Halts Upgrade**
    - **Validates: Requirements 4.8**

- [x] 7. Checkpoint - Ensure pre-upgrade validation works
  - Test validation against lab environment
  - Verify all health checks work correctly
  - Test failure scenarios
  - Ask the user if questions arise

- [x] 8. Implement Upgrade Execution Logic
  - [x] 8.1 Create service dependency graph
    - Define dependencies between OpenStack services
    - Implement topological sort for upgrade order
    - Handle circular dependency detection
    - _Requirements: 5.1_

  - [ ]* 8.2 Write property test for dependency order preservation
    - **Property 17: Dependency Order Preservation**
    - **Validates: Requirements 5.1**

  - [x] 8.3 Create Helm executor wrapper
    - Wrap helm CLI commands
    - Handle helm upgrade with overrides
    - Implement timeout and retry logic
    - Monitor deployment status
    - _Requirements: 5.2, 5.3, 5.4_

  - [x] 8.4 Implement per-service upgrade logic
    - Clean up existing jobs (for Nova)
    - Apply helm chart with updated version
    - Wait for deployment to stabilize
    - Verify service health after upgrade
    - _Requirements: 5.5, 5.6, 5.7_

  - [x] 8.5 Implement upgrade orchestration
    - Execute upgrades in dependency order
    - Monitor each service upgrade
    - Halt on first failure
    - Log all actions and results
    - _Requirements: 5.8, 5.9_

- [x] 9. Implement Rollback Manager
  - [x] 9.1 Create backup functionality
    - Backup helm-chart-versions.yaml
    - Backup all override configurations
    - Create database backups
    - Store backups with timestamps
    - _Requirements: 7.1, 7.2_

  - [x] 9.2 Implement restore functionality
    - Restore helm-chart-versions.yaml from backup
    - Restore override configurations from backup
    - Apply previous helm chart versions
    - Restore databases if needed
    - _Requirements: 7.3, 7.4_

  - [ ]* 9.3 Write property tests for rollback round-trip
    - **Property 18: Configuration Rollback Round-Trip**
    - **Property 19: Version Rollback Round-Trip**
    - **Validates: Requirements 7.1, 7.2**

  - [x] 9.4 Implement rollback verification
    - Verify all services return to healthy state
    - Check pod status after rollback
    - Verify API endpoints after rollback
    - Generate rollback report
    - _Requirements: 7.5, 7.6, 7.7, 7.8_

- [x] 10. Implement Logging and Reporting
  - [x] 10.1 Create structured logging system
    - Log all upgrade actions with timestamps
    - Include action type, component, and details
    - Support different log levels
    - Write logs to file and console
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 10.2 Write property test for action logging completeness
    - **Property 20: Action Logging Completeness**
    - **Validates: Requirements 8.1-8.4**

  - [x] 10.3 Implement summary report generation
    - Aggregate all version changes
    - Aggregate all configuration changes
    - Calculate total duration
    - List all issues encountered
    - _Requirements: 8.5, 8.6, 8.7_

  - [ ]* 10.4 Write property test for summary report completeness
    - **Property 21: Summary Report Completeness**
    - **Validates: Requirements 8.5-8.7**

  - [x] 10.5 Create upgrade documentation generator
    - Generate markdown documentation
    - Include all changes made
    - Document manual steps if needed
    - Update docs/ directory
    - _Requirements: 8.8, 8.9_

- [x] 11. Checkpoint - Ensure core upgrade logic works
  - Make sure to use bd to take/update/complete relevant tasks
  - Test upgrade execution in lab environment
  - Verify rollback functionality
  - Test logging and reporting
  - Ask the user if questions arise

- [x] 12. Create main upgrade orchestration script
  - [x] 12.1 Create CLI interface for upgrade tool
    - Implement argument parsing with subcommands
    - Support dry-run mode for all operations
    - Support configuration file input
    - Provide help and usage information
    - Main CLI entry point: `upgrade-tools/openstack-upgrade`
    - _Requirements: 9.6, 9.7_

  - [x] 12.2 Implement main upgrade workflow
    - Load configuration from YAML
    - Run pre-upgrade validation
    - Update chart versions and configurations
    - Execute upgrade in phases
    - Run post-upgrade verification
    - Generate final report
    - _Requirements: All_

  - [x] 12.3 Add error handling and recovery
    - Catch and handle all exceptions
    - Initiate rollback on failure
    - Provide clear error messages
    - Log all errors with context and stack traces
    - _Requirements: 5.8, 7.6_

- [x] 13. Create Bash wrapper scripts
  - [x] 13.1 Create pre-upgrade validation script
    - Bash wrapper for running validation checks: `scripts/pre-upgrade-validate.sh`
    - Python implementation: `scripts/validate_pre_upgrade.py`
    - Output validation report to console and file
    - Exit with appropriate status codes
    - _Requirements: 4.1-4.9_

  - [x] 13.2 Create upgrade execution script
    - Bash wrapper for running full upgrade: `scripts/upgrade-execute.sh`
    - Python orchestration via CLI: `openstack-upgrade execute`
    - Support dry-run mode
    - Handle interruption gracefully with cleanup
    - _Requirements: 5.1-5.9_

  - [x] 13.3 Create rollback script
    - Bash wrapper for initiating rollback: `scripts/rollback.sh`
    - Python implementation via CLI: `openstack-upgrade rollback`
    - Verify rollback success
    - Generate rollback report
    - _Requirements: 7.1-7.8_

  - [x] 13.4 Create post-upgrade verification script
    - Bash wrapper: `scripts/post-upgrade-verify.sh`
    - Run all post-upgrade checks
    - Test key operations (instance, network, volume creation)
    - Generate verification report
    - _Requirements: 6.1-6.9_

- [x] 14. Create lab environment setup documentation
  - **bd issue**: genestack-upgrade-v6x
  - Lab environment documentation is located in `upgrade-tools/docs/LAB_ENVIRONMENT_SETUP.md`
  
  - [x] 14.1 Document environment variable requirements
    - List all required environment variables
    - Provide example values
    - Create template environment file
    - Document location: `upgrade-tools/docs/LAB_ENVIRONMENT_SETUP.md`
    - _Requirements: 9.1, 9.2_

  - [x] 14.2 Document lab deployment process
    - Document hyperconverged-lab.sh usage
    - Explain deployment timeline (20-30 minutes)
    - Document SSH access procedure
    - Include troubleshooting common deployment issues
    - _Requirements: 9.3_

  - [x] 14.3 Create lab testing guide
    - Document how to test upgrade in lab
    - Provide test scenarios (happy path, failure scenarios)
    - Document expected results for each scenario
    - Include validation checklist
    - _Requirements: 9.4, 9.5, 9.8, 9.9_

- [ ] 15. Integration testing in lab environment
  - **bd issue**: genestack-upgrade-5nk
  - Environment variable file is located outside of current directory as it should not ever be included in github: ~/lab-env.sh
  
  - [ ] 15.1 Deploy lab with Caracal release
    - Source environment variables from ~/lab-env.sh
    - Run hyperconverged-lab.sh script with -x flag
    - Wait for deployment (20-30 minutes)
    - Verify deployment successful (all pods Running)
    - Document lab IP and SSH access details

  - [ ] 15.2 Test pre-upgrade validation
    - Run validation script: `./scripts/pre-upgrade-validate.sh`
    - Verify all checks pass (pod status, API endpoints, backups)
    - Test failure scenarios (stop a service, verify validation fails)
    - Verify validation reports are generated correctly

  - [ ] 15.3 Test upgrade execution
    - Run upgrade script in dry-run mode: `./openstack-upgrade execute --dry-run`
    - Review planned changes in output
    - Run actual upgrade: `./openstack-upgrade execute`
    - Monitor progress and logs in real-time
    - Verify upgrade completes successfully

  - [ ] 15.4 Test post-upgrade verification
    - Run verification script: `./scripts/post-upgrade-verify.sh`
    - Test OpenStack operations (create instance, network, volume)
    - Verify all services healthy and responding
    - Review upgrade report and verify completeness

  - [ ] 15.5 Test rollback functionality
    - Deploy fresh lab environment
    - Start upgrade and simulate failure mid-process
    - Initiate rollback: `./openstack-upgrade rollback`
    - Verify system restored to Caracal state
    - Review rollback report and verify all services operational

- [ ] 16. Create production upgrade documentation
  - **bd issue**: genestack-upgrade-80z
  
  - [ ] 16.1 Update docs/2024.1-to-2025.1.md
    - Document complete upgrade procedure with all steps
    - Include all prerequisites (backups, resource checks, maintenance window)
    - Document expected timeline (30 minutes to 4 hours depending on deployment size)
    - Include troubleshooting section with common issues and solutions
    - Add references to upgrade tool documentation
    - _Requirements: 8.8_

  - [ ] 16.2 Create upgrade runbook
    - Step-by-step upgrade instructions for operators
    - Include validation checkpoints after each phase
    - Document rollback procedure with decision criteria
    - Include emergency contacts and escalation procedures
    - Add pre-flight checklist and post-upgrade verification checklist

  - [ ] 16.3 Create operator guide
    - Document tool usage with examples: `openstack-upgrade --help`
    - Explain configuration options in `config/upgrade-config.yaml`
    - Provide examples for common scenarios (dry-run, partial upgrade, rollback)
    - Include FAQ section addressing common questions
    - Document log locations and how to interpret logs

- [ ] 17. Final checkpoint - Complete end-to-end testing
  - **bd issue**: genestack-upgrade-utk
  
  - Run complete upgrade in lab environment from start to finish
  - Verify all functionality works as documented
  - Test all edge cases and error scenarios (network failures, resource exhaustion, service failures)
  - Validate all scripts and tools work correctly
  - Ensure all documentation is complete and accurate
  - Verify upgrade can be performed by following documentation alone
  - Test rollback from various failure points
  - Validate logging and reporting are comprehensive
  - Ask the user if questions arise or if ready for production deployment

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples and edge cases
- Lab environment testing is critical before production upgrade
- The implementation is Python-based with Bash wrapper scripts for convenience
- All scripts are designed to be idempotent where possible
- Comprehensive logging is essential for troubleshooting
- Tasks 1-13 are complete; tasks 14-17 are tracked in bd (beads) issue tracker
- Use `bd ready` to see available work and `bd show <id>` for task details
- Main CLI tool: `upgrade-tools/openstack-upgrade` with subcommands for all operations
- Configuration: `upgrade-tools/config/upgrade-config.yaml`
- Documentation: `upgrade-tools/docs/` and `upgrade-tools/README.md`
