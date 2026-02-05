# OpenStack Caracal to Epoxy Upgrade Runbook

## Document Information

**Purpose:** Step-by-step operational guide for upgrading Genestack OpenStack from Caracal (2024.1/2024.2) to Epoxy (2025.1)

**Audience:** Platform operators and SREs performing the upgrade

**Last Updated:** 2025-01-XX

**Estimated Duration:** 1-4 hours depending on deployment size

## Pre-Flight Checklist

Complete ALL items before starting upgrade. Check off each item as completed.

### T-7 Days: Planning Phase

- [ ] Review complete upgrade documentation
- [ ] Review breaking changes and assess impact
- [ ] Schedule maintenance window (recommend 2x expected duration)
- [ ] Notify stakeholders and users of planned downtime
- [ ] Prepare communication plan and status page
- [ ] Review rollback procedures with team
- [ ] Identify emergency contacts and escalation path
- [ ] Reserve backup resources (additional nodes if needed)

### T-24 Hours: Preparation Phase

- [ ] Verify all team members are available during maintenance window
- [ ] Confirm backup systems are operational
- [ ] Test communication channels (chat, phone, status page)
- [ ] Review incident response procedures
- [ ] Prepare monitoring dashboards
- [ ] Set up screen sharing for team coordination

### T-2 Hours: Pre-Upgrade Validation

- [ ] **System Health Check**
  ```bash
  # All pods running
  kubectl get pods -n openstack | grep -v Running | grep -v Completed
  # Should return no results
  
  # All services up
  openstack compute service list --format value -c State | grep -v up
  openstack network agent list --format value -c Alive | grep -v ':-)' 
  openstack volume service list --format value -c State | grep -v up
  # Should return no results
  ```

- [ ] **API Endpoint Check**
  ```bash
  openstack endpoint list
  # All endpoints should respond
  
  curl -k https://keystone.example.com:5000/v3
  # Should return 200 OK
  ```

- [ ] **Resource Validation**
  ```bash
  # Check cluster resources
  kubectl top nodes
  # Ensure CPU < 80%, Memory < 80%
  
  # Check disk space
  df -h | grep -E '(/$|/var)'
  # Ensure > 20% free space
  ```

- [ ] **Backup Verification**
  ```bash
  # Verify database backups exist and are recent
  ls -lh /var/backups/openstack/databases/
  # Should show backups within last 24 hours
  
  # Test backup restoration (on test system)
  # Document backup location: ___________________
  ```

- [ ] **Active Workload Check**
  ```bash
  # No active migrations
  openstack server migration list --status running
  # Should return empty
  
  # No pending jobs
  kubectl get jobs -n openstack | grep -v Completed
  # Should return no results
  ```

- [ ] **Configuration Backup**
  ```bash
  # Backup helm chart versions
  cp helm-chart-versions.yaml helm-chart-versions.yaml.backup.$(date +%Y%m%d)
  
  # Backup override configurations
  tar -czf base-helm-configs-backup-$(date +%Y%m%d).tar.gz base-helm-configs/
  
  # Verify backups created
  ls -lh *backup*
  ```

### T-0: Ready to Start

- [ ] All pre-flight checks completed
- [ ] Team assembled and ready
- [ ] Communication channels active
- [ ] Monitoring dashboards open
- [ ] Rollback plan reviewed and ready
- [ ] **GO/NO-GO Decision:** _____ (Initial: _____)

## Upgrade Execution

### Phase 1: Pre-Upgrade Validation (10 minutes)

**Checkpoint 1.1: Run Automated Validation**

```bash
cd /opt/genestack/upgrade-tools
source venv/bin/activate
./openstack-upgrade --validate-only
```

**Expected Result:** All validation checks pass

**If validation fails:**
- [ ] Review validation report
- [ ] Fix all critical issues
- [ ] Re-run validation
- [ ] **Decision Point:** Continue or abort? _____

**Validation Checkpoint:**
- [ ] All pods Running
- [ ] All API endpoints responding
- [ ] Backups verified
- [ ] Resources sufficient
- [ ] No active migrations

**Time Completed:** _____ **Duration:** _____ **Status:** ☐ Pass ☐ Fail

---

### Phase 2: Dry-Run Test (10 minutes)

**Checkpoint 2.1: Execute Dry-Run**

```bash
./openstack-upgrade --dry-run > dry-run-report.txt
```

