#!/bin/bash
# shellcheck disable=SC2034,SC2155

# Gateway Resource Generator
# Generates Kubernetes resources for gateways, routes, and listeners

# Source required libraries
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/gateway-config.sh"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/gateway-utils.sh"

# Function to generate namespace manifest
generate_namespace() {
    local namespace="$1"
    local gateway_name="$2"
    
    cat <<EOF
---
apiVersion: v1
kind: Namespace
metadata:
  name: ${namespace}
  labels:
    app.kubernetes.io/name: envoy-gateway
    app.kubernetes.io/component: gateway
    app.kubernetes.io/instance: ${gateway_name}
    gateway.envoyproxy.io/owning-gateway-namespace: ${namespace}
    gateway.envoyproxy.io/owning-gateway-name: ${gateway_name}
EOF
}

# Function to generate gateway class manifest
generate_gateway_class() {
    local gateway_class_name="$1"
    
    cat <<EOF
---
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: ${gateway_class_name}
spec:
  controllerName: gateway.envoyproxy.io/gatewayclass-controller
EOF
}

# Function to generate gateway manifest
generate_gateway() {
    local gateway_name="$1"
    local namespace="$2"
    local gateway_class="$3"
    local gateway_type="$4"
    local metallb_pool="${5:-}"
    
    # Start the gateway manifest
    cat <<EOF
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: ${gateway_name}
  namespace: ${namespace}
  labels:
    app.kubernetes.io/name: envoy-gateway
    app.kubernetes.io/component: gateway
    app.kubernetes.io/instance: ${gateway_name}
    gateway.envoyproxy.io/gateway-type: ${gateway_type}
EOF
    
    # Add MetalLB annotation if pool is specified
    if [ -n "$metallb_pool" ]; then
        cat <<EOF
  annotations:
    metallb.universe.tf/address-pool: ${metallb_pool}
EOF
    fi
    
    cat <<EOF
spec:
  gatewayClassName: ${gateway_class}
  listeners:
EOF
    
    # Generate listeners from configuration if auto_listeners is enabled
    if is_auto_listeners_enabled && [ -n "$CONFIG_FILE" ]; then
        local listener_count
        listener_count=$(get_gateway_listeners "$gateway_name")
        
        if [ -n "$listener_count" ] && [ "$listener_count" != "null" ] && [ "$listener_count" -gt 0 ]; then
            for ((i=0; i<listener_count; i++)); do
                local listener_name
                local port
                local protocol
                local hostname
                local cert_ref
                
                listener_name=$(get_config_value "gateways.$gateway_name.listeners[$i].name")
                port=$(get_config_value "gateways.$gateway_name.listeners[$i].port")
                protocol=$(get_config_value "gateways.$gateway_name.listeners[$i].protocol")
                hostname=$(get_config_value "gateways.$gateway_name.listeners[$i].hostname" "")
                
                if [ "$protocol" = "HTTPS" ]; then
                    cert_ref="${gateway_name}-cert-tls"
                else
                    cert_ref=""
                fi
                
                # Generate listener inline
                echo "  - name: ${listener_name}"
                echo "    port: ${port}"
                echo "    protocol: ${protocol}"
                
                if [ -n "$hostname" ]; then
                    echo "    hostname: ${hostname}"
                fi
                
                if [ "$protocol" = "HTTPS" ] && [ -n "$cert_ref" ]; then
                    echo "    tls:"
                    echo "      mode: Terminate"
                    echo "      certificateRefs:"
                    echo "      - name: ${cert_ref}"
                fi
                
                echo "    allowedRoutes:"
                echo "      namespaces:"
                echo "        from: All"
            done
        else
            # No listeners configured, output empty array
            echo "  []"
        fi
    else
        # auto_listeners disabled, output empty array
        echo "  []"
    fi
}


