#!/bin/bash
# shellcheck disable=SC2034

# Gateway Configuration Validator
# Validates configuration schema and required fields

# Source the config library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/gateway-config.sh"

# Array to store validation errors
declare -a VALIDATION_ERRORS=()

# Function to add a validation error
add_error() {
    local error_message="$1"
    VALIDATION_ERRORS+=("$error_message")
}

# Function to validate gateway name
validate_gateway_name() {
    local gateway_name="$1"
    
    if [ -z "$gateway_name" ]; then
        add_error "Gateway name cannot be empty"
        return 1
    fi
    
    # Must start and end with alphanumeric, can contain hyphens in the middle
    if ! [[ "$gateway_name" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
        add_error "Gateway name '$gateway_name' contains invalid characters (must be lowercase alphanumeric, can contain hyphens but not at start/end)"
        return 1
    fi
    
    if [ ${#gateway_name} -gt 63 ]; then
        add_error "Gateway name '$gateway_name' exceeds maximum length of 63 characters"
        return 1
    fi
    
    return 0
}

# Function to validate namespace name
validate_namespace_name() {
    local namespace="$1"
    
    if [ -z "$namespace" ]; then
        add_error "Namespace cannot be empty"
        return 1
    fi
    
    if ! [[ "$namespace" =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])?$ ]]; then
        add_error "Namespace '$namespace' is not a valid Kubernetes namespace name"
        return 1
    fi
    
    if [ ${#namespace} -gt 63 ]; then
        add_error "Namespace '$namespace' exceeds maximum length of 63 characters"
        return 1
    fi
    
    return 0
}

# Function to validate gateway type
validate_gateway_type() {
    local gateway_type="$1"
    
    case "$gateway_type" in
        external|internal|hybrid)
            return 0
            ;;
        *)
            add_error "Invalid gateway type '$gateway_type' (must be: external, internal, or hybrid)"
            return 1
            ;;
    esac
}

# Function to validate domain
validate_domain() {
    local domain="$1"
    
    if [ -z "$domain" ]; then
        add_error "Domain cannot be empty"
        return 1
    fi
    
    # Basic domain validation (allows wildcards and subdomains)
    if ! [[ "$domain" =~ ^(\*\.)?([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$ ]] && [ "$domain" != "cluster.local" ]; then
        add_error "Domain '$domain' is not a valid domain name"
        return 1
    fi
    
    return 0
}

# Function to validate certificate provider
validate_certificate_provider() {
    local provider="$1"
    
    case "$provider" in
        letsencrypt|self-signed|custom)
            return 0
            ;;
        *)
            add_error "Invalid certificate provider '$provider' (must be: letsencrypt, self-signed, or custom)"
            return 1
            ;;
    esac
}

# Function to validate ACME challenge method
validate_acme_challenge() {
    local challenge="$1"
    
    case "$challenge" in
        http01|dns01)
            return 0
            ;;
        *)
            add_error "Invalid ACME challenge method '$challenge' (must be: http01 or dns01)"
            return 1
            ;;
    esac
}

# Function to validate DNS provider
validate_dns_provider() {
    local provider="$1"
    
    case "$provider" in
        cloudflare|route53|azuredns|google|digitalocean|acmedns|rfc2136|godaddy|rackspace)
            return 0
            ;;
        *)
            add_error "Invalid DNS provider '$provider'"
            return 1
            ;;
    esac
}

# Function to validate gateway configuration
validate_gateway() {
    local gateway_name="$1"
    
    echo "Validating gateway: $gateway_name"
    
    # Validate gateway name
    validate_gateway_name "$gateway_name" || return 1
    
    # Get gateway configuration
    local namespace
    local gateway_type
    local domain
    local cert_provider
    local acme_challenge
    local dns_provider
    
    namespace=$(get_config_value "gateways.$gateway_name.namespace" "")
    gateway_type=$(get_config_value "gateways.$gateway_name.type" "")
    domain=$(get_config_value "gateways.$gateway_name.domain" "")
    cert_provider=$(get_config_value "gateways.$gateway_name.certificate.provider" "")
    acme_challenge=$(get_config_value "gateways.$gateway_name.certificate.acme_challenge" "http01")
    dns_provider=$(get_config_value "gateways.$gateway_name.certificate.dns_provider" "")
    
    # Validate required fields
    if [ -z "$namespace" ]; then
        add_error "Gateway '$gateway_name': namespace is required"
        return 1
    fi
    
    if [ -z "$gateway_type" ]; then
        add_error "Gateway '$gateway_name': type is required"
        return 1
    fi
    
    if [ -z "$domain" ]; then
        add_error "Gateway '$gateway_name': domain is required"
        return 1
    fi
    
    # Validate namespace
    validate_namespace_name "$namespace" || return 1
    
    # Validate gateway type
    validate_gateway_type "$gateway_type" || return 1
    
    # Validate domain
    validate_domain "$domain" || return 1
    
    # Validate certificate provider
    if [ -n "$cert_provider" ]; then
        validate_certificate_provider "$cert_provider" || return 1
    fi
    
    # Validate ACME challenge if using letsencrypt
    if [ "$cert_provider" = "letsencrypt" ]; then
        validate_acme_challenge "$acme_challenge" || return 1
        
        if [ "$acme_challenge" = "dns01" ] && [ -z "$dns_provider" ]; then
            add_error "Gateway '$gateway_name': dns_provider is required when using dns01 challenge"
            return 1
        fi
        
        if [ -n "$dns_provider" ]; then
            validate_dns_provider "$dns_provider" || return 1
        fi
    fi
    
    return 0
}

# Function to validate all gateways
validate_all_gateways() {
    local gateway_names
    gateway_names=$(get_gateway_names)
    
    local has_errors=0
    
    while IFS= read -r gateway_name; do
        if is_gateway_enabled "$gateway_name"; then
            if ! validate_gateway "$gateway_name"; then
                has_errors=1
            fi
        fi
    done <<< "$gateway_names"
    
    return $has_errors
}

# Function to validate configuration file
validate_config() {
    local config_file="$1"
    
    echo "Validating configuration file: $config_file"
    echo ""
    
    # Load configuration
    if ! load_config "$config_file"; then
        return 1
    fi
    
    # Check if yq is available
    if ! check_yq; then
        return 1
    fi
    
    # Validate all gateways
    if ! validate_all_gateways; then
        echo ""
        echo "Validation failed with errors:"
        for error in "${VALIDATION_ERRORS[@]}"; do
            echo "  - $error"
        done
        return 1
    fi
    
    echo "Configuration validation passed!"
    return 0
}

# Function to print validation errors
print_validation_errors() {
    if [ ${#VALIDATION_ERRORS[@]} -eq 0 ]; then
        echo "No validation errors"
        return 0
    fi
    
    echo "Validation Errors:"
    for error in "${VALIDATION_ERRORS[@]}"; do
        echo "  - $error"
    done
    
    return 1
}

# Function to clear validation errors
clear_validation_errors() {
    VALIDATION_ERRORS=()
}
