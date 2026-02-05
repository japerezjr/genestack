# Integration Testing Guide

This guide provides step-by-step instructions for performing integration testing of the OpenStack Caracal to Epoxy upgrade in a lab environment.

## Overview

Integration testing validates the complete upgrade process in a realistic environment before production deployment. This includes:

- Deploying a lab environment with Caracal
- Testing pre-upgrade validation
- Executing the upgrade process
- Verifying post-upgrade functionality
- Testing rollback capabilities

## Prerequisites

Before starting integration testing, ensure you have:

1. Access to an OpenStack cloud for lab deployment
2. Sufficient quota (3 instances, 24 vCPUs, 48GB RAM, 300GB storage)
3. OpenStack CLI tools installed and configured
4. Environment variables configured (see LAB_ENVIRONMENT_SETUP.md)
5. Genestack repository cloned to `/opt/genestack`

## Test Execution Workflow

### Phase 1: Lab Deployment (Subtask 15.1)

Deploy a fresh lab environment with Caracal release.

**Steps**:

1. **Prepare environment variables**:
   ```bash
   # Create environment file at ~/lab-env.sh
   # DO NOT commit this file to git!
   cat > ~/lab-env.sh << 'EOF'
   #!/bin/bash
   # Lab Environment Configuration
   
   export ACME_EMAIL="admin@example.com"
   export GATEWAY_DOMAIN="lab.example.com"
   export OS_CLOUD="my-openstack-cloud"
   export OS_FLAVOR="m1.xlarge"
   export LAB_NAME_PREFIX="caracal-to-epoxy-test"
   export LAB_NETWORK_MTU="1500"
   
   echo "Lab environment variables loaded"
   EOF
   
   chmod +x ~/lab-env.sh
   ```

2. **Source environment variables**:
   ```bash
   source ~/lab-env.sh
   ```


3. **Verify OpenStack connectivity**:
   ```bash
   openstack --os-cloud ${OS_CLOUD} server list
   openstack --os-cloud ${OS_CLOUD} flavor list
   ```

4. **Deploy lab with Caracal**:
   ```bash
   cd /opt/genestack
   ./scripts/hyperconverged-lab.sh kubespray -x
   ```

5. **Wait for deployment** (20-30 minutes):
   - Monitor deployment progress
   - Script will output status updates
   - Note any errors or warnings

6. **Document lab details**:
   ```bash
   # Save lab IP and access details
   echo "Lab deployed at: $(date)" > ~/lab-deployment-info.txt
   echo "Jump Host IP: <IP_FROM_OUTPUT>" >> ~/lab-deployment-info.txt
   echo "SSH Command: ssh ubuntu@<IP>" >> ~/lab-deployment-info.txt
   ```

7. **Verify deployment**:
   ```bash
   # SSH into lab
   ssh ubuntu@<JUMP_HOST_IP>
   
   # Check Kubernetes
   kubectl get nodes
   kubectl get pods --all-namespaces | grep -v Running | grep -v Completed
   
   # Check OpenStack
   source /etc/genestack/openrc
   openstack service list
   openstack compute service list
   openstack network agent list
   ```

**Expected Results**:
- All Kubernetes nodes in Ready state
- All pods in Running or Completed state
- All OpenStack services listed
- All compute services up
- All network agents alive

**Completion Criteria**:
- Lab successfully deployed
- All services healthy
- SSH access confirmed
- Lab details documented

---

### Phase 2: Pre-Upgrade Validation Testing (Subtask 15.2)

Test the pre-upgrade validation script to ensure it correctly identifies system health.

**Steps**:

1. **Run pre-upgrade validation**:
   ```bash
   cd /opt/genestack/upgrade-tools
   ./scripts/pre-upgrade-validate.sh
   ```

2. **Review validation report**:
   ```bash
   cat validation-report.md
   less validation-report.md
   ```

3. **Verify all checks pass**:
   - Pod status check: PASS
   - API endpoints check: PASS
   - Service health check: PASS
   - Backup validation: PASS
   - Resource availability: PASS

4. **Test failure scenario - Stop a service**:
   ```bash
   # Scale down keystone to simulate failure
   kubectl scale deployment -n openstack keystone-api --replicas=0
   
   # Wait for pods to terminate
   sleep 10
   
   # Run validation again
   ./scripts/pre-upgrade-validate.sh
   ```

