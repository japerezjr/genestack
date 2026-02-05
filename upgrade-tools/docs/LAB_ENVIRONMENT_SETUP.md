# Lab Environment Setup Guide

This guide provides comprehensive instructions for setting up a lab environment to test the OpenStack Caracal to Epoxy upgrade process. The lab environment uses the Genestack hyperconverged deployment scripts to create a test OpenStack cluster on existing OpenStack infrastructure.

## Quick Start

If you want to jump straight to testing the upgrade in a lab, follow these steps:

### 1. Set Up Your Local Environment

First, prepare your local machine with the necessary tools:

```bash
# Navigate to the upgrade-tools directory
cd /path/to/genestack/upgrade-tools

# Create a Python virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required Python packages
pip install -r requirements.txt

# Install the upgrade tools package in development mode
pip install -e .
```

### 2. Deploy a Lab Environment

Deploy a fresh OpenStack Caracal environment using the hyperconverged lab scripts:

```bash
# Navigate to the Genestack root directory
cd /path/to/genestack

# Set required environment variables
export ACME_EMAIL="your-email@example.com"
export GATEWAY_DOMAIN="lab.example.com"
export OS_CLOUD="your-openstack-cloud"
export OS_FLAVOR="m1.xlarge"  # Or appropriate flavor for your cloud
export HYPERCONVERGED_DEV="true"  # Use your local genestack checkout

# Deploy the lab (this will take 30-45 minutes)
./scripts/hyperconverged-lab.sh kubespray
```

