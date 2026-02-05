# End-to-End Testing Guide

## Overview

This document provides comprehensive guidance for performing complete end-to-end testing of the OpenStack Caracal to Epoxy upgrade process. This is the final checkpoint (Task 17) before production deployment.

**Purpose**: Validate that the entire upgrade process works correctly from start to finish, including all edge cases, error scenarios, and recovery procedures.

**Scope**: Complete testing of all upgrade components, scripts, documentation, and operational procedures.

## Testing Objectives

1. **Functional Validation**: Verify all upgrade functionality works as documented
2. **Edge Case Testing**: Test boundary conditions and unusual scenarios
3. **Error Scenario Testing**: Validate error handling and recovery procedures
4. **Documentation Validation**: Ensure upgrade can be performed following documentation alone
5. **Rollback Testing**: Verify rollback works from various failure points
6. **Logging Validation**: Confirm logging and reporting are comprehensive
7. **Production Readiness**: Determine if the upgrade process is ready for production

## Prerequisites

Before starting end-to-end testing:

- [ ] All previous tasks (1-16) completed
- [ ] Lab environment available for testing
- [ ] Access to OpenStack cloud for lab deployment
- [ ] All documentation reviewed and up-to-date
- [ ] Test plan reviewed and approved
- [ ] Sufficient time allocated (8-12 hours for complete testing)

## Test Environment Setup

### 1. Prepare Test Environment

```bash
# Clone repository if not already done
cd /opt
git clone https://github.com/rackerlabs/genestack.git
cd genestack

# Ensure upgrade tools are available
ls -la upgrade-tools/

# Create environment configuration
cat > ~/lab-env.sh << 'EOF'
#!/bin/bash
export ACME_EMAIL="test@example.com"
export GATEWAY_DOMAIN="lab.test.local"
export OS_CLOUD="my-cloud"
export OS_FLAVOR="m1.xlarge"
export LAB_NAME_PREFIX="e2e-test"
export LAB_NETWORK_MTU="1500"
echo "Environment variables loaded"
EOF

chmod +x ~/lab-env.sh
source ~/lab-env.sh
```

### 2. Verify Prerequisites

```bash
# Run prerequisite check
cd upgrade-tools
./scripts/integration-test-checklist.sh
```

## Test Execution Plan

### Phase 1: Happy Path Testing

**Objective**: Verify the upgrade works correctly under ideal conditions.

#### 1.1 Fresh Lab Deployment

```bash
# Deploy lab with Caracal
cd /opt/genestack
source ~/lab-env.sh
./scripts/hyperconverged-lab.sh kubespray -x

# Wait for deployment (20-30 minutes)
# Document start time and completion time
```

**Validation**:
- [ ] Lab deploys successfully
- [ ] All nodes reach Ready state
- [ ] All pods reach Running state
- [ ] All OpenStack services are healthy
- [ ] SSH access works
- [ ] Deployment time within expected range (20-30 minutes)

#### 1.2 Pre-Upgrade Validation

```bash
# SSH into lab
ssh ubuntu@<JUMP_HOST_IP>

# Run pre-upgrade validation
cd /opt/genestack/upgrade-tools
./scripts/pre-upgrade-validate.sh

# Review report
cat validation-report.md
```

**Validation**:
- [ ] All validation checks pass
- [ ] Pod status check: PASS
- [ ] API endpoints check: PASS
- [ ] Service health check: PASS
- [ ] Backup validation: PASS
- [ ] Resource availability: PASS
- [ ] Report is clear and actionable

#### 1.3 Upgrade Execution (Dry-Run)

```bash
# Run dry-run
./openstack-upgrade upgrade --dry-run

# Review planned changes
cat version-update-report.md
```

**Validation**:
- [ ] Dry-run completes without errors
- [ ] All chart version updates listed
- [ ] Configuration changes documented
- [ ] Upgrade order displayed correctly
- [ ] No actual changes applied
- [ ] Report is comprehensive