# Function to generate listener for gateway
generate_listener() {
    local listener_name="$1"
    local port="$2"
    local protocol="$3"
    local hostname="${4:-}"
    local tls_mode="${5:-Terminate}"
    local cert_ref="${6:-}"
    
    local listener_yaml="  - name: ${listener_name}
    port: ${port}
    protocol: ${protocol}"
    
    if [ -n "$hostname" ]; then
        listener_yaml="${listener_yaml}
    hostname: ${hostname}"
    fi
    
    if [ "$protocol" = "HTTPS" ] && [ -n "$cert_ref" ]; then
        listener_yaml="${listener_yaml}
    tls:
      mode: ${tls_mode}
      certificateRefs:
      - name: ${cert_ref}"
    fi
    
    listener_yaml="${listener_yaml}
    allowedRoutes:
      namespaces:
        from: All"
    
    echo "$listener_yaml"
}

# Function to generate HTTPRoute manifest
generate_http_route() {
    local route_name="$1"
    local namespace="$2"
    local gateway_name="$3"
    local gateway_namespace="$4"
    local hostname="$5"
    local service_name="$6"
    local service_namespace="$7"
    local service_port="$8"
    local path_prefix="${9:-/}"
    
    cat <<EOF
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: ${route_name}
  namespace: ${namespace}
  labels:
    app.kubernetes.io/name: envoy-gateway
    app.kubernetes.io/component: route
    gateway.envoyproxy.io/owning-gateway-namespace: ${gateway_namespace}
    gateway.envoyproxy.io/owning-gateway-name: ${gateway_name}
spec:
  parentRefs:
  - name: ${gateway_name}
    namespace: ${gateway_namespace}
  hostnames:
  - ${hostname}
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: ${path_prefix}
    backendRefs:
    - name: ${service_name}
      namespace: ${service_namespace}
      port: ${service_port}
EOF
}

# Function to generate TLS certificate manifest (Let's Encrypt)
generate_letsencrypt_certificate() {
    local cert_name="$1"
    local namespace="$2"
    local domain="$3"
    local email="$4"
    local challenge_method="$5"
    local dns_provider="${6:-}"
    local secret_name="${7:-}"
    
    local cert_yaml="---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: ${cert_name}
  namespace: ${namespace}
spec:
  secretName: ${cert_name}-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - ${domain}
  - '*.${domain}'"
    
    echo "$cert_yaml"
}

# Function to generate ClusterIssuer for Let's Encrypt
generate_letsencrypt_issuer() {
    local issuer_name="$1"
    local email="$2"
    local challenge_method="$3"
    local dns_provider="${4:-}"
    local secret_name="${5:-}"
    
    cat <<EOF
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: ${issuer_name}
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ${email}
    privateKeySecretRef:
      name: ${issuer_name}-account-key
    solvers:
EOF

    if [ "$challenge_method" = "http01" ]; then
        cat <<EOF
    - http01:
        ingress:
          class: envoy
EOF
    elif [ "$challenge_method" = "dns01" ] && [ -n "$dns_provider" ]; then
        case "$dns_provider" in
            cloudflare)
                cat <<EOF
    - dns01:
        cloudflare:
          email: ${email}
          apiTokenSecretRef:
            name: ${secret_name}
            key: api-token
EOF
                ;;
            route53)
                cat <<EOF
    - dns01:
        route53:
          region: us-east-1
          accessKeyIDSecretRef:
            name: ${secret_name}
            key: access-key-id
          secretAccessKeySecretRef:
            name: ${secret_name}
            key: secret-access-key
EOF
                ;;
            azuredns)
                cat <<EOF
    - dns01:
        azureDNS:
          subscriptionIDSecretRef:
            name: ${secret_name}
            key: subscription-id
          tenantIDSecretRef:
            name: ${secret_name}
            key: tenant-id
          clientIDSecretRef:
            name: ${secret_name}
            key: client-id
          clientSecretSecretRef:
            name: ${secret_name}
            key: client-secret
          environment: AzurePublicCloud
EOF
                ;;
            google)
                cat <<EOF
    - dns01:
        cloudDNS:
          serviceAccountSecretRef:
            name: ${secret_name}
            key: service-account.json
