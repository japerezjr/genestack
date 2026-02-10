#!/bin/bash
# shellcheck disable=SC2034,SC2155

# Gateway Configuration Parsing Library
# Handles YAML configuration file parsing and environment variable substitution

# Function to check if yq is installed
check_yq() {
    if ! command -v yq &> /dev/null; then
        echo "ERROR: yq is required but not installed"
        echo "Please install yq: https://github.com/mikefarah/yq"
        return 1
    fi
    return 0
}

# Function to substitute environment variables in a string
# Usage: substitute_env_vars "string with ${VAR_NAME}"
substitute_env_vars() {
    local string="$1"
    local result="$string"
    
    # Find all ${VAR_NAME} patterns and substitute them
    while [[ $result =~ \$\{([A-Za-z_][A-Za-z0-9_]*)\} ]]; do
        local var_name="${BASH_REMATCH[1]}"
        local var_value="${!var_name:-}"
        
        if [ -z "$var_value" ]; then
            echo "WARNING: Environment variable '$var_name' is not set" >&2
        fi
        
        result="${result//\$\{$var_name\}/$var_value}"
    done
    
    echo "$result"
}

# Function to load configuration from YAML file
# Usage: load_config "config.yaml"
load_config() {
    local config_file="$1"
    
    if [ ! -f "$config_file" ]; then
        echo "ERROR: Configuration file not found: $config_file" >&2
        return 1
    fi
    
    # Check if file is readable
    if [ ! -r "$config_file" ]; then
        echo "ERROR: Configuration file is not readable: $config_file" >&2
        return 1
    fi
    
    # Store the config file path for later use
    CONFIG_FILE="$config_file"
    
    return 0
}

# Function to get a value from the configuration
# Usage: get_config_value "gateways.external.domain"
get_config_value() {
    local path="$1"
    local default="${2:-}"
    
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    local value
    value=$(yq eval "$path" "$CONFIG_FILE" 2>/dev/null)
    
    if [ -z "$value" ] || [ "$value" = "null" ]; then
        if [ -n "$default" ]; then
            echo "$default"
        fi
        return 1
    fi
    
    # Substitute environment variables
    substitute_env_vars "$value"
    return 0
}

# Function to get all gateway names
# Usage: get_gateway_names
get_gateway_names() {
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    yq eval '.gateways | keys | .[]' "$CONFIG_FILE" 2>/dev/null
}