**Expected Result:** Dry-run completes without errors

**Review dry-run output:**
- [ ] Chart version updates look correct
- [ ] Service upgrade order is appropriate
- [ ] No unexpected changes
- [ ] Estimated duration is acceptable

**If dry-run shows issues:**
- [ ] Review and fix configuration issues
- [ ] Re-run dry-run
- [ ] **Decision Point:** Continue or abort? _____

**Dry-Run Checkpoint:**
- [ ] Version updates validated
- [ ] Configuration changes reviewed
- [ ] Service order confirmed
- [ ] Team agrees to proceed

**Time Completed:** _____ **Duration:** _____ **Status:** ☐ Pass ☐ Fail

---

### Phase 3: Create Backup (15 minutes)

**Checkpoint 3.1: Automated Backup**

Backup is created automatically by upgrade tool, but verify:

```bash
# Check backup location
ls -lh /var/backups/openstack/

# Verify backup contents
tar -tzf /var/backups/openstack/backup-*.tar.gz | head -20
```

**Expected Result:** Backup created successfully

**Manual backup verification:**
- [ ] helm-chart-versions.yaml backed up
- [ ] base-helm-configs/ backed up
- [ ] Database backups exist
- [ ] Backup size is reasonable (> 100MB)
- [ ] Backup location documented: _____________________

**If backup fails:**
- [ ] Check disk space
- [ ] Check permissions
- [ ] Create manual backup
- [ ] **Decision Point:** Continue or abort? _____

**Backup Checkpoint:**
- [ ] All files backed up
- [ ] Backup integrity verified
- [ ] Backup location documented
- [ ] Rollback plan ready

**Time Completed:** _____ **Duration:** _____ **Status:** ☐ Pass ☐ Fail

---

### Phase 4: Upgrade Execution (30-120 minutes)

**Checkpoint 4.1: Start Upgrade**

```bash
# Start upgrade with full logging
./openstack-upgrade 2>&1 | tee upgrade-execution.log
```

**Expected Result:** Upgrade progresses through all services

**Monitor progress:**
- [ ] Watch pod status in separate terminal:
  ```bash
  watch -n 5 'kubectl get pods -n openstack | grep -v Running | grep -v Completed'
  ```

- [ ] Monitor upgrade logs:
  ```bash
  tail -f upgrade-tools/upgrade.log
  ```

**Service-by-Service Validation:**

For each service upgraded, verify:

**Infrastructure Services:**
- [ ] memcached: Pods Running, no errors
- [ ] mariadb-operator: Pods Running, databases accessible
- [ ] rabbitmq: Pods Running, connections working

**Core Services:**
- [ ] keystone: Pods Running, API responding, `openstack token issue` works
- [ ] glance: Pods Running, API responding, `openstack image list` works
- [ ] placement: Pods Running, API responding
- [ ] cinder: Pods Running, API responding, `openstack volume service list` shows all up
- [ ] neutron: Pods Running, API responding, `openstack network agent list` shows all alive
- [ ] nova: Pods Running, API responding, `openstack compute service list` shows all up
- [ ] horizon: Pods Running, web UI accessible

**Optional Services (if deployed):**
- [ ] octavia: Pods Running, API responding
- [ ] heat: Pods Running, API responding
- [ ] magnum: Pods Running, API responding
- [ ] Other: _______________

**If service upgrade fails:**
1. [ ] Note which service failed: _____________________
2. [ ] Review error logs:
   ```bash
   kubectl logs -n openstack <failed-pod> --tail=100
   ```
3. [ ] Check pod events:
   ```bash
   kubectl describe pod -n openstack <failed-pod>
   ```
4. [ ] **Decision Point:** 
   - [ ] Retry upgrade for this service
   - [ ] Skip service and continue (if optional)
   - [ ] Initiate rollback
   - [ ] Escalate to senior engineer

**Upgrade Checkpoint:**
- [ ] All infrastructure services upgraded
- [ ] All core services upgraded
- [ ] All optional services upgraded (or skipped)
- [ ] No critical errors in logs
- [ ] All pods in Running state

**Time Completed:** _____ **Duration:** _____ **Status:** ☐ Pass ☐ Fail

---

### Phase 5: Post-Upgrade Verification (20 minutes)

**Checkpoint 5.1: Pod Status Check**