EOF
                ;;
            digitalocean)
                cat <<EOF
    - dns01:
        digitalocean:
          tokenSecretRef:
            name: ${secret_name}
            key: api-token
EOF
                ;;
            godaddy)
                cat <<EOF
    - dns01:
        webhook:
          groupName: acme.mycompany.com
          solverName: godaddy
          config:
            apiKeySecretRef:
              name: ${secret_name}
              key: api-key
            apiSecretSecretRef:
              name: ${secret_name}
              key: api-secret
EOF
                ;;
            rackspace)
                cat <<EOF
    - dns01:
        webhook:
          groupName: acme.mycompany.com
          solverName: rackspace
          config:
            usernameSecretRef:
              name: ${secret_name}
              key: username
            apiKeySecretRef:
              name: ${secret_name}
              key: api-key
EOF
                ;;
            acmedns)
                cat <<EOF
    - dns01:
        acmeDNS:
          host: \${ACME_DNS_HOST}
          accountSecretRef:
            name: ${secret_name}
            key: api-key
EOF
                ;;
            rfc2136)
                cat <<EOF
    - dns01:
        rfc2136:
          nameserver: \${RFC2136_NAMESERVER}
          tsigKeyName: \${RFC2136_TSIG_KEY_NAME}
          tsigSecretSecretRef:
            name: ${secret_name}
            key: tsig-secret
          tsigAlgorithm: \${RFC2136_TSIG_ALGORITHM:-HMACSHA256}
EOF
                ;;
            *)
                echo "    # Unsupported DNS provider: ${dns_provider}" >&2
                ;;
        esac
    fi
}

# Function to generate self-signed certificate
generate_selfsigned_certificate() {
    local cert_name="$1"
    local namespace="$2"
    local domain="$3"
    
    cat <<EOF
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: ${cert_name}
  namespace: ${namespace}
spec:
  secretName: ${cert_name}-tls
  issuerRef:
    name: selfsigned-issuer
    kind: ClusterIssuer
  commonName: ${domain}
  dnsNames:
  - ${domain}
  - '*.${domain}'
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned-issuer
spec:
  selfSigned: {}
EOF
}

# Function to generate MetalLB IPAddressPool
generate_metallb_pool() {
    local pool_name="$1"
    local addresses="$2"
    local namespace="${3:-metallb-system}"
    
    cat <<EOF
---
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: ${pool_name}
  namespace: ${namespace}
spec:
  addresses:
  - ${addresses}
EOF
}

# Function to generate MetalLB L2Advertisement
generate_metallb_advertisement() {
    local pool_name="$1"
    local namespace="${2:-metallb-system}"
    
    cat <<EOF
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: ${pool_name}-advertisement
  namespace: ${namespace}
spec:
  ipAddressPools:
  - ${pool_name}
EOF
}

# Function to generate complete gateway configuration
generate_gateway_config() {
    local gateway_name="$1"
    
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    # Get gateway configuration
    local namespace
    local gateway_type
    local domain
    local gateway_class
    local cert_provider
    local email
    local acme_challenge
    local dns_provider
    local metallb_pool
    
    namespace=$(get_config_value "gateways.$gateway_name.namespace")
    gateway_type=$(get_config_value "gateways.$gateway_name.type")
    domain=$(get_config_value "gateways.$gateway_name.domain")
    gateway_class=$(get_config_value "gateways.$gateway_name.gateway_class" "eg")
    cert_provider=$(get_config_value "gateways.$gateway_name.certificate.provider" "self-signed")
    email=$(get_config_value "gateways.$gateway_name.certificate.email" "")
    acme_challenge=$(get_config_value "gateways.$gateway_name.certificate.acme_challenge" "http01")
    dns_provider=$(get_config_value "gateways.$gateway_name.certificate.dns_provider" "")
    metallb_pool=$(get_config_value "gateways.$gateway_name.metallb_pool" "")
    
    # Generate namespace
    generate_namespace "$namespace" "$gateway_name"
    echo ""
    
    # Generate gateway class (if needed)
    generate_gateway_class "$gateway_class"
    echo ""
    
    # Generate gateway
    generate_gateway "$gateway_name" "$namespace" "$gateway_class" "$gateway_type" "$metallb_pool"
    echo ""
    
    # Generate certificate based on provider
    if [ "$cert_provider" = "letsencrypt" ] && [ -n "$email" ]; then
        local secret_name="${gateway_name}-dns-credentials"
        generate_letsencrypt_issuer "letsencrypt-prod" "$email" "$acme_challenge" "$dns_provider" "$secret_name"
        echo ""
        generate_letsencrypt_certificate "${gateway_name}-cert" "$namespace" "$domain" "$email" "$acme_challenge" "$dns_provider" "$secret_name"
        echo ""
    elif [ "$cert_provider" = "self-signed" ]; then
        generate_selfsigned_certificate "${gateway_name}-cert" "$namespace" "$domain"
        echo ""
    fi
    
    return 0
}

