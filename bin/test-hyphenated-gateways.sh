#!/bin/bash
# Test script for hyphenated gateway names

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the config library
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/lib/gateway-config.sh"

# Test configuration file
TEST_CONFIG="${SCRIPT_DIR}/../examples/rackspace-multi-gateway-config.yaml"

echo "Testing hyphenated gateway names fix"
echo "====================================="
echo ""

# Load configuration
echo "Loading configuration: $TEST_CONFIG"
if ! load_config "$TEST_CONFIG"; then
    echo "ERROR: Failed to load configuration"
    exit 1
fi
echo "✓ Configuration loaded"
echo ""

# Test get_gateway_names
echo "Testing get_gateway_names..."
gateway_names=$(get_gateway_names)
if [ $? -ne 0 ]; then
    echo "ERROR: get_gateway_names failed"
    exit 1
fi

if [ -z "$gateway_names" ]; then
    echo "ERROR: No gateway names returned"
    exit 1
fi

echo "✓ Gateway names retrieved:"
echo "$gateway_names" | while read -r name; do
    echo "  - $name"
done
echo ""

# Test each gateway with hyphenated names
echo "Testing hyphenated gateway name access..."
for gateway_name in rackspace-internal prometheus-internal grafana-internal longhorn-internal openstack-external; do
    echo "Testing gateway: $gateway_name"
    
    # Test is_gateway_enabled
    if is_gateway_enabled "$gateway_name"; then
        echo "  ✓ Enabled: true"
    else
        echo "  ✗ Enabled: false (UNEXPECTED)"
        exit 1
    fi
    
    # Test get_config_value with hyphenated key
    namespace=$(get_config_value "gateways.$gateway_name.namespace")
    if [ -z "$namespace" ]; then
        echo "  ✗ Failed to get namespace"
        exit 1
    fi
    echo "  ✓ Namespace: $namespace"
    
    gateway_type=$(get_config_value "gateways.$gateway_name.type")
    if [ -z "$gateway_type" ]; then
        echo "  ✗ Failed to get type"
        exit 1
    fi
    echo "  ✓ Type: $gateway_type"
    
    domain=$(get_config_value "gateways.$gateway_name.domain")
    if [ -z "$domain" ]; then
        echo "  ✗ Failed to get domain"
        exit 1
    fi
    echo "  ✓ Domain: $domain"
    
    echo ""
done

echo "====================================="
echo "All tests passed! ✓"
echo "====================================="
