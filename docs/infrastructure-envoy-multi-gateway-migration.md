# Migration Guide: Single Gateway to Multi-Gateway

## Overview

This guide helps you migrate from the legacy single Envoy Gateway setup to the new multi-gateway configuration file mode. The migration is optional - existing single gateway deployments continue to work unchanged.

## Why Migrate?

Benefits of multi-gateway setup:

- **Better Security**: Namespace isolation per gateway
- **Flexibility**: Different certificate providers per gateway
- **Organization**: Separate external and internal services
- **Scalability**: Independent scaling per gateway
- **Maintainability**: Easier to manage complex setups

## Migration Strategies

### Strategy 1: Keep Single Gateway (No Migration)

If your setup is simple and working well, you don't need to migrate. The legacy mode is fully supported and will continue to work.

**When to use:**

- Single domain with all services
- Simple certificate management
- No need for namespace isolation
- Small number of routes

**Action required:** None

### Strategy 2: Gradual Migration (Recommended)

Deploy new gateways alongside the existing one, then gradually move services.

**When to use:**

- Production environments
- Need zero downtime
- Want to test before full migration
- Complex routing requirements

**Steps:**

1. Deploy new multi-gateway setup in parallel
2. Test new gateways with non-critical services
3. Gradually move services to new gateways
4. Decommission old gateway when ready

### Strategy 3: Clean Migration

Remove existing gateway and deploy new multi-gateway setup.

**When to use:**

- Development/testing environments
- Can tolerate downtime
- Want clean slate
- Simple setup

**Steps:**

1. Document existing configuration
2. Remove old gateway
3. Deploy new multi-gateway setup
4. Verify all services working

## Pre-Migration Checklist

Before starting migration:

- [ ] Document current gateway configuration
- [ ] List all routes and services
- [ ] Note certificate configuration
- [ ] Identify DNS provider and credentials
- [ ] Check MetalLB pool configuration
- [ ] Backup current configuration
- [ ] Plan maintenance window (if needed)
- [ ] Notify stakeholders

## Step-by-Step Migration

### Step 1: Document Current Setup

Export current gateway configuration:

```bash
# Get current gateway
kubectl get gateway -A -o yaml > current-gateway.yaml

# Get current routes
kubectl get httproute -A -o yaml > current-routes.yaml

# Get current certificates
kubectl get certificate -A -o yaml > current-certificates.yaml

# Get current services
kubectl get service -A -o yaml > current-services.yaml
```

### Step 2: Create Configuration File

Create a new configuration file based on your current setup.

**Example: Converting single external gateway**

Current command:
```bash
./setup-envoy-gateway.sh \
  --email admin@example.com \
  --domain api.example.com \
  --challenge dns01 \
  --dns-plugin cloudflare
```

New configuration file (`multi-gateway-config.yaml`):
```yaml
gateways:
  external:
    enabled: true
    namespace: envoy-gateway-external
    type: external
    domain: api.example.com
    certificate:
      provider: letsencrypt
      email: admin@example.com
      acme_challenge: dns01
      dns_provider: cloudflare
      dns_credentials:
        api_token: ${CLOUDFLARE_API_TOKEN}
    metallb_pool: external-pool
    listeners:
      - name: https
        port: 443
        protocol: HTTPS
      - name: http
        port: 80
        protocol: HTTP
    routes: []  # Will be auto-generated or manually defined

global:
  namespace_isolation: true
  auto_routes: true
  auto_listeners: true
```

### Step 3: Add Routes to Configuration

Convert existing HTTPRoutes to configuration format:

```yaml
routes:
  - name: keystone
    hostname: keystone.api.example.com
    service: keystone
    namespace: openstack
    port: 5000
  - name: nova
    hostname: nova.api.example.com
    service: nova-api
    namespace: openstack
    port: 8774
  - name: horizon
    hostname: horizon.api.example.com
    service: horizon
    namespace: openstack
    port: 80
```

### Step 4: Test Configuration

Validate the configuration file:

```bash
# Set environment variables
export CLOUDFLARE_API_TOKEN="your-token"

# Dry-run validation (if available)
./setup-envoy-gateway.sh --config multi-gateway-config.yaml --dry-run

# Or deploy to test namespace first
# Edit config to use test namespace
./setup-envoy-gateway.sh --config multi-gateway-config-test.yaml
```

### Step 5: Deploy New Gateway

For gradual migration, deploy alongside existing gateway:

```bash
# Deploy new multi-gateway setup
./setup-envoy-gateway.sh --config multi-gateway-config.yaml

# Verify deployment
kubectl get gateway -A
kubectl get httproute -A
kubectl get certificate -A
```

### Step 6: Update DNS Records

Point DNS records to new gateway:

```bash
# Get new gateway IP
kubectl get service -n envoy-gateway-external

# Update DNS records to point to new IP
# Test with curl or browser
curl -k https://keystone.api.example.com
```

### Step 7: Monitor and Verify

Monitor the new gateway:

```bash
# Check gateway status
kubectl describe gateway external -n envoy-gateway-external

# Check certificate status
kubectl get certificate -n envoy-gateway-external

# Check route status
kubectl get httproute -n envoy-gateway-external

# View logs
kubectl logs -n envoy-gateway-external -l app=envoy-gateway
```

### Step 8: Decommission Old Gateway (Optional)

Once verified, remove old gateway:

```bash
# Delete old gateway
kubectl delete gateway <old-gateway-name> -n <old-namespace>

# Delete old routes
kubectl delete httproute -n <old-namespace> --all

# Delete old certificates
kubectl delete certificate -n <old-namespace> --all

# Delete old namespace (if using namespace isolation)
kubectl delete namespace <old-namespace>
```