# Function to generate routes for a gateway
generate_gateway_routes() {
    local gateway_name="$1"
    
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    local namespace
    namespace=$(get_config_value "gateways.$gateway_name.namespace")
    
    local route_count
    route_count=$(get_gateway_routes "$gateway_name")
    
    if [ -z "$route_count" ] || [ "$route_count" = "null" ] || [ "$route_count" -eq 0 ]; then
        return 0
    fi
    
    for ((i=0; i<route_count; i++)); do
        local route_name
        local hostname
        local service_name
        local service_namespace
        local service_port
        local path_prefix
        
        route_name=$(get_config_value "gateways.$gateway_name.routes[$i].name")
        hostname=$(get_config_value "gateways.$gateway_name.routes[$i].hostname")
        service_name=$(get_config_value "gateways.$gateway_name.routes[$i].service")
        service_namespace=$(get_config_value "gateways.$gateway_name.routes[$i].namespace")
        service_port=$(get_config_value "gateways.$gateway_name.routes[$i].port")
        path_prefix=$(get_config_value "gateways.$gateway_name.routes[$i].path" "/")
        
        generate_http_route "$route_name" "$namespace" "$gateway_name" "$namespace" "$hostname" "$service_name" "$service_namespace" "$service_port" "$path_prefix"
        echo ""
    done
    
    return 0
}

# Function to generate listeners for a gateway
generate_gateway_listeners() {
    local gateway_name="$1"
    
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    local listener_count
    listener_count=$(get_gateway_listeners "$gateway_name")
    
    if [ -z "$listener_count" ] || [ "$listener_count" = "null" ] || [ "$listener_count" -eq 0 ]; then
        return 0
    fi
    
    for ((i=0; i<listener_count; i++)); do
        local listener_name
        local port
        local protocol
        local hostname
        local cert_ref
        
        listener_name=$(get_config_value "gateways.$gateway_name.listeners[$i].name")
        port=$(get_config_value "gateways.$gateway_name.listeners[$i].port")
        protocol=$(get_config_value "gateways.$gateway_name.listeners[$i].protocol")
        hostname=$(get_config_value "gateways.$gateway_name.listeners[$i].hostname" "")
        
        if [ "$protocol" = "HTTPS" ]; then
            cert_ref="${gateway_name}-cert-tls"
        else
            cert_ref=""
        fi
        
        generate_listener "$listener_name" "$port" "$protocol" "$hostname" "Terminate" "$cert_ref"
        echo ""
    done
    
    return 0
}

# Function to generate all resources for all enabled gateways
generate_all_gateways() {
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    local gateway_names
    gateway_names=$(get_gateway_names)
    
    while IFS= read -r gateway_name; do
        if is_gateway_enabled "$gateway_name"; then
            print_section "Generating configuration for gateway: $gateway_name"
            
            generate_gateway_config "$gateway_name"
            generate_gateway_routes "$gateway_name"
        fi
    done <<< "$gateway_names"
    
    return 0
}