5. **Verify validation detects failure**:
   ```bash
   # Should report keystone as unhealthy
   # Should recommend fixing before upgrade
   cat validation-report.md
   ```

6. **Restore service**:
   ```bash
   kubectl scale deployment -n openstack keystone-api --replicas=3
   
   # Wait for pods to be ready
   kubectl wait --for=condition=ready pod -l application=keystone,component=api -n openstack --timeout=300s
   
   # Run validation again
   ./scripts/pre-upgrade-validate.sh
   ```

7. **Verify validation passes again**:
   ```bash
   cat validation-report.md
   ```

**Expected Results**:
- Initial validation passes all checks
- Validation correctly detects stopped service
- Validation passes after service restoration
- Reports are generated correctly

**Completion Criteria**:
- Pre-upgrade validation script works correctly
- Failure detection works as expected
- Reports are accurate and helpful

---

### Phase 3: Upgrade Execution Testing (Subtask 15.3)

Test the complete upgrade process from Caracal to Epoxy.

**Steps**:

1. **Create baseline snapshot**:
   ```bash
   cd /opt/genestack/upgrade-tools
   
   # Document current state
   openstack service list > pre-upgrade-services.txt
   kubectl get pods -n openstack > pre-upgrade-pods.txt
   openstack compute service list > pre-upgrade-compute.txt
   openstack network agent list > pre-upgrade-network.txt
   openstack volume service list > pre-upgrade-volume.txt
   
   # Save chart versions
   cp /opt/genestack/helm-chart-versions.yaml pre-upgrade-chart-versions.yaml
   ```

2. **Run upgrade in dry-run mode**:
   ```bash
   ./openstack-upgrade upgrade --dry-run
   ```

3. **Review planned changes**:
   ```bash
   cat version-update-report.md
   less version-update-report.md
   ```

4. **Verify dry-run output**:
   - All chart version updates listed
   - Configuration changes documented
   - Upgrade order displayed
   - No actual changes applied

5. **Verify no changes were made**:
   ```bash
   # Check chart versions unchanged
   diff /opt/genestack/helm-chart-versions.yaml pre-upgrade-chart-versions.yaml
   
   # Should show no differences
   ```

6. **Run actual upgrade**:
   ```bash
   # Start upgrade
   ./scripts/upgrade-execute.sh 2>&1 | tee upgrade-execution.log
   ```

7. **Monitor upgrade progress** (in another terminal):
   ```bash
   # Watch pods
   kubectl get pods -n openstack -w
   
   # Monitor logs
   tail -f /opt/genestack/upgrade-tools/upgrade.log
   ```

8. **Wait for upgrade completion**:
   - Monitor each service upgrade
   - Note any warnings or errors
   - Verify each service health check passes

9. **Verify upgrade completion**:
   ```bash
   # Check all pods running
   kubectl get pods -n openstack | grep -v Running | grep -v Completed
   
   # Verify chart versions updated
   grep "2025.1" /opt/genestack/helm-chart-versions.yaml
   
   # Check service health
   openstack compute service list
   openstack network agent list
   openstack volume service list
   ```

**Expected Results**:
- Dry-run shows planned changes without applying them
- Actual upgrade completes successfully
- All services upgraded in correct order
- All pods reach Running state
- All services report as healthy
- Upgrade logs show no critical errors

**Completion Criteria**:
- Upgrade executes successfully
- All services upgraded to Epoxy
- No critical errors encountered
- Upgrade report generated

---

### Phase 4: Post-Upgrade Verification Testing (Subtask 15.4)

Verify all OpenStack functionality works correctly after upgrade.

**Steps**:

1. **Run post-upgrade verification**:
   ```bash
   cd /opt/genestack/upgrade-tools
   ./scripts/post-upgrade-verify.sh
   ```

2. **Review verification report**:
   ```bash
   cat verification-report.md
   ```

3. **Test image operations**:
   ```bash
   openstack image list
   
   # Upload test image if needed
   wget http://download.cirros-cloud.net/0.6.2/cirros-0.6.2-x86_64-disk.img
   openstack image create cirros-test \
     --file cirros-0.6.2-x86_64-disk.img \
     --disk-format qcow2 \
     --container-format bare \
     --public
   ```