## Migration Examples

### Example 1: Single External Gateway

**Before:**
```bash
./setup-envoy-gateway.sh \
  --email admin@example.com \
  --domain cloud.example.com \
  --challenge http01
```

**After:**
```yaml
gateways:
  external:
    enabled: true
    namespace: envoy-gateway-external
    type: external
    domain: cloud.example.com
    certificate:
      provider: letsencrypt
      email: admin@example.com
      acme_challenge: http01
    metallb_pool: external-pool
    listeners:
      - name: https
        port: 443
        protocol: HTTPS
      - name: http
        port: 80
        protocol: HTTP

global:
  namespace_isolation: true
  auto_routes: true
```

### Example 2: Split External and Internal

**Before:** Single gateway for all services

**After:** Separate gateways for external and internal
```yaml
gateways:
  external:
    enabled: true
    namespace: envoy-gateway-external
    type: external
    domain: api.example.com
    certificate:
      provider: letsencrypt
      email: admin@example.com
      acme_challenge: dns01
      dns_provider: cloudflare
      dns_credentials:
        api_token: ${CLOUDFLARE_API_TOKEN}
    metallb_pool: external-pool
    routes:
      - name: keystone
        hostname: keystone.api.example.com
        service: keystone
        namespace: openstack
        port: 5000

  internal:
    enabled: true
    namespace: envoy-gateway-internal
    type: internal
    domain: internal.example.local
    certificate:
      provider: self-signed
    metallb_pool: internal-pool
    routes:
      - name: mariadb
        hostname: mariadb.internal.example.local
        service: mariadb
        namespace: openstack
        port: 3306

global:
  namespace_isolation: true
  auto_routes: true
```

### Example 3: Multiple DNS Providers

**Before:** Single DNS provider

**After:** Different DNS providers per gateway
```yaml
gateways:
  production:
    enabled: true
    namespace: envoy-gateway-prod
    type: external
    domain: prod.example.com
    certificate:
      provider: letsencrypt
      email: admin@example.com
      acme_challenge: dns01
      dns_provider: route53
      dns_credentials:
        access_key_id: ${AWS_ACCESS_KEY_ID}
        secret_access_key: ${AWS_SECRET_ACCESS_KEY}

  staging:
    enabled: true
    namespace: envoy-gateway-staging
    type: external
    domain: staging.example.com
    certificate:
      provider: letsencrypt
      email: admin@example.com
      acme_challenge: dns01
      dns_provider: cloudflare
      dns_credentials:
        api_token: ${CLOUDFLARE_API_TOKEN}

global:
  namespace_isolation: true
```

## Rollback Plan

If migration fails, rollback steps:

1. **Keep old gateway running** during migration
2. **Revert DNS changes** to point back to old gateway
3. **Remove new gateways** if needed:
   ```bash
   kubectl delete gateway <new-gateway> -n <new-namespace>
   kubectl delete namespace <new-namespace>
   ```
4. **Verify old gateway** is still working
5. **Investigate issues** before retry

## Common Migration Issues

### Issue: Certificate Not Ready

**Symptom:** Certificate stuck in "Pending" state

**Solution:**
1. Check DNS credentials are correct
2. Verify DNS provider API access
3. Check cert-manager logs
4. Ensure domain is properly configured

### Issue: Routes Not Working

**Symptom:** 404 or connection refused errors

**Solution:**
1. Verify backend service exists and is running
2. Check service namespace matches route configuration
3. Verify service port is correct
4. Check gateway listeners are configured

### Issue: Gateway Not Programmed

**Symptom:** Gateway stuck in "Pending" state

**Solution:**
1. Check Envoy Gateway controller is running
2. Verify GatewayClass exists
3. Check MetalLB is configured
4. Review gateway configuration for errors

### Issue: Namespace Conflicts

**Symptom:** Resources already exist errors

**Solution:**
1. Use different namespace names
2. Clean up old resources first
3. Use unique gateway names

## Post-Migration Tasks

After successful migration:

- [ ] Update documentation with new configuration
- [ ] Update runbooks and procedures
- [ ] Train team on new configuration format
- [ ] Set up monitoring for new gateways
- [ ] Configure alerts for certificate expiry
- [ ] Schedule regular reviews of gateway configuration
- [ ] Document lessons learned
- [ ] Clean up old gateway resources

## Best Practices

### During Migration

- **Test thoroughly** in non-production first
- **Migrate gradually** one service at a time
- **Keep old gateway** running during migration
- **Monitor closely** for issues
- **Have rollback plan** ready
- **Document everything** for future reference

### After Migration

- **Monitor certificate expiry** dates
- **Review gateway logs** regularly
- **Update routes** as services change
- **Keep configuration** in version control
- **Regular security audits** of gateway configuration
- **Performance testing** of new setup

## Getting Help

If you encounter issues during migration:

1. Check [Troubleshooting Guide](infrastructure-envoy-multi-gateway.md#troubleshooting)
2. Review [Design Document](envoy-multi-gateway-design.md)
3. Check Envoy Gateway logs
4. Review cert-manager logs
5. Open GitHub issue with details

## Conclusion

Migration to multi-gateway setup provides better security, flexibility, and maintainability. Take your time, test thoroughly, and migrate gradually for best results.

For questions or issues, refer to the main [Multi-Gateway Documentation](infrastructure-envoy-multi-gateway.md).
