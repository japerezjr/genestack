#!/bin/bash
# shellcheck disable=SC2034,SC2155

# Gateway Orchestrator
# Orchestrates the deployment of multiple gateways from configuration

# Source required libraries
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/gateway-config.sh"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/gateway-validator.sh"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/gateway-generator.sh"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/gateway-utils.sh"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/gateway-certificates.sh"

# Function to setup a single gateway
setup_gateway() {
    local gateway_name="$1"
    
    print_section "Setting up gateway: $gateway_name"
    
    # Get gateway configuration
    local namespace
    local gateway_type
    local domain
    local cert_provider
    
    namespace=$(get_config_value "gateways.$gateway_name.namespace")
    gateway_type=$(get_config_value "gateways.$gateway_name.type")
    domain=$(get_config_value "gateways.$gateway_name.domain")
    cert_provider=$(get_config_value "gateways.$gateway_name.certificate.provider" "self-signed")
    
    print_message "INFO" "Gateway: $gateway_name"
    print_message "INFO" "  Type: $gateway_type"
    print_message "INFO" "  Namespace: $namespace"
    print_message "INFO" "  Domain: $domain"
    print_message "INFO" "  Certificate Provider: $cert_provider"
    echo ""
    
    # Create namespace if namespace isolation is enabled
    if is_namespace_isolation_enabled; then
        print_message "INFO" "Creating namespace: $namespace"
        if ! create_namespace "$namespace"; then
            print_message "ERROR" "Failed to create namespace: $namespace"
            return 1
        fi
    fi
    
    # Setup certificate provider and credentials
    print_message "INFO" "Setting up certificate provider"
    if ! setup_certificate_provider "$gateway_name" "$namespace"; then
        print_message "ERROR" "Failed to setup certificate provider"
        return 1
    fi
    
    # Generate and apply gateway configuration
    local temp_dir
    temp_dir=$(mktemp -d)
    local gateway_manifest="${temp_dir}/${gateway_name}-gateway.yaml"
    
    print_message "INFO" "Generating gateway manifest"
    generate_gateway_config "$gateway_name" > "$gateway_manifest"
    
    if [ ! -s "$gateway_manifest" ]; then
        print_message "ERROR" "Failed to generate gateway manifest"
        rm -rf "$temp_dir"
        return 1
    fi
    
    print_message "INFO" "Applying gateway manifest"
    if ! kubectl apply -f "$gateway_manifest"; then
        print_message "ERROR" "Failed to apply gateway manifest"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Wait for gateway to be programmed
    print_message "INFO" "Waiting for gateway to be programmed"
    if ! wait_for_gateway "$gateway_name" "$namespace" 300; then
        print_message "WARN" "Gateway did not become programmed within timeout"
    fi
    
    # Wait for certificate to be ready (if using Let's Encrypt)
    if [ "$cert_provider" = "letsencrypt" ]; then
        local cert_name="${gateway_name}-cert"
        print_message "INFO" "Waiting for certificate to be ready"
        if ! wait_for_certificate "$cert_name" "$namespace" 300; then
            print_message "WARN" "Certificate did not become ready within timeout"
        fi
    fi
    
    # Generate and apply routes if auto_routes is enabled
    if is_auto_routes_enabled; then
        local routes_manifest="${temp_dir}/${gateway_name}-routes.yaml"
        
        print_message "INFO" "Generating routes manifest"
        generate_gateway_routes "$gateway_name" > "$routes_manifest"
        
        if [ -s "$routes_manifest" ]; then
            print_message "INFO" "Applying routes manifest"
            if ! kubectl apply -f "$routes_manifest"; then
                print_message "WARN" "Failed to apply routes manifest"
            fi
        else
            print_message "INFO" "No routes to apply"
        fi
    fi
    
    # Clean up temporary files
    rm -rf "$temp_dir"
    
    print_message "SUCCESS" "Gateway $gateway_name setup complete"
    echo ""
    
    return 0
}