#### 1.4 Upgrade Execution (Actual)

```bash
# Create baseline snapshot
openstack service list > pre-upgrade-services.txt
kubectl get pods -n openstack > pre-upgrade-pods.txt
cp /opt/genestack/helm-chart-versions.yaml pre-upgrade-versions.yaml

# Run upgrade
./scripts/upgrade-execute.sh 2>&1 | tee upgrade-execution.log

# Monitor in another terminal
kubectl get pods -n openstack -w
```

**Validation**:
- [ ] Upgrade starts successfully
- [ ] Services upgrade in correct order
- [ ] Each service health check passes
- [ ] All pods reach Running state
- [ ] No critical errors in logs
- [ ] Upgrade completes successfully
- [ ] Upgrade duration within expected range
- [ ] Upgrade report generated

#### 1.5 Post-Upgrade Verification

```bash
# Run post-upgrade verification
./scripts/post-upgrade-verify.sh

# Review report
cat verification-report.md

# Test operations
openstack image list
openstack network create test-net
openstack subnet create test-subnet --network test-net --subnet-range 192.168.100.0/24
openstack server create test-vm --flavor m1.small --image cirros --network test-net
openstack volume create test-vol --size 1
openstack server add volume test-vm test-vol

# Clean up
openstack server remove volume test-vm test-vol
openstack server delete test-vm
openstack volume delete test-vol
openstack subnet delete test-subnet
openstack network delete test-net
```

**Validation**:
- [ ] Post-upgrade verification passes
- [ ] All services report Epoxy versions
- [ ] Image operations work
- [ ] Network operations work
- [ ] Compute operations work
- [ ] Volume operations work
- [ ] No errors in service logs
- [ ] API response times acceptable

### Phase 2: Edge Case Testing

**Objective**: Test boundary conditions and unusual scenarios.

#### 2.1 Large Configuration Files

```bash
# Test with very large override files
# Create a large override file (>1MB)
python3 << 'EOF'
import yaml

config = {
    'conf': {
        f'section_{i}': {
            f'option_{j}': f'value_{j}' 
            for j in range(100)
        }
        for i in range(100)
    }
}

with open('/tmp/large-override.yaml', 'w') as f:
    yaml.dump(config, f)
EOF

# Validate large file
cd /opt/genestack/upgrade-tools
python3 -c "
from src.validation.config_validator import ConfigurationValidator
validator = ConfigurationValidator()
result = validator.validate_override('/tmp/large-override.yaml')
print(f'Validation result: {result.passed}')
"
```

**Validation**:
- [ ] Large files parse correctly
- [ ] Validation completes in reasonable time (<30 seconds)
- [ ] No memory issues
- [ ] Report generated correctly

#### 2.2 Missing or Corrupted Files

```bash
# Test with missing chart versions file
cd /opt/genestack
mv helm-chart-versions.yaml helm-chart-versions.yaml.backup

# Run validation
cd upgrade-tools
./scripts/pre-upgrade-validate.sh

# Should report error gracefully
# Restore file
cd /opt/genestack
mv helm-chart-versions.yaml.backup helm-chart-versions.yaml

# Test with corrupted YAML
echo "invalid: yaml: content:" > /tmp/corrupted.yaml
cd upgrade-tools
python3 -c "
from src.validation.yaml_validator import YAMLValidator
validator = YAMLValidator()
result = validator.validate_file('/tmp/corrupted.yaml')
print(f'Validation caught error: {not result.valid}')
"
```

**Validation**:
- [ ] Missing files detected and reported
- [ ] Corrupted files detected and reported
- [ ] Error messages are clear
- [ ] System doesn't crash
- [ ] Graceful error handling

#### 2.3 Circular Dependencies