4. **Test network operations**:
   ```bash
   # Create test network
   openstack network create test-upgrade-net
   openstack subnet create test-upgrade-subnet \
     --network test-upgrade-net \
     --subnet-range 192.168.100.0/24
   
   # Verify creation
   openstack network show test-upgrade-net
   openstack subnet show test-upgrade-subnet
   ```

5. **Test compute operations**:
   ```bash
   # Create test instance
   openstack server create test-upgrade-vm \
     --flavor m1.small \
     --image cirros-test \
     --network test-upgrade-net \
     --wait
   
   # Verify instance is active
   openstack server show test-upgrade-vm
   openstack console log show test-upgrade-vm
   ```

6. **Test volume operations**:
   ```bash
   # Create test volume
   openstack volume create test-upgrade-vol --size 1
   
   # Wait for volume to be available
   openstack volume show test-upgrade-vol
   
   # Attach volume to instance
   openstack server add volume test-upgrade-vm test-upgrade-vol
   
   # Verify attachment
   openstack server show test-upgrade-vm | grep volumes_attached
   ```

7. **Clean up test resources**:
   ```bash
   # Detach and delete volume
   openstack server remove volume test-upgrade-vm test-upgrade-vol
   openstack volume delete test-upgrade-vol
   
   # Delete instance
   openstack server delete test-upgrade-vm
   
   # Delete network resources
   openstack subnet delete test-upgrade-subnet
   openstack network delete test-upgrade-net
   ```

8. **Verify service versions**:
   ```bash
   # Check OpenStack version
   openstack --version
   
   # Check service endpoints
   openstack endpoint list
   
   # Verify all services responding
   for service in identity image compute network volume; do
     echo "Testing $service..."
     openstack ${service} service list 2>/dev/null || echo "$service OK"
   done
   ```

**Expected Results**:
- Post-upgrade verification passes all checks
- Image operations work correctly
- Network creation succeeds
- Instance creation succeeds
- Volume creation and attachment succeeds
- All services report correct versions
- No critical errors in logs

**Completion Criteria**:
- All functional tests pass
- All OpenStack operations work correctly
- Services report Epoxy versions
- Verification report shows success

---

### Phase 5: Rollback Testing (Subtask 15.5)

Test the rollback functionality to ensure system can be restored to Caracal.

**Steps**:

1. **Deploy fresh lab environment**:
   ```bash
   # Clean up existing lab
   cd /opt/genestack
   ./scripts/hyperconverged-lab-kubespray-uninstall.sh
   
   # Wait for cleanup to complete
   sleep 60
   
   # Deploy fresh lab
   source ~/lab-env.sh
   ./scripts/hyperconverged-lab.sh kubespray -x
   
   # Wait for deployment (20-30 minutes)
   ```

2. **Verify fresh deployment**:
   ```bash
   ssh ubuntu@<JUMP_HOST_IP>
   kubectl get nodes
   kubectl get pods -n openstack
   openstack service list
   ```

3. **Create backup before upgrade**:
   ```bash
   cd /opt/genestack/upgrade-tools
   
   # Backup current state
   cp /opt/genestack/helm-chart-versions.yaml backup-chart-versions.yaml
   tar -czf backup-configs.tar.gz /opt/genestack/base-helm-configs/
   
   # Document pre-rollback state
   openstack service list > pre-rollback-services.txt
   kubectl get pods -n openstack > pre-rollback-pods.txt
   ```

4. **Start upgrade and simulate failure**:
   ```bash
   # Option 1: Let upgrade complete then test rollback
   ./scripts/upgrade-execute.sh
   
   # Option 2: Interrupt upgrade mid-process (Ctrl+C after a few services)
   # This tests rollback from partial upgrade state
   ```

5. **Initiate rollback**:
   ```bash
   ./scripts/rollback.sh 2>&1 | tee rollback-execution.log
   ```

6. **Monitor rollback progress**:
   ```bash
   # In another terminal
   kubectl get pods -n openstack -w
   
   # Monitor rollback logs
   tail -f rollback.log
   ```

7. **Verify rollback completion**:
   ```bash
   # Check chart versions restored
   diff /opt/genestack/helm-chart-versions.yaml backup-chart-versions.yaml
   
   # Should show no differences
   
   # Check all pods running
   kubectl get pods -n openstack | grep -v Running | grep -v Completed
   
   # Verify services back to Caracal
   grep "2024.1\|2024.2" /opt/genestack/helm-chart-versions.yaml
   ```