See [Lab Deployment Process](#lab-deployment-process) for detailed deployment instructions.

### 3. Run Upgrade Tests

Once your lab is deployed, you can test the upgrade process:

```bash
# SSH into your lab jump host (IP provided at end of deployment)
ssh ubuntu@<JUMP_HOST_IP>

# On the jump host, navigate to the upgrade tools
cd /opt/genestack/upgrade-tools

# Install python3-venv if not already installed
sudo apt-get update
sudo apt-get install -y python3-venv python3-full

# Remove any existing venv and create a fresh one
rm -rf venv
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Verify you're in the venv (should show path with /venv/bin/)
which python3
which pip

# Upgrade pip in the venv
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Install the upgrade tools package in development mode
pip install -e .

# Run pre-upgrade validation
./scripts/pre-upgrade-validate.sh

# Run the upgrade (dry-run first)
python3 -m cli upgrade --dry-run

# Run the actual upgrade
python3 -m cli upgrade
```

See [Lab Testing Guide](#lab-testing-guide) for comprehensive testing scenarios.

## Table of Contents

1. [Environment Variable Requirements](#environment-variable-requirements)
2. [Lab Deployment Process](#lab-deployment-process)
3. [Lab Testing Guide](#lab-testing-guide)

---

## Environment Variable Requirements

The hyperconverged lab deployment scripts use several environment variables to configure the deployment. This section documents all required and optional variables.

### Required Environment Variables

These variables must be set before running the lab deployment:

#### `ACME_EMAIL`
- **Description**: Email address for ACME/Let's Encrypt certificate registration
- **Required**: Yes (for production-like deployments)
- **Default**: `example@aol.com` (if not set, will prompt)
- **Example**: `export ACME_EMAIL="admin@example.com"`
- **Notes**: Used for SSL certificate generation. Use a valid email for production-like testing.

#### `GATEWAY_DOMAIN`
- **Description**: Domain name for the gateway and ingress
- **Required**: Yes
- **Default**: `cluster.local` (if not set, will prompt)
- **Example**: `export GATEWAY_DOMAIN="lab.example.com"`
- **Notes**: This domain will be used for all OpenStack API endpoints.

#### `OS_CLOUD`
- **Description**: OpenStack cloud configuration name from clouds.yaml
- **Required**: Yes
- **Default**: `default` (if not set, will prompt)
- **Example**: `export OS_CLOUD="my-openstack-cloud"`
- **Notes**: Must match a cloud configuration in your `~/.config/openstack/clouds.yaml` file.

#### `OS_FLAVOR`
- **Description**: OpenStack flavor to use for lab instances
- **Required**: Yes (will prompt if not set)
- **Default**: None (script will suggest based on available flavors)
- **Example**: `export OS_FLAVOR="m1.xlarge"`
- **Notes**: Recommended minimum: 8 vCPUs, 16GB RAM, 100GB disk for hyperconverged nodes.

### Optional Environment Variables

These variables have sensible defaults but can be customized:

#### `LAB_NAME_PREFIX`
- **Description**: Prefix for all created OpenStack resources (instances, networks, etc.)
- **Required**: No
- **Default**: 
  - `hyperconverged` (for Kubespray deployments)
  - `talos-hyperconverged` (for Talos deployments)
- **Example**: `export LAB_NAME_PREFIX="upgrade-test"`
- **Notes**: Useful for running multiple lab environments or identifying resources.

#### `LAB_NETWORK_MTU`
- **Description**: MTU (Maximum Transmission Unit) for lab networks
- **Required**: No
- **Default**: `1500`
- **Example**: `export LAB_NETWORK_MTU="1450"`
- **Notes**: Adjust if your underlying network requires a different MTU (e.g., for VXLAN overhead).

#### `OS_IMAGE`
- **Description**: OpenStack image to use for instances
- **Required**: No
- **Default**: `Ubuntu 24.04` (for Kubespray)
- **Example**: `export OS_IMAGE="Ubuntu 22.04"`
- **Notes**: For Kubespray deployments only. Talos uses its own image.

#### `HYPERCONVERGED_DEV`
- **Description**: Enable development mode to sync local Genestack checkout to lab
- **Required**: No
- **Default**: `false`
- **Example**: `export HYPERCONVERGED_DEV="true"`
- **Notes**: When enabled, your local `/opt/genestack` directory is synced to the lab for testing local changes.

#### `HYPERCONVERGED_CINDER_VOLUME`
- **Description**: Enable iSCSI Cinder volume support in the lab
- **Required**: No
- **Default**: `false`
- **Example**: `export HYPERCONVERGED_CINDER_VOLUME="true"`
- **Notes**: Enables block storage testing. Requires additional configuration and resources.

#### `TEST_LEVEL`
- **Description**: Level of testing to perform during deployment
- **Required**: No
- **Default**: `off`
- **Example**: `export TEST_LEVEL="basic"`
- **Notes**: Controls automated testing during deployment. Options: `off`, `basic`, `full`.

### Talos-Specific Environment Variables

These variables are only used when deploying with Talos Linux:

#### `TALOS_VERSION`
- **Description**: Version of Talos Linux to deploy
- **Required**: No
- **Default**: `v1.11.5`
- **Example**: `export TALOS_VERSION="v1.11.5"`
- **Notes**: Must be a valid Talos release version.

#### `TALOS_ARCH`
- **Description**: CPU architecture for Talos
- **Required**: No
- **Default**: `amd64`
- **Example**: `export TALOS_ARCH="arm64"`
- **Notes**: Options: `amd64`, `arm64`.

#### `TALOS_SCHEMATIC_ID`
- **Description**: Talos Factory schematic ID with required extensions
- **Required**: No
- **Default**: `88d1f7a5c4f1d3aba7df787c448c1d3d008ed29cfb34af53fa0df4336a56040b`
- **Example**: `export TALOS_SCHEMATIC_ID="<your-schematic-id>"`
- **Notes**: Default includes iscsi-tools, util-linux-tools, and qemu-guest-agent extensions for Longhorn.

#### `TALOS_IMAGE_NAME`
- **Description**: Name for the Talos image in Glance
- **Required**: No
- **Default**: `talos-${TALOS_VERSION}-genestack`
- **Example**: `export TALOS_IMAGE_NAME="talos-custom"`
- **Notes**: Used to identify the Talos image in OpenStack.

#### `TALOS_CLUSTER_NAME`
- **Description**: Name for the Talos Kubernetes cluster
- **Required**: No
- **Default**: `genestack-talos`
- **Example**: `export TALOS_CLUSTER_NAME="upgrade-test-cluster"`
- **Notes**: Used in Talos configuration and kubeconfig.

#### `JUMP_HOST_IMAGE`
- **Description**: Image to use for the jump host (Talos deployments only)
- **Required**: No
- **Default**: `Ubuntu 24.04`
- **Example**: `export JUMP_HOST_IMAGE="Ubuntu 22.04"`
- **Notes**: Jump host provides SSH access and management tools for Talos clusters.

### Environment File Template

Create a file (e.g., `lab-env.sh`) with your environment variables:

```bash
#!/bin/bash
# Lab Environment Configuration

# Required Variables
export ACME_EMAIL="admin@example.com"
export GATEWAY_DOMAIN="lab.example.com"
export OS_CLOUD="my-openstack-cloud"
export OS_FLAVOR="m1.xlarge"

# Optional Variables
export LAB_NAME_PREFIX="caracal-to-epoxy-test"
export LAB_NETWORK_MTU="1500"
export HYPERCONVERGED_DEV="false"
export HYPERCONVERGED_CINDER_VOLUME="false"
export TEST_LEVEL="off"

# Talos-Specific (if using Talos deployment)
# export TALOS_VERSION="v1.11.5"
# export TALOS_ARCH="amd64"
# export TALOS_CLUSTER_NAME="upgrade-test-cluster"

echo "Lab environment variables loaded"
```

Source this file before running the deployment:

```bash
source lab-env.sh
```

### Verifying Environment Variables

Before starting the deployment, verify your environment variables are set:

```bash
# Check required variables
echo "ACME_EMAIL: ${ACME_EMAIL}"
echo "GATEWAY_DOMAIN: ${GATEWAY_DOMAIN}"
echo "OS_CLOUD: ${OS_CLOUD}"
echo "OS_FLAVOR: ${OS_FLAVOR}"

# Check optional variables
echo "LAB_NAME_PREFIX: ${LAB_NAME_PREFIX:-<not set, will use default>}"
echo "LAB_NETWORK_MTU: ${LAB_NETWORK_MTU:-<not set, will use default>}"
```

---

## Lab Deployment Process

This section provides step-by-step instructions for deploying a lab environment to test the OpenStack upgrade.

### Prerequisites

Before deploying the lab, ensure you have:

1. **OpenStack Access**: Access to an existing OpenStack cloud with sufficient quota
2. **OpenStack CLI**: OpenStack client tools installed and configured
3. **clouds.yaml**: Properly configured OpenStack credentials in `~/.config/openstack/clouds.yaml`
4. **Genestack Repository**: Clone of the Genestack repository at `/opt/genestack`
5. **Sufficient Quota**: Minimum requirements:
   - 3 instances (for minimal deployment)
   - 24 vCPUs (8 per instance)
   - 48GB RAM (16GB per instance)
   - 300GB storage (100GB per instance)
   - 2 floating IPs
   - 1 network, 2 subnets, 1 router

### Deployment Platforms

Genestack supports two deployment platforms for lab environments:

#### 1. Kubespray (Traditional)
- Uses Ubuntu VMs with SSH access
- Kubernetes deployed via Kubespray/Ansible
- Requires SSH keypair for node access
- More familiar for traditional operators
- **Recommended for**: Testing upgrades, traditional workflows

#### 2. Talos Linux (Modern)
- Uses Talos Linux immutable OS
- Kubernetes deployed via talosctl
- No SSH - managed via Talos API
- Includes Talos-specific configs for Longhorn, Kube-OVN, Ceph
- **Recommended for**: Modern deployments, production-like testing

### Deployment Steps

#### Step 1: Prepare Environment

1. **Navigate to Genestack directory**:
   ```bash
   cd /opt/genestack
   ```

2. **Create and source environment file**:
   ```bash
   # Create environment file (see template above)
   vi lab-env.sh
   
   # Source the file
   source lab-env.sh
   ```

3. **Verify OpenStack connectivity**:
   ```bash
   openstack --os-cloud ${OS_CLOUD} server list
   openstack --os-cloud ${OS_CLOUD} flavor list
   openstack --os-cloud ${OS_CLOUD} image list
   ```

#### Step 2: Choose Deployment Platform

Run the hyperconverged lab script. You can either:

**Option A: Interactive Mode** (will prompt for platform choice):
```bash
./scripts/hyperconverged-lab.sh
```

**Option B: Specify Platform** (Kubespray):
```bash
./scripts/hyperconverged-lab.sh kubespray
```

**Option C: Specify Platform** (Talos):
```bash
./scripts/hyperconverged-lab.sh talos
```

#### Step 3: Monitor Deployment

The deployment script will:

1. **Create OpenStack Resources** (5-10 minutes):
   - Create network and subnets
   - Create security groups
   - Launch instances
   - Assign floating IPs

2. **Deploy Kubernetes** (10-15 minutes):
   - Install Kubernetes via Kubespray or Talos
   - Configure networking (Kube-OVN)
   - Set up storage (Longhorn or Ceph)

3. **Deploy OpenStack Services** (15-20 minutes):
   - Install infrastructure services (MariaDB, RabbitMQ, Memcached)
   - Install core OpenStack services (Keystone, Glance, Nova, Neutron, Cinder)
   - Install optional services (based on configuration)

**Total deployment time**: Approximately 30-45 minutes

#### Step 4: Access the Lab Environment

Once deployment completes, the script will output:

```
================================================================================
Deployment Complete!
================================================================================

Lab Environment Details:
  - Lab Name: caracal-to-epoxy-test
  - Platform: kubespray
  - Kubernetes Version: v1.31.4
  - OpenStack Release: 2024.1 (Caracal)

Access Information:
  - Jump Host IP: 203.0.113.10
  - SSH Command: ssh ubuntu@203.0.113.10
  - Kubeconfig: /etc/genestack/kubeconfig

Next Steps:
  1. SSH into the jump host
  2. Verify Kubernetes cluster: kubectl get nodes
  3. Verify OpenStack services: openstack service list
  4. Run upgrade tests

================================================================================
```

**SSH into the lab**:
```bash
# Use the IP provided in the output
ssh ubuntu@<JUMP_HOST_IP>

# Or if using Talos with jump host
ssh ubuntu@<JUMP_HOST_IP>
```

#### Step 5: Verify Lab Deployment

Once logged into the lab, verify the deployment:

1. **Check Kubernetes cluster**:
   ```bash
   kubectl get nodes
   kubectl get pods --all-namespaces
   ```

2. **Check OpenStack services**:
   ```bash
   source /etc/genestack/openrc
   openstack service list
   openstack endpoint list
   ```

3. **Verify service health**:
   ```bash
   openstack compute service list
   openstack network agent list
   openstack volume service list
   ```

4. **Test basic operations**:
   ```bash
   # Create a test network
   openstack network create test-net
   
   # Create a test image (if not already present)
   openstack image list
   
   # List flavors
   openstack flavor list
   ```

### Deployment Options

The hyperconverged lab script supports several options:

#### Include Specific Services

Deploy only specific OpenStack services:

```bash
./scripts/hyperconverged-lab.sh kubespray -i heat,octavia,magnum
```

#### Exclude Specific Services

Deploy all services except specified ones:

```bash
./scripts/hyperconverged-lab.sh kubespray -e skyline,trove
```

#### Enable Extra Operations

Run additional setup operations (k9s install, Octavia pre-configuration, etc.):

```bash
./scripts/hyperconverged-lab.sh kubespray -x
```

#### Combined Options

Combine multiple options:

```bash
./scripts/hyperconverged-lab.sh kubespray -i heat,octavia -x
```

### Deployment Timeline

Expected timeline for each phase:

| Phase | Duration | Description |
|-------|----------|-------------|
| Resource Creation | 5-10 min | Create OpenStack resources (network, instances, IPs) |
| Kubernetes Setup | 10-15 min | Deploy and configure Kubernetes cluster |
| Infrastructure Services | 5-10 min | Deploy MariaDB, RabbitMQ, Memcached |
| Core OpenStack Services | 10-15 min | Deploy Keystone, Glance, Nova, Neutron, Cinder |
| Optional Services | 5-10 min | Deploy additional services (if included) |
| Verification | 2-5 min | Run health checks and verification |
| **Total** | **30-45 min** | Complete deployment |

### Troubleshooting Deployment Issues

#### Issue: Deployment Fails During Resource Creation

**Symptoms**: Script fails when creating OpenStack resources

**Solutions**:
1. Check OpenStack quota: `openstack quota show`
2. Verify cloud configuration: `openstack --os-cloud ${OS_CLOUD} server list`
3. Check for existing resources with same name prefix
4. Review OpenStack API logs

#### Issue: Kubernetes Deployment Fails

**Symptoms**: Kubespray or Talos deployment fails

**Solutions**:
1. Check instance connectivity: `ping <instance-ip>`
2. Verify SSH access (Kubespray): `ssh ubuntu@<instance-ip>`
3. Check instance console logs: `openstack console log show <instance-name>`
4. Verify security group rules allow required ports

#### Issue: OpenStack Services Fail to Deploy

**Symptoms**: Helm deployments fail or pods don't start

**Solutions**:
1. Check pod status: `kubectl get pods --all-namespaces`
2. Check pod logs: `kubectl logs -n openstack <pod-name>`
3. Verify storage is available: `kubectl get pv,pvc --all-namespaces`
4. Check for resource constraints: `kubectl top nodes`

#### Issue: Deployment Takes Too Long

**Symptoms**: Deployment exceeds expected timeline

**Solutions**:
1. Check instance performance (may need larger flavor)
2. Verify network connectivity and bandwidth
3. Check for image download issues
4. Monitor deployment progress: `kubectl get pods -w --all-namespaces`

### Cleaning Up the Lab

When you're done testing, clean up the lab environment:

#### Kubespray Cleanup

```bash
cd /opt/genestack
./scripts/hyperconverged-lab-kubespray-uninstall.sh
```

#### Talos Cleanup

```bash
cd /opt/genestack
./scripts/hyperconverged-lab-talos-uninstall.sh
```

The cleanup script will:
1. Delete all OpenStack instances
2. Delete networks and subnets
3. Delete security groups
4. Release floating IPs
5. Optionally delete the Talos image from Glance

---

## Lab Testing Guide

This section provides comprehensive guidance for testing the OpenStack Caracal to Epoxy upgrade in the lab environment.

### Testing Prerequisites

Before starting upgrade testing, ensure:

1. **Lab is fully deployed**: All services are running and healthy
2. **Baseline established**: Document current state (versions, configurations, resources)
3. **Backup created**: Take snapshots or backups of the lab environment
4. **Upgrade tools installed**: Upgrade tooling is available in the lab
5. **Test data prepared**: Create test resources (instances, networks, volumes) for validation

### Test Scenarios

#### Scenario 1: Pre-Upgrade Validation

**Objective**: Verify the pre-upgrade validation catches issues before upgrade

**Steps**:

1. **Set up Python environment** (if not already done):
   ```bash
   cd /opt/genestack/upgrade-tools
   
   # Install python3-venv if needed
   sudo apt-get update
   sudo apt-get install -y python3-venv python3-full
   
   # Create and activate virtual environment
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   
   # Upgrade pip and install requirements
   pip install --upgrade pip
   pip install -r requirements.txt
   
   # Install the upgrade tools package in development mode
   pip install -e .
   ```

2. **Run pre-upgrade validation**:
   ```bash
   ./scripts/pre-upgrade-validate.sh
   ```

3. **Review validation report**:
   ```bash
   cat validation-report.md
   ```

3. **Expected results**:
   - All services reported as healthy
   - All pods in Running state
   - All API endpoints accessible
   - Database backups verified
   - No active migrations or jobs
   - Sufficient cluster resources

4. **Test failure scenarios**:
   ```bash
   # Stop a service to test validation failure
   kubectl scale deployment -n openstack keystone-api --replicas=0
   
   # Run validation again
   ./scripts/pre-upgrade-validate.sh
   
   # Should report keystone as unhealthy and halt
   
   # Restore service
   kubectl scale deployment -n openstack keystone-api --replicas=3
   ```

#### Scenario 2: Dry-Run Upgrade

**Objective**: Test the upgrade process without making actual changes

**Steps**:

1. **Run upgrade in dry-run mode**:
   ```bash
   cd /opt/genestack/upgrade-tools
   ./openstack-upgrade upgrade --dry-run
   ```

2. **Review planned changes**:
   ```bash
   cat version-update-report.md
   ```

3. **Expected results**:
   - All chart version updates listed
   - All configuration changes documented
   - Upgrade order displayed
   - No actual changes applied
   - Estimated duration provided

4. **Verify no changes were made**:
   ```bash
   # Check chart versions unchanged
   cat /opt/genestack/helm-chart-versions.yaml
   
   # Check pods unchanged
   kubectl get pods -n openstack
   ```

#### Scenario 3: Full Upgrade Execution

**Objective**: Perform a complete upgrade from Caracal to Epoxy

**Steps**:

1. **Create baseline snapshot**:
   ```bash
   # Document current state
   openstack service list > pre-upgrade-services.txt
   kubectl get pods -n openstack > pre-upgrade-pods.txt
   openstack compute service list > pre-upgrade-compute.txt
   openstack network agent list > pre-upgrade-network.txt
   ```

2. **Run the upgrade**:
   ```bash
   cd /opt/genestack/upgrade-tools
   ./scripts/upgrade-execute.sh
   ```

3. **Monitor upgrade progress**:
   ```bash
   # In another terminal, watch pods
   kubectl get pods -n openstack -w
   
   # Monitor upgrade logs
   tail -f upgrade.log
   ```

4. **Expected results**:
   - Pre-upgrade validation passes
   - Chart versions updated successfully
   - Services upgraded in dependency order
   - Each service health check passes
   - Post-upgrade verification succeeds
   - Upgrade report generated

5. **Verify upgrade completion**:
   ```bash
   # Check all pods are running
   kubectl get pods -n openstack
   
   # Verify service versions
   openstack --version
   
   # Check service health
   openstack compute service list
   openstack network agent list
   openstack volume service list
   ```

#### Scenario 4: Post-Upgrade Verification

**Objective**: Verify all services are functioning correctly after upgrade

**Steps**:

1. **Run post-upgrade verification**:
   ```bash
   cd /opt/genestack/upgrade-tools
   ./scripts/post-upgrade-verify.sh
   ```

2. **Test core operations**:
   ```bash
   # Test image operations
   openstack image list
   
   # Test network operations
   openstack network create test-upgrade-net
   openstack subnet create test-upgrade-subnet \
     --network test-upgrade-net \
     --subnet-range 192.168.100.0/24
   
   # Test compute operations
   openstack server create test-upgrade-vm \
     --flavor m1.small \
     --image cirros \
     --network test-upgrade-net
   
   # Wait for instance to be active
   openstack server show test-upgrade-vm
   
   # Test volume operations
   openstack volume create test-upgrade-vol --size 1
   
   # Attach volume to instance
   openstack server add volume test-upgrade-vm test-upgrade-vol
   
   # Verify attachment
   openstack server show test-upgrade-vm
   ```

3. **Clean up test resources**:
   ```bash
   openstack server remove volume test-upgrade-vm test-upgrade-vol
   openstack server delete test-upgrade-vm
   openstack volume delete test-upgrade-vol
   openstack subnet delete test-upgrade-subnet
   openstack network delete test-upgrade-net
   ```

4. **Expected results**:
   - All API endpoints respond correctly
   - All service lists show services as up/enabled
   - Instance creation succeeds
   - Network creation succeeds
   - Volume creation and attachment succeeds
   - No critical errors in logs

#### Scenario 5: Rollback Testing

**Objective**: Verify rollback functionality works correctly

**Steps**:

1. **Simulate upgrade failure**:
   ```bash
   # Option 1: Manually trigger rollback
   cd /opt/genestack/upgrade-tools
   ./scripts/rollback.sh
   
   # Option 2: Cause a failure during upgrade
   # (This would require modifying the upgrade process)
   ```

2. **Monitor rollback**:
   ```bash
   # Watch pods during rollback
   kubectl get pods -n openstack -w
   
   # Monitor rollback logs
   tail -f rollback.log
   ```

3. **Verify rollback completion**:
   ```bash
   # Check chart versions restored
   cat /opt/genestack/helm-chart-versions.yaml
   
   # Verify services are back to Caracal
   openstack --version
   
   # Check all services healthy
   openstack compute service list
   openstack network agent list
   ```

4. **Expected results**:
   - Chart versions restored to Caracal
   - All services return to healthy state
   - All pods running
   - API endpoints accessible
   - Rollback report generated

#### Scenario 6: Breaking Change Handling

**Objective**: Verify breaking changes are detected and handled correctly

**Steps**:

1. **Check breaking change detection**:
   ```bash
   cd /opt/genestack/upgrade-tools
   ./openstack-upgrade detect-breaking-changes
   ```

2. **Review breaking changes report**:
   ```bash
   cat breaking-changes-report.md
   ```

3. **Expected results**:
   - oslo.messaging configuration changes detected
   - Deprecated options identified
   - Mitigation steps provided
   - Impact assessment included

4. **Verify deprecated options are handled**:
   ```bash
   # Check for deprecated oslo.messaging options
   grep -r "heartbeat_in_pthread" /opt/genestack/base-helm-configs/
   
   # Should not find any after upgrade
   ```

#### Scenario 7: Service-Specific Testing

**Objective**: Test specific OpenStack services after upgrade

**Keystone (Identity)**:
```bash
# Test authentication
openstack token issue

# Test user operations
openstack user list
openstack project list
openstack role list

# Test endpoint operations
openstack endpoint list
openstack service list
```

**Glance (Image)**:
```bash
# Test image operations
openstack image list
openstack image show <image-id>

# Upload test image (if needed)
wget http://download.cirros-cloud.net/0.6.2/cirros-0.6.2-x86_64-disk.img
openstack image create cirros-test \
  --file cirros-0.6.2-x86_64-disk.img \
  --disk-format qcow2 \
  --container-format bare \
  --public
```

**Nova (Compute)**:
```bash
# Test compute services
openstack compute service list
openstack hypervisor list
openstack flavor list

# Test instance operations
openstack server list
openstack server create test-vm \
  --flavor m1.small \
  --image cirros \
  --network private
```

**Neutron (Network)**:
```bash
# Test network services
openstack network agent list
openstack network list
openstack subnet list
openstack router list

# Test network operations
openstack network create test-net
openstack subnet create test-subnet \
  --network test-net \
  --subnet-range 10.0.0.0/24
```

**Cinder (Volume)**:
```bash
# Test volume services
openstack volume service list
openstack volume type list

# Test volume operations
openstack volume list
openstack volume create test-vol --size 1
openstack volume show test-vol
```

### Performance Testing

#### Baseline Performance Metrics

Before upgrade, collect baseline metrics:

```bash
# API response times
time openstack server list
time openstack network list
time openstack volume list

# Resource utilization
kubectl top nodes
kubectl top pods -n openstack

# Service response times
curl -w "@curl-format.txt" -o /dev/null -s https://${GATEWAY_DOMAIN}/identity/v3
```

Create `curl-format.txt`:
```
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_appconnect:  %{time_appconnect}\n
time_pretransfer:  %{time_pretransfer}\n
time_redirect:  %{time_redirect}\n
time_starttransfer:  %{time_starttransfer}\n
----------\n
time_total:  %{time_total}\n
```

#### Post-Upgrade Performance Comparison

After upgrade, collect the same metrics and compare:

```bash
# Compare API response times
# (Should be similar or better)

# Compare resource utilization
# (Should be similar, slight increase acceptable)

# Compare service response times
# (Should be similar or better)
```

### Expected Test Results

#### Successful Upgrade

A successful upgrade should show:

- ✅ All pre-upgrade validations pass
- ✅ All chart versions updated to Epoxy (2025.1)
- ✅ All services upgraded in correct order
- ✅ All pods reach Running state
- ✅ All API endpoints accessible
- ✅ All service lists show services as up/enabled
- ✅ All functional tests pass
- ✅ Performance metrics within acceptable range
- ✅ No critical errors in logs
- ✅ Upgrade report generated successfully

#### Common Issues and Solutions

**Issue**: Pod fails to start after upgrade

**Solution**:
```bash
# Check pod status
kubectl describe pod -n openstack <pod-name>

# Check pod logs
kubectl logs -n openstack <pod-name>

# Check for image pull issues
kubectl get events -n openstack --sort-by='.lastTimestamp'
```

**Issue**: API endpoint not responding

**Solution**:
```bash
# Check service status
kubectl get svc -n openstack

# Check ingress/gateway
kubectl get gateway -n openstack
kubectl get httproute -n openstack

# Test endpoint directly
curl -k https://<service-ip>:<port>/
```

**Issue**: Database migration fails

**Solution**:
```bash
# Check db-sync job logs
kubectl logs -n openstack <service>-db-sync-<hash>

# Check database connectivity
kubectl exec -n openstack <service>-api-<hash> -- mysql -h mariadb -u root -p<password> -e "SHOW DATABASES;"

# Manually run db-sync if needed
kubectl delete job -n openstack <service>-db-sync
# Re-run helm upgrade to recreate job
```

### Test Documentation

Document all test results:

1. **Test Execution Log**:
   - Date and time of test
   - Lab environment details
   - Test scenario executed
   - Results (pass/fail)
   - Issues encountered
   - Resolution steps

2. **Performance Metrics**:
   - Pre-upgrade baseline
   - Post-upgrade measurements
   - Comparison and analysis

3. **Issue Tracker**:
   - List of issues found
   - Severity and impact
   - Workarounds or fixes
   - Status (open/resolved)

4. **Lessons Learned**:
   - What went well
   - What could be improved
   - Recommendations for production

### Next Steps After Lab Testing

Once lab testing is complete and successful:

1. **Review all test results**: Ensure all scenarios passed
2. **Document any issues**: Create tickets for any problems found
3. **Update upgrade procedures**: Incorporate lessons learned
4. **Plan production upgrade**: Schedule maintenance window
5. **Prepare rollback plan**: Document rollback procedures
6. **Communicate with stakeholders**: Share test results and upgrade plan

---

## Additional Resources

- [Genestack Documentation](https://docs.rackspacecloud.com/)
- [OpenStack Epoxy Release Notes](https://releases.openstack.org/epoxy/)
- [OpenStack-Helm Documentation](https://docs.openstack.org/openstack-helm/)
- [Upgrade Tools README](../README.md)
- [Pre-Upgrade Validation Guide](VALIDATION.md)

## Support

For issues or questions:

1. Check the [Genestack GitHub Issues](https://github.com/rackerlabs/genestack/issues)
2. Review the [Genestack Documentation](https://docs.rackspacecloud.com/)
3. Contact your Genestack support team

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-04  
**Applies To**: OpenStack Caracal (2024.1/2024.2) to Epoxy (2025.1) Upgrade