```bash
# Test dependency resolution with circular dependencies
cd /opt/genestack/upgrade-tools
python3 << 'EOF'
from src.executor.dependency_graph import DependencyGraph

# Create graph with circular dependency
graph = DependencyGraph()
graph.add_dependency('service-a', 'service-b')
graph.add_dependency('service-b', 'service-c')
graph.add_dependency('service-c', 'service-a')

try:
    order = graph.get_upgrade_order()
    print(f"ERROR: Should have detected circular dependency")
except ValueError as e:
    print(f"SUCCESS: Circular dependency detected: {e}")
EOF
```

**Validation**:
- [ ] Circular dependencies detected
- [ ] Clear error message provided
- [ ] Upgrade halts before applying changes
- [ ] No partial upgrades applied

#### 2.4 Concurrent Modifications

```bash
# Test behavior when files are modified during upgrade
# This simulates external changes during upgrade process

# Start upgrade in background
cd /opt/genestack/upgrade-tools
./scripts/upgrade-execute.sh &
UPGRADE_PID=$!

# Wait a few seconds
sleep 5

# Modify chart versions file
cd /opt/genestack
echo "# Modified during upgrade" >> helm-chart-versions.yaml

# Wait for upgrade to complete
wait $UPGRADE_PID

# Check if upgrade detected the modification
# (Implementation should detect and warn or fail)
```

**Validation**:
- [ ] Concurrent modifications detected
- [ ] Appropriate warning or error generated
- [ ] System state remains consistent
- [ ] No data corruption

### Phase 3: Error Scenario Testing

**Objective**: Validate error handling and recovery procedures.

#### 3.1 Network Failure Simulation

```bash
# Deploy fresh lab
cd /opt/genestack
source ~/lab-env.sh
./scripts/hyperconverged-lab.sh kubespray -x

# SSH into lab
ssh ubuntu@<JUMP_HOST_IP>

# Start upgrade
cd /opt/genestack/upgrade-tools
./scripts/upgrade-execute.sh &
UPGRADE_PID=$!

# Simulate network issue by blocking API access temporarily
# (In another terminal)
sudo iptables -A OUTPUT -p tcp --dport 6443 -j DROP
sleep 30
sudo iptables -D OUTPUT -p tcp --dport 6443 -j DROP

# Check upgrade behavior
wait $UPGRADE_PID
echo "Exit code: $?"
```

**Validation**:
- [ ] Network failures detected
- [ ] Appropriate retries attempted
- [ ] Timeout handling works correctly
- [ ] Error logged with context
- [ ] System state preserved
- [ ] Recovery possible after network restored

#### 3.2 Resource Exhaustion

```bash
# Test behavior under resource constraints
# Create resource pressure
stress-ng --vm 4 --vm-bytes 90% --timeout 60s &

# Run upgrade during resource pressure
cd /opt/genestack/upgrade-tools
./scripts/upgrade-execute.sh

# Monitor resource usage
kubectl top nodes
kubectl top pods -n openstack
```

**Validation**:
- [ ] Resource constraints detected
- [ ] Appropriate warnings generated
- [ ] Upgrade throttles or waits for resources
- [ ] No pod evictions during upgrade
- [ ] System remains stable

#### 3.3 Service Failure During Upgrade

```bash
# Deploy fresh lab
cd /opt/genestack
source ~/lab-env.sh
./scripts/hyperconverged-lab.sh kubespray -x

# SSH into lab
ssh ubuntu@<JUMP_HOST_IP>

# Start upgrade
cd /opt/genestack/upgrade-tools
./scripts/upgrade-execute.sh &
UPGRADE_PID=$!

# Wait for a service to start upgrading
sleep 60

# Kill a service pod during upgrade
kubectl delete pod -n openstack $(kubectl get pods -n openstack -l application=keystone -o name | head -1)

# Check upgrade behavior
wait $UPGRADE_PID
echo "Exit code: $?"
```

**Validation**:
- [ ] Service failure detected
- [ ] Upgrade halts appropriately
- [ ] Error logged with details
- [ ] System state preserved
- [ ] Rollback can be initiated
- [ ] Clear recovery instructions provided

#### 3.4 Database Migration Failure