8. **Test service functionality after rollback**:
   ```bash
   # Check service health
   openstack compute service list
   openstack network agent list
   openstack volume service list
   
   # Test basic operations
   openstack image list
   openstack network list
   openstack server list
   ```

9. **Review rollback report**:
   ```bash
   cat rollback-report.md
   ```

**Expected Results**:
- Rollback executes successfully
- Chart versions restored to Caracal
- All services return to healthy state
- All pods reach Running state
- API endpoints accessible
- Basic operations work correctly
- Rollback report generated

**Completion Criteria**:
- Rollback functionality works correctly
- System restored to Caracal state
- All services operational after rollback
- Rollback report is accurate

---

## Test Results Documentation

Document all test results in a structured format:

### Test Execution Summary

```
Test Date: YYYY-MM-DD
Tester: [Name]
Lab Environment: [Details]
OpenStack Cloud: [Cloud name]

Phase 1: Lab Deployment
- Status: [PASS/FAIL]
- Duration: [Minutes]
- Issues: [None/List issues]

Phase 2: Pre-Upgrade Validation
- Status: [PASS/FAIL]
- All checks passed: [YES/NO]
- Failure detection works: [YES/NO]
- Issues: [None/List issues]

Phase 3: Upgrade Execution
- Status: [PASS/FAIL]
- Duration: [Minutes]
- Services upgraded: [Count]
- Issues: [None/List issues]

Phase 4: Post-Upgrade Verification
- Status: [PASS/FAIL]
- All tests passed: [YES/NO]
- Issues: [None/List issues]

Phase 5: Rollback Testing
- Status: [PASS/FAIL]
- Rollback successful: [YES/NO]
- Issues: [None/List issues]

Overall Result: [PASS/FAIL]
```

### Issues Encountered

Document any issues found during testing:

```
Issue #1:
- Phase: [Which phase]
- Description: [What happened]
- Severity: [Critical/High/Medium/Low]
- Workaround: [If any]
- Resolution: [How it was fixed]
- Status: [Open/Resolved]

Issue #2:
...
```

### Performance Metrics

Document performance before and after upgrade:

```
API Response Times:
- Pre-upgrade: [ms]
- Post-upgrade: [ms]
- Change: [+/- %]

Resource Utilization:
- CPU: [Pre] -> [Post]
- Memory: [Pre] -> [Post]
- Storage: [Pre] -> [Post]

Service Startup Times:
- Average: [seconds]
- Slowest service: [name] - [seconds]
```

### Lessons Learned

Document insights from testing:

```
What Went Well:
- [Item 1]
- [Item 2]

What Could Be Improved:
- [Item 1]
- [Item 2]

Recommendations for Production:
- [Recommendation 1]
- [Recommendation 2]
```

---

## Troubleshooting

### Common Issues

**Issue**: Lab deployment fails

**Solution**:
```bash
# Check OpenStack quota
openstack quota show

# Verify cloud configuration
openstack --os-cloud ${OS_CLOUD} server list

# Check for existing resources
openstack server list | grep ${LAB_NAME_PREFIX}
```

**Issue**: Upgrade hangs on a service

**Solution**:
```bash
# Check pod status
kubectl describe pod -n openstack <pod-name>

# Check pod logs
kubectl logs -n openstack <pod-name>

# Check for resource constraints
kubectl top nodes
kubectl top pods -n openstack
```

**Issue**: Rollback fails

**Solution**:
```bash
# Check backup files exist
ls -la backup-*

# Manually restore chart versions
cp backup-chart-versions.yaml /opt/genestack/helm-chart-versions.yaml

# Manually rollback services
helm rollback -n openstack <service-name>
```

---

## Next Steps

After successful integration testing:

1. **Review all test results**: Ensure all phases passed
2. **Document issues**: Create tickets for any problems
3. **Update procedures**: Incorporate lessons learned
4. **Plan production upgrade**: Schedule maintenance window
5. **Prepare rollback plan**: Document rollback procedures
6. **Communicate results**: Share with stakeholders

---

## Additional Resources

- [Lab Environment Setup Guide](LAB_ENVIRONMENT_SETUP.md)
- [Upgrade Tools README](../README.md)
- [Pre-Upgrade Validation Guide](VALIDATION.md)
- [Genestack Documentation](https://docs.rackspacecloud.com/)

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-04  
**Applies To**: OpenStack Caracal to Epoxy Upgrade Integration Testing
