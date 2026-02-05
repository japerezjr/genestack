# Integration Testing for OpenStack Caracal to Epoxy Upgrade

This directory contains comprehensive integration testing documentation and tools for validating the OpenStack Caracal to Epoxy upgrade process.

## Overview

Integration testing validates the complete upgrade workflow in a realistic lab environment before production deployment. This ensures:

- The upgrade process works end-to-end
- All services upgrade successfully
- Rollback functionality works correctly
- No critical issues exist in the upgrade tooling

## Quick Start

### 1. Prerequisites

Before starting integration testing:

- Access to an OpenStack cloud for lab deployment
- Sufficient quota (3 instances, 24 vCPUs, 48GB RAM, 300GB storage)
- OpenStack CLI tools installed
- kubectl installed
- Genestack repository cloned to `/opt/genestack`

### 2. Set Up Environment

Create environment file at `~/lab-env.sh` (DO NOT commit to git):

```bash
cat > ~/lab-env.sh << 'EOF'
#!/bin/bash
export ACME_EMAIL="admin@example.com"
export GATEWAY_DOMAIN="lab.example.com"
export OS_CLOUD="my-openstack-cloud"
export OS_FLAVOR="m1.xlarge"
export LAB_NAME_PREFIX="caracal-to-epoxy-test"
EOF

chmod +x ~/lab-env.sh
source ~/lab-env.sh
```

### 3. Run Integration Testing Checklist

Use the interactive checklist script to guide you through testing:

```bash
cd /opt/genestack/upgrade-tools
./scripts/integration-test-checklist.sh
```

This script will:
- Check prerequisites
- Guide you through each testing phase
- Record test results
- Generate a summary report

### 4. Manual Testing (Alternative)

If you prefer manual testing, follow the detailed guide:

```bash
# Read the comprehensive testing guide
less docs/INTEGRATION_TESTING.md

# Follow each phase step-by-step
# Phase 1: Lab Deployment
# Phase 2: Pre-Upgrade Validation
# Phase 3: Upgrade Execution
# Phase 4: Post-Upgrade Verification
# Phase 5: Rollback Testing
```

## Testing Phases

### Phase 1: Lab Deployment (Subtask 15.1)

Deploy a fresh lab environment with Caracal release.

**Duration**: 20-30 minutes

**Key Steps**:
1. Source environment variables
2. Deploy lab: `./scripts/hyperconverged-lab.sh kubespray -x`
3. Verify deployment
4. Document lab IP and SSH access

**Success Criteria**:
- All Kubernetes nodes Ready
- All pods Running
- All OpenStack services healthy

### Phase 2: Pre-Upgrade Validation (Subtask 15.2)

Test the pre-upgrade validation script.

**Duration**: 10-15 minutes

**Key Steps**:
1. Run validation script
2. Verify all checks pass
3. Test failure detection
4. Verify validation reports

**Success Criteria**:
- Validation passes on healthy system
- Validation detects failures correctly
- Reports are accurate

### Phase 3: Upgrade Execution (Subtask 15.3)

Test the complete upgrade process.

**Duration**: 30-60 minutes

**Key Steps**:
1. Create baseline snapshot
2. Run dry-run upgrade
3. Run actual upgrade
4. Monitor progress
5. Verify completion

**Success Criteria**:
- Dry-run shows changes without applying
- Upgrade completes successfully
- All services upgraded to Epoxy
- No critical errors

### Phase 4: Post-Upgrade Verification (Subtask 15.4)

Verify all functionality after upgrade.

**Duration**: 15-20 minutes

**Key Steps**:
1. Run verification script
2. Test image operations
3. Test network operations
4. Test compute operations
5. Test volume operations

**Success Criteria**:
- All verification checks pass
- All OpenStack operations work
- Services report Epoxy versions

### Phase 5: Rollback Testing (Subtask 15.5)

Test rollback functionality.

**Duration**: 45-60 minutes (includes fresh lab deployment)

**Key Steps**:
1. Deploy fresh lab
2. Create backup
3. Start upgrade
4. Initiate rollback
5. Verify restoration

**Success Criteria**:
- Rollback executes successfully
- System restored to Caracal
- All services operational

## Documentation

### Comprehensive Guides

- **[INTEGRATION_TESTING.md](docs/INTEGRATION_TESTING.md)**: Complete step-by-step testing guide
- **[LAB_ENVIRONMENT_SETUP.md](docs/LAB_ENVIRONMENT_SETUP.md)**: Lab deployment and configuration
- **[README.md](README.md)**: Upgrade tools overview

### Scripts

- **[integration-test-checklist.sh](scripts/integration-test-checklist.sh)**: Interactive testing checklist
- **[pre-upgrade-validate.sh](scripts/pre-upgrade-validate.sh)**: Pre-upgrade validation
- **[upgrade-execute.sh](scripts/upgrade-execute.sh)**: Upgrade execution
- **[post-upgrade-verify.sh](scripts/post-upgrade-verify.sh)**: Post-upgrade verification
- **[rollback.sh](scripts/rollback.sh)**: Rollback execution

## Test Results

Test results are saved to `integration-test-results.txt` when using the checklist script.

Example results format:

```
Integration Testing Results - 2026-02-04 10:00:00
========================================
[2026-02-04 10:05:00] Phase: Prerequisites | Status: PASS | Details: All checks passed
[2026-02-04 10:35:00] Phase: Phase 1: Lab Deployment | Status: PASS | Details: Jump Host: 203.0.113.10
[2026-02-04 10:50:00] Phase: Phase 2: Pre-Upgrade Validation | Status: PASS | Details: All validation tests passed
[2026-02-04 11:45:00] Phase: Phase 3: Upgrade Execution | Status: PASS | Details: Duration: 45 minutes
[2026-02-04 12:05:00] Phase: Phase 4: Post-Upgrade Verification | Status: PASS | Details: All functional tests passed
[2026-02-04 13:15:00] Phase: Phase 5: Rollback Testing | Status: PASS | Details: Rollback successful
```

## Troubleshooting

### Common Issues

**Lab deployment fails**:
```bash
# Check OpenStack quota
openstack quota show

# Verify cloud configuration
openstack --os-cloud ${OS_CLOUD} server list
```

**Upgrade hangs**:
```bash
# Check pod status
kubectl describe pod -n openstack <pod-name>

# Check resource constraints
kubectl top nodes
```

**Rollback fails**:
```bash
# Check backup files
ls -la backup-*

# Manually restore if needed
cp backup-chart-versions.yaml /opt/genestack/helm-chart-versions.yaml
```

See [INTEGRATION_TESTING.md](docs/INTEGRATION_TESTING.md) for detailed troubleshooting.

## Next Steps

After successful integration testing:

1. **Review Results**: Ensure all phases passed
2. **Document Issues**: Create tickets for any problems
3. **Update Procedures**: Incorporate lessons learned
4. **Plan Production**: Schedule maintenance window
5. **Prepare Rollback**: Document rollback procedures
6. **Communicate**: Share results with stakeholders

## Support

For issues or questions:

- Review the [Genestack Documentation](https://docs.rackspacecloud.com/)
- Check [GitHub Issues](https://github.com/rackerlabs/genestack/issues)
- Contact your Genestack support team

---

**Last Updated**: 2026-02-04  
**Applies To**: OpenStack Caracal (2024.1/2024.2) to Epoxy (2025.1) Upgrade