```bash
# Simulate database migration failure
# This requires modifying the upgrade process temporarily

cd /opt/genestack/upgrade-tools

# Create a test that simulates db-sync failure
python3 << 'EOF'
from src.executor.service_upgrader import ServiceUpgrader
from unittest.mock import patch, MagicMock

upgrader = ServiceUpgrader()

# Mock helm executor to simulate db-sync failure
with patch.object(upgrader, 'helm_executor') as mock_helm:
    mock_helm.run_db_sync.return_value = False
    
    result = upgrader.upgrade_service('keystone')
    
    if not result.success:
        print("SUCCESS: Database migration failure handled correctly")
    else:
        print("ERROR: Database migration failure not detected")
EOF
```

**Validation**:
- [ ] Database migration failures detected
- [ ] Upgrade halts before service restart
- [ ] Error logged with details
- [ ] Database state preserved
- [ ] Manual recovery steps provided
- [ ] Rollback possible

#### 3.5 Helm Deployment Timeout

```bash
# Test timeout handling
cd /opt/genestack/upgrade-tools

# Modify config to use very short timeout
cat > /tmp/test-config.yaml << 'EOF'
upgrade:
  timeout_per_service: 5  # Very short timeout
  namespace: openstack
EOF

# Run upgrade with short timeout
./openstack-upgrade upgrade --config /tmp/test-config.yaml
```

**Validation**:
- [ ] Timeout detected correctly
- [ ] Upgrade halts on timeout
- [ ] Error message is clear
- [ ] Partial deployment handled correctly
- [ ] Rollback possible
- [ ] Logs show timeout details

### Phase 4: Rollback Testing

**Objective**: Verify rollback works from various failure points.

#### 4.1 Rollback After Complete Upgrade

```bash
# Deploy fresh lab
cd /opt/genestack
source ~/lab-env.sh
./scripts/hyperconverged-lab.sh kubespray -x

# SSH into lab
ssh ubuntu@<JUMP_HOST_IP>

# Create backup
cd /opt/genestack/upgrade-tools
cp /opt/genestack/helm-chart-versions.yaml backup-versions.yaml
tar -czf backup-configs.tar.gz /opt/genestack/base-helm-configs/

# Run complete upgrade
./scripts/upgrade-execute.sh

# Verify upgrade completed
grep "2025.1" /opt/genestack/helm-chart-versions.yaml

# Initiate rollback
./scripts/rollback.sh 2>&1 | tee rollback.log

# Verify rollback
diff /opt/genestack/helm-chart-versions.yaml backup-versions.yaml
kubectl get pods -n openstack
openstack service list
```

**Validation**:
- [ ] Rollback completes successfully
- [ ] Chart versions restored to Caracal
- [ ] All services return to healthy state
- [ ] All pods reach Running state
- [ ] API endpoints accessible
- [ ] Basic operations work
- [ ] Rollback report generated
- [ ] Rollback duration acceptable

#### 4.2 Rollback After Partial Upgrade

```bash
# Deploy fresh lab
cd /opt/genestack
source ~/lab-env.sh
./scripts/hyperconverged-lab.sh kubespray -x

# SSH into lab
ssh ubuntu@<JUMP_HOST_IP>

# Create backup
cd /opt/genestack/upgrade-tools
cp /opt/genestack/helm-chart-versions.yaml backup-versions.yaml

# Start upgrade and interrupt after a few services
./scripts/upgrade-execute.sh &
UPGRADE_PID=$!

# Wait for a few services to upgrade
sleep 120

# Interrupt upgrade
kill $UPGRADE_PID

# Check state
kubectl get pods -n openstack
grep "2025.1" /opt/genestack/helm-chart-versions.yaml

# Initiate rollback
./scripts/rollback.sh 2>&1 | tee rollback-partial.log

# Verify rollback
kubectl get pods -n openstack
openstack service list
```

