# Envoy Gateway Multi-Gateway Support Design

## Overview

This document outlines the design and implementation plan for adding multi-gateway support to Genestack's Envoy Gateway setup. The feature enables configuration file-based management of multiple gateways with namespace isolation, flexible certificate management, and full backward compatibility.

## Current State

The current implementation (`bin/setup-envoy-gateway.sh`) supports:
- Single gateway deployment
- Command-line argument-based configuration
- HTTP01 and DNS01 ACME challenges
- Multiple DNS providers (GoDaddy, Rackspace, Cloudflare, Route53, Azure DNS, etc.)
- Interactive mode for user input

## Proposed Features

### 1. Configuration File Mode (`--config`)

**Purpose**: Enable YAML-based configuration for complex multi-gateway setups

**Implementation**:
- Add `--config FILE` option to `setup-envoy-gateway.sh`
- Parse YAML configuration file
- Support environment variable substitution (e.g., `${CLOUDFLARE_API_TOKEN}`)
- Validate configuration schema
- Generate appropriate Kubernetes resources

**Example Usage**:
```bash
./setup-envoy-gateway.sh --config multi-gateway-config.yaml
```

### 2. Namespace Isolation

**Purpose**: Improve security and organization by running each gateway in its own namespace

**Implementation**:
- Create separate namespace for each gateway (e.g., `envoy-gateway-external`, `envoy-gateway-internal`)
- Apply RBAC policies per namespace
- Isolate network policies per gateway
- Enable independent scaling and resource management

**Benefits**:
- Better security isolation
- Easier troubleshooting
- Independent lifecycle management
- Cleaner resource organization

### 3. Hybrid Gateway Support

**Purpose**: Support external-only, internal-only, or both gateway types

**Gateway Types**:
- **External**: Public-facing services with Let's Encrypt certificates
- **Internal**: Internal services with self-signed certificates
- **Hybrid**: Both external and internal services in one gateway

**Implementation**:
- Define gateway type in configuration
- Apply appropriate certificate management per type
- Configure MetalLB pools per type
- Route traffic based on gateway type

### 4. Flexible Certificate Management

**Purpose**: Support different certificate providers per gateway

**Supported Providers**:
- **Let's Encrypt**: For external gateways
- **Self-Signed**: For internal gateways
- **Custom**: For bring-your-own-certificate scenarios

**Implementation**:
- Per-gateway certificate configuration
- Support multiple ACME challenge methods (HTTP01, DNS01)
- Support multiple DNS providers
- Automatic certificate renewal

### 5. Route and Listener Processing

**Purpose**: Automatically create routes and listeners for multiple gateways

**Implementation**:
- Parse routes from configuration
- Generate HTTPRoute resources per gateway
- Create listeners based on gateway type
- Support hostname-based routing
- Support path-based routing

### 6. Multiple MetalLB Pools

**Purpose**: Support different IP pools for different gateway types

**Implementation**:
- Define MetalLB pool per gateway
- Support external and internal pools
- Enable independent IP management
- Support pool-specific annotations

### 7. Internal Gateway Port 443

**Purpose**: Allow internal gateways to use port 443 (same as external)

**Implementation**:
- Configure separate listeners per gateway
- Support port 443 for both external and internal
- Use hostname-based routing to differentiate
- Ensure no port conflicts

### 8. Backward Compatibility

**Purpose**: Ensure existing single-gateway deployments continue to work

**Implementation**:
- Preserve all existing command-line options
- Support legacy mode when no `--config` is provided
- Maintain interactive mode
- Keep all DNS plugins working
- No breaking changes to existing workflows

## Architecture

### Directory Structure

```
bin/
├── setup-envoy-gateway.sh          # Main script (enhanced)
├── lib/
│   ├── gateway-config.sh           # Configuration parsing
│   ├── gateway-validator.sh        # Configuration validation
│   ├── gateway-generator.sh        # Kubernetes resource generation
│   └── gateway-utils.sh            # Utility functions

etc/gateway-api/
├── gateways/                       # Gateway definitions
│   ├── external-gateway.yaml
│   ├── internal-gateway.yaml
│   └── hybrid-gateway.yaml
├── routes/                         # Route definitions (existing)
└── listeners/                      # Listener definitions (existing)

examples/
├── multi-gateway-config.yaml       # Multi-gateway example
└── simple-gateway-config.yaml      # Single-gateway example (legacy)

docs/
└── envoy-multi-gateway-design.md   # This document
```

### Configuration Schema

```yaml
gateways:
  <gateway-name>:
    enabled: bool
    namespace: string
    type: external|internal|hybrid
    domain: string
    certificate:
      provider: letsencrypt|self-signed|custom
      email: string (for letsencrypt)
      acme_challenge: http01|dns01
      dns_provider: string
      dns_credentials: object
    metallb_pool: string
    listeners: array
    routes: array

global:
  legacy_mode: bool
  default_certificate_provider: string
  default_acme_challenge: string
  default_dns_provider: string
  namespace_isolation: bool
  auto_routes: bool
  auto_listeners: bool

dns_providers:
  <provider-name>:
    type: string
    credentials: object
```

## Implementation Plan

### Phase 1: Foundation (Week 1)
- [ ] Create configuration parsing library
- [ ] Implement configuration validation
- [ ] Add `--config` option to main script
- [ ] Create example configurations

### Phase 2: Multi-Gateway Support (Week 2)
- [ ] Implement namespace creation
- [ ] Add gateway type support
- [ ] Implement route generation
- [ ] Add listener generation

### Phase 3: Certificate Management (Week 3)
- [ ] Implement per-gateway certificate configuration
- [ ] Add certificate provider abstraction
- [ ] Support multiple DNS providers per gateway
- [ ] Add certificate validation

### Phase 4: Testing & Documentation (Week 4)
- [ ] Unit tests for configuration parsing
- [ ] Integration tests for multi-gateway setup
- [ ] End-to-end tests
- [ ] Update documentation
- [ ] Create migration guide

## Error Handling

- Validate configuration schema before processing
- Check for namespace conflicts
- Verify MetalLB pool availability
- Validate DNS provider credentials
- Check certificate provider compatibility
- Provide clear error messages

## Backward Compatibility

- Existing `--email`, `--domain`, `--challenge` options preserved
- Interactive mode still available
- Single gateway mode default when no `--config` provided
- All DNS plugins supported in both modes
- No changes to existing Kubernetes resources

## Testing Strategy

### Unit Tests
- Configuration parsing
- Configuration validation
- Resource generation
- DNS provider credential handling

### Integration Tests
- Multi-gateway deployment
- Namespace isolation
- Certificate management
- Route and listener creation

### End-to-End Tests
- Full deployment with multiple gateways
- Certificate renewal
- Route updates
- Failover scenarios

## Migration Path

### For Existing Users
1. No action required - existing deployments continue to work
2. Optional: Migrate to configuration file mode for easier management
3. Optional: Split single gateway into multiple gateways

### For New Users
1. Use configuration file mode for multi-gateway setups
2. Use legacy mode for simple single-gateway setups
3. Gradually migrate to multi-gateway as needs grow

## Success Criteria

- [ ] Configuration file mode works for multi-gateway setups
- [ ] Namespace isolation properly implemented
- [ ] All certificate providers supported
- [ ] Backward compatibility maintained
- [ ] All tests passing
- [ ] Documentation complete
- [ ] No breaking changes to existing deployments

## Future Enhancements

- Gateway auto-scaling based on traffic
- Advanced traffic management (canary deployments, A/B testing)
- Multi-region gateway support
- Gateway federation
- Advanced monitoring and observability