```bash
# All pods should be Running or Completed
kubectl get pods -n openstack

# No pods in Error, CrashLoopBackOff, or Pending
kubectl get pods -n openstack | grep -E '(Error|CrashLoop|Pending)'
# Should return no results
```

**Expected Result:** All pods healthy

- [ ] All pods in Running or Completed state
- [ ] No pods in error states
- [ ] All containers ready

**Checkpoint 5.2: API Endpoint Verification**

```bash
# All endpoints accessible
openstack endpoint list

# Test each service API
openstack token issue          # Keystone
openstack image list           # Glance
openstack server list          # Nova
openstack network list         # Neutron
openstack volume list          # Cinder
openstack loadbalancer list    # Octavia (if deployed)
```

**Expected Result:** All APIs responding

- [ ] Keystone API responding
- [ ] Glance API responding
- [ ] Nova API responding
- [ ] Neutron API responding
- [ ] Cinder API responding
- [ ] Other APIs responding: _____

**Checkpoint 5.3: Service List Verification**

```bash
# All compute services up
openstack compute service list
# All should show State=up

# All network agents alive
openstack network agent list
# All should show Alive=:-)

# All volume services enabled
openstack volume service list
# All should show State=up, Status=enabled
```

**Expected Result:** All services operational

- [ ] All compute services up
- [ ] All network agents alive
- [ ] All volume services enabled
- [ ] No services in down state

**Checkpoint 5.4: Functional Testing**

```bash
# Create test instance
openstack server create \
  --flavor m1.small \
  --image cirros \
  --network private \
  --key-name test-key \
  test-upgrade-instance

# Wait for instance to be ACTIVE
openstack server show test-upgrade-instance -f value -c status
# Should show ACTIVE

# Create test network
openstack network create test-upgrade-network

# Create test volume
openstack volume create --size 1 test-upgrade-volume

# Wait for volume to be available
openstack volume show test-upgrade-volume -f value -c status
# Should show available

# Attach volume to instance
openstack server add volume test-upgrade-instance test-upgrade-volume

# Verify attachment
openstack server show test-upgrade-instance -f json | jq '.volumes_attached'

# Clean up test resources
openstack server remove volume test-upgrade-instance test-upgrade-volume
openstack server delete test-upgrade-instance
openstack volume delete test-upgrade-volume
openstack network delete test-upgrade-network
```

**Expected Result:** All operations succeed

- [ ] Instance creation successful
- [ ] Network creation successful
- [ ] Volume creation successful
- [ ] Volume attachment successful
- [ ] Resource deletion successful

**Checkpoint 5.5: Log Analysis**

```bash
# Check for critical errors in recent logs
for service in keystone glance nova neutron cinder; do
  echo "=== Checking $service logs ==="
  kubectl logs -n openstack -l application=$service --tail=100 | grep -i error
done
```

**Expected Result:** No critical errors

- [ ] No authentication failures
- [ ] No database connection errors
- [ ] No RabbitMQ connection errors
- [ ] No critical service errors
- [ ] Only expected warnings (if any)

**Post-Upgrade Checkpoint:**
- [ ] All pods healthy
- [ ] All APIs responding
- [ ] All services operational
- [ ] Functional tests passed
- [ ] No critical errors in logs

**Time Completed:** _____ **Duration:** _____ **Status:** ☐ Pass ☐ Fail

---

### Phase 6: Final Verification (10 minutes)

**Checkpoint 6.1: Generate Upgrade Report**

```bash
# Review upgrade report
cat upgrade-report.txt

# Or if not generated, create summary
./openstack-upgrade --validate-only > post-upgrade-validation.txt
```

**Review report for:**
- [ ] All services upgraded successfully
- [ ] Total upgrade duration: _____ minutes
- [ ] Any warnings or issues: _____________________
- [ ] All validation checks passed

**Checkpoint 6.2: Performance Baseline**

```bash
# Test API response times
time openstack server list
time openstack network list
time openstack volume list

# Check resource utilization
kubectl top nodes
kubectl top pods -n openstack
```

**Expected Result:** Performance within normal range

- [ ] API response times < 5 seconds
- [ ] Node CPU < 80%
- [ ] Node memory < 80%
- [ ] No resource exhaustion

**Checkpoint 6.3: User Acceptance**

- [ ] Test user login to Horizon dashboard
- [ ] Verify user can list their resources
- [ ] Verify user can create test instance (if applicable)
- [ ] No user-facing errors or issues