**Validation**:
- [ ] Partial upgrade state detected
- [ ] Rollback handles mixed versions
- [ ] All services rolled back correctly
- [ ] System returns to consistent state
- [ ] No orphaned resources
- [ ] Services operational after rollback

#### 4.3 Rollback After Service Failure

```bash
# Deploy fresh lab and simulate service failure during upgrade
cd /opt/genestack
source ~/lab-env.sh
./scripts/hyperconverged-lab.sh kubespray -x

# SSH into lab
ssh ubuntu@<JUMP_HOST_IP>

# Create backup
cd /opt/genestack/upgrade-tools
cp /opt/genestack/helm-chart-versions.yaml backup-versions.yaml

# Start upgrade
./scripts/upgrade-execute.sh &
UPGRADE_PID=$!

# Wait and then cause a service failure
sleep 60
kubectl delete deployment -n openstack keystone-api

# Wait for upgrade to detect failure
wait $UPGRADE_PID

# Initiate rollback
./scripts/rollback.sh 2>&1 | tee rollback-failure.log

# Verify rollback
kubectl get pods -n openstack
openstack service list
```

**Validation**:
- [ ] Service failure detected during upgrade
- [ ] Rollback initiated automatically or manually
- [ ] Failed service restored correctly
- [ ] Other services rolled back
- [ ] System returns to healthy state
- [ ] Clear error messages in logs

### Phase 5: Documentation Validation

**Objective**: Ensure upgrade can be performed following documentation alone.

#### 5.1 Fresh Operator Test

**Setup**: Have someone unfamiliar with the upgrade process follow the documentation.

**Documents to Test**:
1. LAB_ENVIRONMENT_SETUP.md
2. OPERATOR_GUIDE.md
3. UPGRADE_RUNBOOK.md
4. INTEGRATION_TESTING.md

**Process**:
```bash
# Operator follows documentation step-by-step
# Document any:
# - Unclear instructions
# - Missing steps
# - Incorrect commands
# - Confusing terminology
# - Missing prerequisites
```

**Validation**:
- [ ] All prerequisites clearly documented
- [ ] All steps are clear and unambiguous
- [ ] All commands work as documented
- [ ] No undocumented steps required
- [ ] Troubleshooting section helpful
- [ ] Expected outputs documented
- [ ] Timing estimates accurate

#### 5.2 Documentation Completeness Check

```bash
# Check all documentation files exist
cd /opt/genestack/upgrade-tools/docs

required_docs=(
    "LAB_ENVIRONMENT_SETUP.md"
    "OPERATOR_GUIDE.md"
    "UPGRADE_RUNBOOK.md"
    "INTEGRATION_TESTING.md"
    "END_TO_END_TESTING.md"
    "VALIDATION.md"
)

for doc in "${required_docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "✓ $doc exists"
    else
        echo "✗ $doc missing"
    fi
done

# Check main documentation
cd /opt/genestack/docs
if [ -f "2024.1-to-2025.1.md" ]; then
    echo "✓ Main upgrade documentation exists"
else
    echo "✗ Main upgrade documentation missing"
fi
```

**Validation**:
- [ ] All required documentation exists
- [ ] Documentation is up-to-date
- [ ] Cross-references are correct
- [ ] Examples are accurate
- [ ] Screenshots/diagrams included where helpful
- [ ] Version numbers correct

### Phase 6: Logging and Reporting Validation

**Objective**: Confirm logging and reporting are comprehensive.

#### 6.1 Log Completeness

```bash
# Run complete upgrade
cd /opt/genestack/upgrade-tools
./scripts/upgrade-execute.sh

# Check log file
cat upgrade.log

# Verify log contains:
# - Timestamp for each action
# - Service names
# - Version changes
# - Health check results
# - Any errors or warnings
# - Duration information
```

**Validation**:
- [ ] All actions logged
- [ ] Timestamps present
- [ ] Log levels appropriate
- [ ] Error context included
- [ ] Stack traces for exceptions
- [ ] No sensitive data in logs
- [ ] Log rotation works
- [ ] Logs parseable

