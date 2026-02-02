# Envoy Gateway Multi-Gateway Setup

## Overview

Genestack supports deploying multiple Envoy Gateways with namespace isolation, flexible certificate management, and independent configuration. This enables you to run separate gateways for external (public-facing) and internal services with different security policies and certificate providers.

## Features

- **Configuration File Mode**: YAML-based configuration for complex multi-gateway setups
- **Namespace Isolation**: Each gateway runs in its own namespace for better security and organization
- **Hybrid Gateway Support**: External-only, internal-only, or both gateway types
- **Flexible Certificate Management**: Let's Encrypt or self-signed certificates per gateway
- **Multiple DNS Providers**: Support for Cloudflare, Route53, Azure DNS, Google Cloud DNS, DigitalOcean, GoDaddy, Rackspace, ACME-DNS, RFC2136
- **Route and Listener Processing**: Automatic creation of routes and listeners for multiple gateways
- **Multiple MetalLB Pools**: Different IP pools for different gateway types
- **Backward Compatibility**: Legacy single gateway mode still works unchanged

## Quick Start

### Single Gateway (Legacy Mode)

For simple single-gateway deployments, use the legacy command-line mode:

```bash
cd /opt/genestack/bin
./setup-envoy-gateway.sh \
  --email admin@example.com \
  --domain api.example.com \
  --challenge dns01 \
  --dns-plugin cloudflare
```

### Multi-Gateway (Configuration File Mode)

For complex multi-gateway deployments, use configuration file mode:

```bash
cd /opt/genestack/bin
./setup-envoy-gateway.sh --config /path/to/multi-gateway-config.yaml
```

## Configuration File Format

### Basic Structure

```yaml
gateways:
  <gateway-name>:
    enabled: true|false
    namespace: string
    type: external|internal|hybrid
    domain: string
    certificate:
      provider: letsencrypt|self-signed|custom
      email: string
      acme_challenge: http01|dns01
      dns_provider: string
      dns_credentials: object
    metallb_pool: string
    listeners: array
    routes: array

global:
  namespace_isolation: true|false
  auto_routes: true|false
  auto_listeners: true|false
```

### Global Settings

The `global` section controls behavior across all gateways:

**namespace_isolation** (default: `true`)

- **When `true`**: Each gateway is deployed in its own dedicated namespace (e.g., `envoy-gateway-external`, `envoy-gateway-internal`)
- **When `false`**: All gateways share a common namespace
- **Use case**: Enable for production environments to improve security isolation and resource organization. Disable for development/testing to simplify management.

**auto_routes** (default: `true`)

- **When `true`**: Automatically generates and applies HTTPRoute resources based on the `routes` array defined in each gateway configuration
- **When `false`**: Routes must be manually created and applied separately
- **Use case**: Enable for automated route management. Disable if you want full manual control over route creation or use external route management tools.

**auto_listeners** (default: `true`)

- **When `true`**: Automatically generates and applies listener configurations based on the `listeners` array defined in each gateway configuration
- **When `false`**: Listeners must be manually configured in the gateway manifests
- **Use case**: Enable for automated listener setup. Disable if you need custom listener configurations not supported by the automation.

### Example: External Gateway with Let's Encrypt

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
    routes:
      - name: keystone
        hostname: keystone.api.example.com
        service: keystone
        namespace: openstack
        port: 5000

global:
  namespace_isolation: true
  auto_routes: true
  auto_listeners: true
```

### Example: Internal Gateway with Self-Signed Certificates

```yaml
gateways:
  internal:
    enabled: true
    namespace: envoy-gateway-internal
    type: internal
    domain: internal.example.local
    certificate:
      provider: self-signed
    metallb_pool: internal-pool
    listeners:
      - name: https
        port: 443
        protocol: HTTPS
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

## DNS Provider Configuration

### Cloudflare

```yaml
certificate:
  provider: letsencrypt
  email: admin@example.com
  acme_challenge: dns01
  dns_provider: cloudflare
  dns_credentials:
    api_token: ${CLOUDFLARE_API_TOKEN}
```