**Final Checkpoint:**
- [ ] Upgrade report reviewed
- [ ] Performance acceptable
- [ ] User acceptance verified
- [ ] Ready to declare success

**Time Completed:** _____ **Duration:** _____ **Status:** ☐ Pass ☐ Fail

---

## Upgrade Complete

### Success Criteria

All of the following must be true:

- [ ] All pre-flight checks completed
- [ ] All upgrade phases completed successfully
- [ ] All pods in healthy state
- [ ] All APIs responding correctly
- [ ] All services operational
- [ ] Functional tests passed
- [ ] No critical errors in logs
- [ ] Performance within acceptable range
- [ ] User acceptance verified

**Total Upgrade Duration:** _____ hours _____ minutes

**Upgrade Status:** ☐ SUCCESS ☐ PARTIAL SUCCESS ☐ FAILED

**Sign-off:**
- Operator: _____________________ Date/Time: _____
- Reviewer: _____________________ Date/Time: _____

---

## Rollback Procedures

### When to Rollback

Initiate rollback if:

- [ ] Multiple core services failed to upgrade
- [ ] Keystone, Nova, or Neutron non-functional
- [ ] Data corruption detected
- [ ] Severe performance degradation (> 50% slower)
- [ ] Security vulnerabilities introduced
- [ ] Unable to fix issues within maintenance window

**DO NOT rollback if:**
- Only optional services failed (can be fixed independently)
- Minor configuration issues (can be fixed in place)
- Cosmetic issues only
- Non-critical warnings

### Rollback Decision

**Decision Point:** Rollback required? ☐ YES ☐ NO

**Reason for rollback:** _____________________________________

**Approved by:** _____________________ Time: _____

### Automated Rollback Procedure

**Step 1: Initiate Rollback**

```bash
cd /opt/genestack/upgrade-tools
source venv/bin/activate

# Start rollback
./openstack-upgrade --rollback
```

**Expected Result:** Rollback completes successfully

**Monitor rollback:**
- [ ] Watch pod status
- [ ] Monitor rollback logs
- [ ] Verify services being restored

**Step 2: Verify Rollback**

```bash
# Check pod status
kubectl get pods -n openstack

# Verify services
openstack compute service list
openstack network agent list
openstack volume service list

# Test API endpoints
openstack token issue
openstack server list
```

**Expected Result:** All services restored to Caracal

- [ ] All pods Running
- [ ] All services operational
- [ ] APIs responding
- [ ] Version shows Caracal (2024.1 or 2024.2)

**Rollback Checkpoint:**
- [ ] Rollback completed
- [ ] Services verified
- [ ] System operational
- [ ] Users notified

**Rollback Duration:** _____ minutes **Status:** ☐ Success ☐ Failed

### Manual Rollback Procedure

If automated rollback fails:

**Step 1: Restore Configuration Files**

```bash
# Restore helm chart versions
cp helm-chart-versions.yaml.backup.$(date +%Y%m%d) helm-chart-versions.yaml

# Restore override configurations
tar -xzf base-helm-configs-backup-$(date +%Y%m%d).tar.gz
```

**Step 2: Rollback Services**

```bash
# Rollback in reverse order
helm rollback horizon -n openstack
helm rollback nova -n openstack
helm rollback neutron -n openstack
helm rollback cinder -n openstack
helm rollback placement -n openstack
helm rollback glance -n openstack
helm rollback keystone -n openstack
```

**Step 3: Restore Databases (if needed)**

```bash
# Only if database schema changes occurred
kubectl exec -n openstack mariadb-server-0 -- \
  mysql < /var/backups/openstack/databases/backup-$(date +%Y%m%d).sql
```

**Step 4: Verify Rollback**

```bash
# Check all services
kubectl get pods -n openstack
openstack compute service list
openstack network agent list
openstack volume service list
```

**Manual Rollback Checkpoint:**
- [ ] Configurations restored
- [ ] Services rolled back
- [ ] Databases restored (if needed)
- [ ] System verified operational

---

## Post-Upgrade Tasks

### Immediate (Within 1 hour)

- [ ] **User Communication**
  - [ ] Notify users that upgrade is complete
  - [ ] Update status page
  - [ ] Send completion email with any known issues