#### 6.2 Report Completeness

```bash
# Check all reports generated
cd /opt/genestack/upgrade-tools

reports=(
    "validation-report.md"
    "version-update-report.md"
    "upgrade-report.md"
    "verification-report.md"
)

for report in "${reports[@]}"; do
    if [ -f "$report" ]; then
        echo "✓ $report exists"
        echo "  Lines: $(wc -l < $report)"
        echo "  Size: $(du -h $report | cut -f1)"
    else
        echo "✗ $report missing"
    fi
done
```

**Validation**:
- [ ] All reports generated
- [ ] Reports are well-formatted
- [ ] Reports contain all required information
- [ ] Reports are actionable
- [ ] Reports include timestamps
- [ ] Reports include summary sections
- [ ] Reports include details sections

#### 6.3 Audit Trail

```bash
# Verify audit trail is complete
cd /opt/genestack/upgrade-tools

# Check that all changes are documented
grep -E "Updated|Changed|Modified" upgrade.log | wc -l

# Verify all version changes logged
grep "version" upgrade.log | grep -E "2024\.[12].*2025\.1"

# Check all service upgrades logged
grep "Upgrading service" upgrade.log
```

**Validation**:
- [ ] All changes documented
- [ ] Change timestamps recorded
- [ ] User/initiator recorded
- [ ] Before/after states captured
- [ ] Audit trail immutable
- [ ] Audit trail complete

### Phase 7: Production Readiness Assessment

**Objective**: Determine if upgrade process is ready for production.

#### 7.1 Readiness Checklist

**Functional Requirements**:
- [ ] All upgrade functionality works correctly
- [ ] All validation checks work correctly
- [ ] All error scenarios handled appropriately
- [ ] Rollback works from all failure points
- [ ] All documentation complete and accurate
- [ ] All logging and reporting comprehensive

**Performance Requirements**:
- [ ] Upgrade completes within acceptable timeframe
- [ ] Resource utilization acceptable
- [ ] No performance degradation after upgrade
- [ ] API response times acceptable

**Reliability Requirements**:
- [ ] No data loss during upgrade
- [ ] No data corruption during upgrade
- [ ] Rollback preserves data integrity
- [ ] Error recovery works correctly

**Security Requirements**:
- [ ] No credentials in logs
- [ ] Backups encrypted
- [ ] Audit trail complete
- [ ] Access controls maintained

**Operational Requirements**:
- [ ] Runbook complete and tested
- [ ] Troubleshooting guide complete
- [ ] Support procedures documented
- [ ] Escalation paths defined

#### 7.2 Risk Assessment

**Identified Risks**:
1. **Risk**: [Description]
   - **Likelihood**: [High/Medium/Low]
   - **Impact**: [High/Medium/Low]
   - **Mitigation**: [Strategy]
   - **Status**: [Mitigated/Accepted/Monitoring]

2. **Risk**: [Description]
   - **Likelihood**: [High/Medium/Low]
   - **Impact**: [High/Medium/Low]
   - **Mitigation**: [Strategy]
   - **Status**: [Mitigated/Accepted/Monitoring]

#### 7.3 Go/No-Go Decision

**Criteria for Production Deployment**:
- [ ] All critical tests passed
- [ ] All high-priority issues resolved
- [ ] Documentation complete
- [ ] Rollback tested and verified
- [ ] Stakeholders informed
- [ ] Maintenance window scheduled
- [ ] Support team briefed
- [ ] Rollback plan approved

**Decision**: [GO / NO-GO]

**Rationale**: [Explanation of decision]

**Conditions**: [Any conditions or prerequisites for GO decision]

## Test Results Template

### Test Execution Summary