### AWS Route53

```yaml
certificate:
  provider: letsencrypt
  email: admin@example.com
  acme_challenge: dns01
  dns_provider: route53
  dns_credentials:
    access_key_id: ${AWS_ACCESS_KEY_ID}
    secret_access_key: ${AWS_SECRET_ACCESS_KEY}
    hosted_zone_id: ${AWS_HOSTED_ZONE_ID}  # Optional
```

### Azure DNS

```yaml
certificate:
  provider: letsencrypt
  email: admin@example.com
  acme_challenge: dns01
  dns_provider: azuredns
  dns_credentials:
    subscription_id: ${AZURE_SUBSCRIPTION_ID}
    tenant_id: ${AZURE_TENANT_ID}
    client_id: ${AZURE_CLIENT_ID}
    client_secret: ${AZURE_CLIENT_SECRET}
    resource_group: ${AZURE_RESOURCE_GROUP}  # Optional
```

### Google Cloud DNS

```yaml
certificate:
  provider: letsencrypt
  email: admin@example.com
  acme_challenge: dns01
  dns_provider: google
  dns_credentials:
    service_account_key: ${GCP_SERVICE_ACCOUNT_KEY}  # JSON content
```

### DigitalOcean

```yaml
certificate:
  provider: letsencrypt
  email: admin@example.com
  acme_challenge: dns01
  dns_provider: digitalocean
  dns_credentials:
    api_token: ${DIGITALOCEAN_API_TOKEN}
```

### GoDaddy

```yaml
certificate:
  provider: letsencrypt
  email: admin@example.com
  acme_challenge: dns01
  dns_provider: godaddy
  dns_credentials:
    api_key: ${GODADDY_API_KEY}
    api_secret: ${GODADDY_API_SECRET}
```

### Rackspace

```yaml
certificate:
  provider: letsencrypt
  email: admin@example.com
  acme_challenge: dns01
  dns_provider: rackspace
  dns_credentials:
    username: ${RACKSPACE_USERNAME}
    api_key: ${RACKSPACE_API_KEY}
```

### ACME-DNS

```yaml
certificate:
  provider: letsencrypt
  email: admin@example.com
  acme_challenge: dns01
  dns_provider: acmedns
  dns_credentials:
    host: ${ACME_DNS_HOST}
    api_key: ${ACME_DNS_API_KEY}
```

### RFC2136 (Dynamic DNS)

```yaml
certificate:
  provider: letsencrypt
  email: admin@example.com
  acme_challenge: dns01
  dns_provider: rfc2136
  dns_credentials:
    nameserver: ${RFC2136_NAMESERVER}
    tsig_key_name: ${RFC2136_TSIG_KEY_NAME}
    tsig_secret: ${RFC2136_TSIG_SECRET}
    tsig_algorithm: HMACSHA256  # Optional, default: HMACSHA256
```

## Environment Variable Substitution

Configuration files support environment variable substitution using `${VAR_NAME}` syntax:

```yaml
certificate:
  dns_credentials:
    api_token: ${CLOUDFLARE_API_TOKEN}
```

Set environment variables before running the setup script:

```bash
export CLOUDFLARE_API_TOKEN="your-token-here"
./setup-envoy-gateway.sh --config multi-gateway-config.yaml
```

## Gateway Management

### Deploy All Gateways

```bash
./setup-envoy-gateway.sh --config multi-gateway-config.yaml
```

### Check Gateway Status

```bash
# Check specific gateway
kubectl get gateway external -n envoy-gateway-external

# Check all gateways
kubectl get gateway --all-namespaces

# Check gateway details
kubectl describe gateway external -n envoy-gateway-external
```

### Check Certificate Status

```bash
# Check certificates
kubectl get certificate -n envoy-gateway-external

# Check certificate details
kubectl describe certificate external-cert -n envoy-gateway-external

# Check certificate expiry
kubectl get certificate external-cert -n envoy-gateway-external -o jsonpath='{.status.notAfter}'
```

### Check Routes