- [ ] **Documentation**
  - [ ] Complete this runbook with actual times and issues
  - [ ] Document any deviations from plan
  - [ ] Note any issues encountered and resolutions
  - [ ] Save all logs and reports

- [ ] **Monitoring**
  - [ ] Set up enhanced monitoring for 24 hours
  - [ ] Configure alerts for anomalies
  - [ ] Monitor error rates and performance

### Short-term (Within 24 hours)

- [ ] **Performance Review**
  - [ ] Compare API response times to baseline
  - [ ] Review resource utilization trends
  - [ ] Check for any performance degradation
  - [ ] Investigate any anomalies

- [ ] **Log Review**
  - [ ] Review all service logs for errors
  - [ ] Check for authentication issues
  - [ ] Verify no database connection problems
  - [ ] Document any recurring warnings

- [ ] **User Feedback**
  - [ ] Collect user feedback on any issues
  - [ ] Address any user-reported problems
  - [ ] Update documentation based on feedback

### Medium-term (Within 1 week)

- [ ] **Post-Mortem**
  - [ ] Conduct team post-mortem meeting
  - [ ] Document lessons learned
  - [ ] Identify process improvements
  - [ ] Update runbook based on experience

- [ ] **Cleanup**
  - [ ] Remove old helm releases (after verification period)
  - [ ] Clean up temporary resources
  - [ ] Archive logs and reports
  - [ ] Keep backups for 30 days, then remove

- [ ] **Security Review**
  - [ ] Review Epoxy security advisories
  - [ ] Update security policies if needed
  - [ ] Rotate credentials if required
  - [ ] Perform security scan

---

## Emergency Contacts

### Primary Team

| Role | Name | Phone | Email |
|------|------|-------|-------|
| Lead Operator | __________ | __________ | __________ |
| Backup Operator | __________ | __________ | __________ |
| Platform Engineer | __________ | __________ | __________ |
| Database Admin | __________ | __________ | __________ |

### Escalation Path

| Level | Contact | Phone | Email | When to Escalate |
|-------|---------|-------|-------|------------------|
| L1 | __________ | __________ | __________ | Initial issues |
| L2 | __________ | __________ | __________ | After 30 min |
| L3 | __________ | __________ | __________ | Critical issues |
| Management | __________ | __________ | __________ | Major incident |

### External Support

| Vendor | Contact | Phone | Email | Support Level |
|--------|---------|-------|-------|---------------|
| Genestack | __________ | __________ | __________ | __________ |
| Rackspace | __________ | __________ | __________ | __________ |
| Other | __________ | __________ | __________ | __________ |

---

## Notes and Issues

### Issues Encountered

| Time | Issue | Resolution | Duration |
|------|-------|------------|----------|
| _____ | _____ | _____ | _____ |
| _____ | _____ | _____ | _____ |
| _____ | _____ | _____ | _____ |

### Deviations from Plan

| Step | Planned | Actual | Reason |
|------|---------|--------|--------|
| _____ | _____ | _____ | _____ |
| _____ | _____ | _____ | _____ |

### Lessons Learned

1. _____________________________________________________
2. _____________________________________________________
3. _____________________________________________________

### Recommendations for Next Time

1. _____________________________________________________
2. _____________________________________________________
3. _____________________________________________________

---

## Appendix: Quick Reference Commands

### Health Checks

```bash
# Pod status
kubectl get pods -n openstack

# Service status
openstack compute service list
openstack network agent list
openstack volume service list

# API endpoints
openstack endpoint list

# Resource utilization
kubectl top nodes
kubectl top pods -n openstack
```

### Troubleshooting

```bash
# View pod logs
kubectl logs -n openstack <pod-name> --tail=100

# Describe pod
kubectl describe pod -n openstack <pod-name>

# Check events
kubectl get events -n openstack --sort-by='.lastTimestamp'

# Restart pod
kubectl delete pod -n openstack <pod-name>

# Check helm releases
helm list -n openstack

# Rollback helm release
helm rollback <release> -n openstack
```

### Database Operations

```bash
# Connect to database
kubectl exec -it -n openstack mariadb-server-0 -- mysql

# Check database status
kubectl exec -n openstack mariadb-server-0 -- mysql -e "SHOW DATABASES;"

# Run db-sync manually
kubectl exec -n openstack keystone-api-xxx -- keystone-manage db_sync
```

---

**End of Runbook**