# Function to check if a gateway is enabled
# Usage: is_gateway_enabled "external"
is_gateway_enabled() {
    local gateway_name="$1"
    local enabled
    
    enabled=$(get_config_value "gateways.$gateway_name.enabled" "false")
    
    # Debug output (can be removed later)
    if [ "${DEBUG:-false}" = "true" ]; then
        echo "[DEBUG] Gateway: $gateway_name, enabled value: '$enabled'" >&2
    fi
    
    # Handle both boolean and string values, and trim whitespace
    enabled=$(echo "$enabled" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
    
    if [ "$enabled" = "true" ]; then
        return 0
    fi
    return 1
}

# Function to get gateway configuration
# Usage: get_gateway_config "external"
get_gateway_config() {
    local gateway_name="$1"
    
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    yq eval ".gateways.$gateway_name" "$CONFIG_FILE" 2>/dev/null
}

# Function to get all routes for a gateway
# Usage: get_gateway_routes "external"
get_gateway_routes() {
    local gateway_name="$1"
    
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    yq eval ".gateways.$gateway_name.routes | length" "$CONFIG_FILE" 2>/dev/null
}

# Function to get a specific route for a gateway
# Usage: get_gateway_route "external" 0
get_gateway_route() {
    local gateway_name="$1"
    local route_index="$2"
    
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    yq eval ".gateways.$gateway_name.routes[$route_index]" "$CONFIG_FILE" 2>/dev/null
}

# Function to get all listeners for a gateway
# Usage: get_gateway_listeners "external"
get_gateway_listeners() {
    local gateway_name="$1"
    
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    yq eval ".gateways.$gateway_name.listeners | length" "$CONFIG_FILE" 2>/dev/null
}

# Function to get a specific listener for a gateway
# Usage: get_gateway_listener "external" 0
get_gateway_listener() {
    local gateway_name="$1"
    local listener_index="$2"
    
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    yq eval ".gateways.$gateway_name.listeners[$listener_index]" "$CONFIG_FILE" 2>/dev/null
}

# Function to get global configuration
# Usage: get_global_config "legacy_mode"
get_global_config() {
    local key="$1"
    local default="${2:-}"
    
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    local value
    value=$(yq eval ".global.$key" "$CONFIG_FILE" 2>/dev/null)
    
    if [ -z "$value" ] || [ "$value" = "null" ]; then
        if [ -n "$default" ]; then
            echo "$default"
        fi
        return 1
    fi
    
    substitute_env_vars "$value"
    return 0
}

# Function to get DNS provider configuration
# Usage: get_dns_provider_config "cloudflare"
get_dns_provider_config() {
    local provider_name="$1"
    
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    yq eval ".dns_providers.$provider_name" "$CONFIG_FILE" 2>/dev/null
}

# Function to get all DNS provider names
# Usage: get_dns_provider_names
get_dns_provider_names() {
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    yq eval '.dns_providers | keys | .[]' "$CONFIG_FILE" 2>/dev/null
}

# Function to check if configuration is in legacy mode
# Usage: is_legacy_mode
is_legacy_mode() {
    local legacy_mode
    legacy_mode=$(get_global_config "legacy_mode" "false")
    
    if [ "$legacy_mode" = "true" ]; then
        return 0
    fi
    return 1
}

# Function to check if namespace isolation is enabled
# Usage: is_namespace_isolation_enabled
is_namespace_isolation_enabled() {
    local isolation
    isolation=$(get_global_config "namespace_isolation" "true")
    
    if [ "$isolation" = "true" ]; then
        return 0
    fi
    return 1
}

# Function to check if auto routes are enabled
# Usage: is_auto_routes_enabled
is_auto_routes_enabled() {
    local auto_routes
    auto_routes=$(get_global_config "auto_routes" "true")
    
    if [ "$auto_routes" = "true" ]; then
        return 0
    fi
    return 1
}

# Function to check if auto listeners are enabled
# Usage: is_auto_listeners_enabled
is_auto_listeners_enabled() {
    local auto_listeners
    auto_listeners=$(get_global_config "auto_listeners" "true")
    
    if [ "$auto_listeners" = "true" ]; then
        return 0
    fi
    return 1
}

# Function to print configuration summary
# Usage: print_config_summary
print_config_summary() {
    if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: No configuration file loaded" >&2
        return 1
    fi
    
    echo "Configuration Summary:"
    echo "====================="
    echo "Config File: $CONFIG_FILE"
    echo ""
    
    echo "Global Settings:"
    echo "  Legacy Mode: $(get_global_config 'legacy_mode' 'false')"
    echo "  Namespace Isolation: $(get_global_config 'namespace_isolation' 'true')"
    echo "  Auto Routes: $(get_global_config 'auto_routes' 'true')"
    echo "  Auto Listeners: $(get_global_config 'auto_listeners' 'true')"
    echo ""
    
    echo "Gateways:"
    local gateway_names
    gateway_names=$(get_gateway_names)
    
    while IFS= read -r gateway_name; do
        if is_gateway_enabled "$gateway_name"; then
            local namespace
            local gateway_type
            local domain
            
            namespace=$(get_config_value "gateways.$gateway_name.namespace" "N/A")
            gateway_type=$(get_config_value "gateways.$gateway_name.type" "N/A")
            domain=$(get_config_value "gateways.$gateway_name.domain" "N/A")
            
            echo "  - $gateway_name (enabled)"
            echo "    Type: $gateway_type"
            echo "    Namespace: $namespace"
            echo "    Domain: $domain"
        fi
    done <<< "$gateway_names"
    
    return 0
}