# Function to setup all enabled gateways
setup_all_gateways() {
    if [ -z "$CONFIG_FILE" ]; then
        print_message "ERROR" "No configuration file loaded"
        return 1
    fi
    
    print_section "Multi-Gateway Setup"
    
    # Validate configuration
    print_message "INFO" "Validating configuration"
    if ! validate_config "$CONFIG_FILE"; then
        print_message "ERROR" "Configuration validation failed"
        return 1
    fi
    
    # Print configuration summary
    echo ""
    print_config_summary
    echo ""
    
    # Get all gateway names
    local gateway_names
    gateway_names=$(get_gateway_names)
    
    if [ -z "$gateway_names" ]; then
        print_message "ERROR" "No gateways found in configuration"
        return 1
    fi
    
    # Setup each enabled gateway
    local failed_gateways=()
    while IFS= read -r gateway_name; do
        if is_gateway_enabled "$gateway_name"; then
            if ! setup_gateway "$gateway_name"; then
                failed_gateways+=("$gateway_name")
            fi
        else
            print_message "INFO" "Gateway $gateway_name is disabled, skipping"
        fi
    done <<< "$gateway_names"
    
    # Report results
    echo ""
    print_section "Setup Summary"
    
    if [ ${#failed_gateways[@]} -eq 0 ]; then
        print_message "SUCCESS" "All gateways setup successfully"
        return 0
    else
        print_message "ERROR" "Some gateways failed to setup:"
        for gateway in "${failed_gateways[@]}"; do
            print_message "ERROR" "  - $gateway"
        done
        return 1
    fi
}

# Function to cleanup a single gateway
cleanup_gateway() {
    local gateway_name="$1"
    
    print_section "Cleaning up gateway: $gateway_name"
    
    local namespace
    namespace=$(get_config_value "gateways.$gateway_name.namespace")
    
    print_message "INFO" "Deleting gateway: $gateway_name"
    kubectl delete gateway "$gateway_name" -n "$namespace" --ignore-not-found=true
    
    print_message "INFO" "Deleting routes for gateway: $gateway_name"
    kubectl delete httproute -n "$namespace" -l "gateway.envoyproxy.io/owning-gateway-name=$gateway_name" --ignore-not-found=true
    
    print_message "INFO" "Deleting certificates for gateway: $gateway_name"
    kubectl delete certificate -n "$namespace" -l "gateway.envoyproxy.io/owning-gateway-name=$gateway_name" --ignore-not-found=true
    
    if is_namespace_isolation_enabled; then
        print_message "INFO" "Deleting namespace: $namespace"
        kubectl delete namespace "$namespace" --ignore-not-found=true
    fi
    
    print_message "SUCCESS" "Gateway $gateway_name cleanup complete"
    echo ""
    
    return 0
}

# Function to cleanup all gateways
cleanup_all_gateways() {
    if [ -z "$CONFIG_FILE" ]; then
        print_message "ERROR" "No configuration file loaded"
        return 1
    fi
    
    print_section "Multi-Gateway Cleanup"
    
    local gateway_names
    gateway_names=$(get_gateway_names)
    
    if [ -z "$gateway_names" ]; then
        print_message "WARN" "No gateways found in configuration"
        return 0
    fi
    
    while IFS= read -r gateway_name; do
        cleanup_gateway "$gateway_name"
    done <<< "$gateway_names"
    
    print_message "SUCCESS" "All gateways cleaned up"
    return 0
}

# Function to get gateway status
get_gateway_status() {
    local gateway_name="$1"
    
    local namespace
    namespace=$(get_config_value "gateways.$gateway_name.namespace")
    
    print_section "Gateway Status: $gateway_name"
    
    print_message "INFO" "Gateway Resource:"
    kubectl get gateway "$gateway_name" -n "$namespace" 2>/dev/null || print_message "WARN" "Gateway not found"
    echo ""
    
    print_message "INFO" "Routes:"
    kubectl get httproute -n "$namespace" -l "gateway.envoyproxy.io/owning-gateway-name=$gateway_name" 2>/dev/null || print_message "INFO" "No routes found"
    echo ""
    
    print_message "INFO" "Certificates:"
    kubectl get certificate -n "$namespace" 2>/dev/null || print_message "INFO" "No certificates found"
    echo ""
    
    # Check certificate status
    local cert_name="${gateway_name}-cert"
    if kubectl get certificate "$cert_name" -n "$namespace" &>/dev/null; then
        check_certificate_status "$cert_name" "$namespace"
        get_certificate_expiry "$cert_name" "$namespace"
    fi
    echo ""
    
    print_message "INFO" "Services:"
    kubectl get service -n "$namespace" 2>/dev/null || print_message "INFO" "No services found"
    echo ""
    
    return 0
}

# Function to get status of all gateways
get_all_gateways_status() {
    if [ -z "$CONFIG_FILE" ]; then
        print_message "ERROR" "No configuration file loaded"
        return 1
    fi
    
    local gateway_names
    gateway_names=$(get_gateway_names)
    
    if [ -z "$gateway_names" ]; then
        print_message "WARN" "No gateways found in configuration"
        return 0
    fi
    
    while IFS= read -r gateway_name; do
        if is_gateway_enabled "$gateway_name"; then
            get_gateway_status "$gateway_name"
        fi
    done <<< "$gateway_names"
    
    return 0
}

# Function to export gateway configuration
export_gateway_config() {
    local gateway_name="$1"
    local output_file="$2"
    
    print_message "INFO" "Exporting configuration for gateway: $gateway_name"
    
    {
        generate_gateway_config "$gateway_name"
        generate_gateway_routes "$gateway_name"
    } > "$output_file"
    
    if [ -s "$output_file" ]; then
        print_message "SUCCESS" "Configuration exported to: $output_file"
        return 0
    else
        print_message "ERROR" "Failed to export configuration"
        return 1
    fi
}

# Function to export all gateway configurations
export_all_configs() {
    local output_dir="$1"
    
    if [ -z "$CONFIG_FILE" ]; then
        print_message "ERROR" "No configuration file loaded"
        return 1
    fi
    
    mkdir -p "$output_dir"
    
    local gateway_names
    gateway_names=$(get_gateway_names)
    
    if [ -z "$gateway_names" ]; then
        print_message "WARN" "No gateways found in configuration"
        return 0
    fi
    
    while IFS= read -r gateway_name; do
        if is_gateway_enabled "$gateway_name"; then
            local output_file="${output_dir}/${gateway_name}.yaml"
            export_gateway_config "$gateway_name" "$output_file"
        fi
    done <<< "$gateway_names"
    
    print_message "SUCCESS" "All configurations exported to: $output_dir"
    return 0
}