```bash
# Check routes for a gateway
kubectl get httproute -n envoy-gateway-external

# Check route details
kubectl describe httproute keystone -n envoy-gateway-external
```

### View Gateway Logs

```bash
# Get gateway pod name
kubectl get pods -n envoy-gateway-external

# View logs
kubectl logs -n envoy-gateway-external <pod-name>
```

## Troubleshooting

### Gateway Not Programmed

If a gateway is not becoming programmed:

1. Check gateway status:
```bash
kubectl describe gateway <gateway-name> -n <namespace>
```

2. Check Envoy Gateway controller logs:
```bash
kubectl logs -n envoy-gateway-system deployment/envoy-gateway
```

3. Verify GatewayClass exists:
```bash
kubectl get gatewayclass
```

### Certificate Not Ready

If a certificate is not becoming ready:

1. Check certificate status:
```bash
kubectl describe certificate <cert-name> -n <namespace>
```

2. Check cert-manager logs:
```bash
kubectl logs -n cert-manager deployment/cert-manager
```

3. Check DNS credentials secret:
```bash
kubectl get secret <gateway-name>-dns-credentials -n <namespace>
```

4. Verify ClusterIssuer exists:
```bash
kubectl get clusterissuer
```

### Routes Not Working

If routes are not working:

1. Check HTTPRoute status:
```bash
kubectl describe httproute <route-name> -n <namespace>
```

2. Verify backend service exists:
```bash
kubectl get service <service-name> -n <service-namespace>
```

3. Check gateway listeners:
```bash
kubectl get gateway <gateway-name> -n <namespace> -o yaml
```

### DNS Provider Issues

If DNS01 challenge is failing:

1. Verify DNS credentials are correct
2. Check DNS provider API access
3. Verify domain ownership
4. Check cert-manager logs for specific errors

## Best Practices

### Security

- Use namespace isolation for production deployments
- Use Let's Encrypt for external gateways
- Use self-signed certificates for internal gateways only
- Store DNS credentials in environment variables or secrets management systems
- Rotate DNS credentials regularly
- Use RBAC to restrict access to gateway namespaces

### High Availability

- Deploy multiple gateway replicas
- Use multiple MetalLB IP pools
- Configure health checks for backend services
- Monitor certificate expiry dates
- Set up alerts for gateway failures

### Performance

- Use separate gateways for high-traffic services
- Configure resource limits for gateway pods
- Monitor gateway metrics
- Use connection pooling for backend services
- Enable HTTP/2 for better performance

### Maintenance

- Regularly update Envoy Gateway version
- Monitor certificate renewal
- Review and update routes periodically
- Clean up unused gateways and routes
- Document gateway configurations

## Migration from Single Gateway

See [Migration Guide](infrastructure-envoy-multi-gateway-migration.md) for detailed instructions on migrating from single gateway to multi-gateway setup.

## Advanced Configuration

### Custom Certificate Management

For bring-your-own-certificate scenarios:

```yaml
certificate:
  provider: custom
```

Then manually create the certificate secret:

```bash
kubectl create secret tls <gateway-name>-cert-tls \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem \
  -n <namespace>
```

### Multiple Listeners per Gateway

```yaml
listeners:
  - name: https
    port: 443
    protocol: HTTPS
  - name: http
    port: 80
    protocol: HTTP
  - name: https-alt
    port: 8443
    protocol: HTTPS
```

### Path-Based Routing

```yaml
routes:
  - name: api-v1
    hostname: api.example.com
    service: api-v1
    namespace: default
    port: 8080
    path: /v1
  - name: api-v2
    hostname: api.example.com
    service: api-v2
    namespace: default
    port: 8080
    path: /v2
```

## Reference

- [Envoy Gateway Documentation](https://gateway.envoyproxy.io/)
- [Gateway API Documentation](https://gateway-api.sigs.k8s.io/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [MetalLB Documentation](https://metallb.universe.tf/)

## Support

For issues and questions:
- GitHub Issues: https://github.com/rackerlabs/genestack/issues
- Design Document: [envoy-multi-gateway-design.md](envoy-multi-gateway-design.md)