```
Test Date: YYYY-MM-DD
Tester: [Name]
Lab Environment: [Details]
Test Duration: [Hours]

Phase 1: Happy Path Testing
- Status: [PASS/FAIL]
- Duration: [Minutes]
- Issues: [Count]

Phase 2: Edge Case Testing
- Status: [PASS/FAIL]
- Test Cases: [Count]
- Issues: [Count]

Phase 3: Error Scenario Testing
- Status: [PASS/FAIL]
- Scenarios Tested: [Count]
- Issues: [Count]

Phase 4: Rollback Testing
- Status: [PASS/FAIL]
- Rollback Scenarios: [Count]
- Issues: [Count]

Phase 5: Documentation Validation
- Status: [PASS/FAIL]
- Documents Reviewed: [Count]
- Issues: [Count]

Phase 6: Logging and Reporting
- Status: [PASS/FAIL]
- Reports Validated: [Count]
- Issues: [Count]

Phase 7: Production Readiness
- Status: [READY/NOT READY]
- Critical Issues: [Count]
- High Priority Issues: [Count]

Overall Result: [PASS/FAIL]
Production Ready: [YES/NO]
```

### Issues Log

```
Issue #1:
- Phase: [Which phase]
- Severity: [Critical/High/Medium/Low]
- Description: [What happened]
- Steps to Reproduce: [How to reproduce]
- Expected Behavior: [What should happen]
- Actual Behavior: [What actually happened]
- Workaround: [If any]
- Resolution: [How it was fixed]
- Status: [Open/Resolved/Deferred]

Issue #2:
...
```

### Performance Metrics

```
Upgrade Performance:
- Total Duration: [Minutes]
- Pre-validation: [Minutes]
- Chart Updates: [Minutes]
- Service Upgrades: [Minutes]
- Post-verification: [Minutes]

Resource Utilization:
- Peak CPU: [%]
- Peak Memory: [GB]
- Peak Storage I/O: [MB/s]
- Network Traffic: [GB]

API Response Times:
- Pre-upgrade: [ms]
- During upgrade: [ms]
- Post-upgrade: [ms]

Service Startup Times:
- Fastest: [Service] - [Seconds]
- Slowest: [Service] - [Seconds]
- Average: [Seconds]
```

### Recommendations

```
For Production Deployment:
1. [Recommendation]
2. [Recommendation]
3. [Recommendation]

For Future Improvements:
1. [Improvement]
2. [Improvement]
3. [Improvement]

For Documentation:
1. [Update needed]
2. [Update needed]
3. [Update needed]
```

## Troubleshooting

### Common Issues During Testing

**Issue**: Lab deployment fails
```bash
# Check quota
openstack quota show

# Check for existing resources
openstack server list | grep ${LAB_NAME_PREFIX}

# Clean up old resources
openstack server delete <old-server>
```

**Issue**: Upgrade hangs
```bash
# Check pod status
kubectl get pods -n openstack

# Check pod logs
kubectl logs -n openstack <pod-name>

# Check events
kubectl get events -n openstack --sort-by='.lastTimestamp'
```

**Issue**: Rollback fails
```bash
# Check backup files
ls -la backup-*

# Manually restore if needed
cp backup-versions.yaml /opt/genestack/helm-chart-versions.yaml

# Force helm rollback
helm rollback -n openstack <release-name>
```

## Next Steps

After completing end-to-end testing:

1. **Review Results**: Analyze all test results and metrics
2. **Document Issues**: Create tickets for any problems found
3. **Update Documentation**: Incorporate lessons learned
4. **Brief Stakeholders**: Present findings and recommendations
5. **Plan Production**: Schedule maintenance window if ready
6. **Prepare Support**: Brief support team on procedures
7. **Final Approval**: Obtain sign-off for production deployment

## Conclusion

End-to-end testing is the final validation before production deployment. All phases must pass, all critical issues must be resolved, and all documentation must be complete before proceeding to production.

**Remember**: It's better to find issues in testing than in production. Be thorough, test all scenarios, and don't skip steps.

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-04  
**Applies To**: OpenStack Caracal to Epoxy Upgrade - Task 17 Final Checkpoint
