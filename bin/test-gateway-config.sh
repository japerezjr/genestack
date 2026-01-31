#!/bin/bash
# shellcheck disable=SC2034

# Gateway Configuration Test Script
# Tests configuration parsing, validation, and resource generation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/lib"

# Source required libraries
# shellcheck source=/dev/null
source "${LIB_DIR}/gateway-config.sh"
# shellcheck source=/dev/null
source "${LIB_DIR}/gateway-validator.sh"
# shellcheck source=/dev/null
source "${LIB_DIR}/gateway-generator.sh"
# shellcheck source=/dev/null
source "${LIB_DIR}/gateway-utils.sh"
# shellcheck source=/dev/null
source "${LIB_DIR}/gateway-certificates.sh"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test result tracking
declare -a FAILED_TESTS

# Function to run a test
run_test() {
    local test_name="$1"
    local test_function="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    echo ""
    echo "=========================================="
    echo "Test $TESTS_RUN: $test_name"
    echo "=========================================="
    
    if $test_function; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "✓ PASSED: $test_name"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        FAILED_TESTS+=("$test_name")
        echo "✗ FAILED: $test_name"
    fi
}

# Test 1: Check required commands
test_required_commands() {
    echo "Checking required commands..."
    
    local required_commands=("yq" "kubectl")
    local missing=0
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            echo "ERROR: Required command not found: $cmd"
            missing=1
        else
            echo "✓ Found: $cmd"
        fi
    done
    
    return $missing
}

# Test 2: Configuration file parsing
test_config_parsing() {
    echo "Testing configuration file parsing..."
    
    local test_config="${SCRIPT_DIR}/../examples/multi-gateway-config.yaml"
    # Adjust path if running from bin/lib
    if [[ "$SCRIPT_DIR" == *"/lib" ]]; then
        test_config="${SCRIPT_DIR}/../../examples/multi-gateway-config.yaml"
    fi
    
    if [ ! -f "$test_config" ]; then
        echo "ERROR: Test configuration file not found: $test_config"
        return 1
    fi
    
    # Load configuration
    CONFIG_FILE="$test_config"
    
    # Test getting gateway names
    local gateway_names
    gateway_names=$(get_gateway_names)
    
    if [ -z "$gateway_names" ]; then
        echo "ERROR: Failed to get gateway names"
        return 1
    fi
    
    echo "✓ Found gateways: $gateway_names"
    
    # Test getting gateway configuration
    local namespace
    namespace=$(get_config_value "gateways.external.namespace")
    
    if [ -z "$namespace" ]; then
        echo "ERROR: Failed to get gateway namespace"
        return 1
    fi
    
    echo "✓ Gateway namespace: $namespace"
    
    return 0
}

# Test 3: Configuration validation
test_config_validation() {
    echo "Testing configuration validation..."
    
    local test_config="${SCRIPT_DIR}/../examples/multi-gateway-config.yaml"
    # Adjust path if running from bin/lib
    if [[ "$SCRIPT_DIR" == *"/lib" ]]; then
        test_config="${SCRIPT_DIR}/../../examples/multi-gateway-config.yaml"
    fi
    
    if [ ! -f "$test_config" ]; then
        echo "ERROR: Test configuration file not found: $test_config"
        return 1
    fi
    
    # Validate configuration
    if validate_config "$test_config"; then
        echo "✓ Configuration validation passed"
        return 0
    else
        echo "ERROR: Configuration validation failed"
        return 1
    fi
}

# Test 4: Gateway name validation
test_gateway_name_validation() {
    echo "Testing gateway name validation..."
    
    local valid_names=("external" "internal" "my-gateway" "gateway-1")
    local invalid_names=("External" "my_gateway" "gateway@1" "-gateway" "gateway-")
    
    local failed=0
    
    for name in "${valid_names[@]}"; do
        if validate_gateway_name "$name"; then
            echo "✓ Valid name accepted: $name"
        else
            echo "ERROR: Valid name rejected: $name"
            failed=1
        fi
    done
    
    for name in "${invalid_names[@]}"; do
        if validate_gateway_name "$name"; then
            echo "ERROR: Invalid name accepted: $name"
            failed=1
        else
            echo "✓ Invalid name rejected: $name"
        fi
    done
    
    return $failed
}

# Test 5: Namespace name validation
test_namespace_validation() {
    echo "Testing namespace name validation..."
    
    local valid_names=("envoy-gateway-external" "default" "my-namespace")
    local invalid_names=("Envoy-Gateway" "my_namespace" "namespace@1")
    
    local failed=0
    
    for name in "${valid_names[@]}"; do
        if validate_namespace_name "$name"; then
            echo "✓ Valid namespace accepted: $name"
        else
            echo "ERROR: Valid namespace rejected: $name"
            failed=1
        fi
    done
    
    for name in "${invalid_names[@]}"; do
        if validate_namespace_name "$name"; then
            echo "ERROR: Invalid namespace accepted: $name"
            failed=1
        else
            echo "✓ Invalid namespace rejected: $name"
        fi
    done
    
    return $failed
}

# Test 6: Gateway type validation
test_gateway_type_validation() {
    echo "Testing gateway type validation..."
    
    local valid_types=("external" "internal" "hybrid")
    local invalid_types=("External" "public" "private" "")
    
    local failed=0
    
    for type in "${valid_types[@]}"; do
        if validate_gateway_type "$type"; then
            echo "✓ Valid type accepted: $type"
        else
            echo "ERROR: Valid type rejected: $type"
            failed=1
        fi
    done
    
    for type in "${invalid_types[@]}"; do
        if validate_gateway_type "$type"; then
            echo "ERROR: Invalid type accepted: $type"
            failed=1
        else
            echo "✓ Invalid type rejected: $type"
        fi
    done
    
    return $failed
}

# Test 7: Domain validation
test_domain_validation() {
    echo "Testing domain validation..."
    
    local valid_domains=("example.com" "api.example.com" "my-domain.co.uk")
    local invalid_domains=("" "invalid domain" "domain@example" "-example.com")
    
    local failed=0
    
    for domain in "${valid_domains[@]}"; do
        if validate_domain "$domain"; then
            echo "✓ Valid domain accepted: $domain"
        else
            echo "ERROR: Valid domain rejected: $domain"
            failed=1
        fi
    done
    
    for domain in "${invalid_domains[@]}"; do
        if validate_domain "$domain"; then
            echo "ERROR: Invalid domain accepted: $domain"
            failed=1
        else
            echo "✓ Invalid domain rejected: $domain"
        fi
    done
    
    return $failed
}

# Test 8: Certificate provider validation
test_cert_provider_validation() {
    echo "Testing certificate provider validation..."
    
    local valid_providers=("letsencrypt" "self-signed" "custom")
    local invalid_providers=("LetsEncrypt" "selfsigned" "unknown" "")
    
    local failed=0
    
    for provider in "${valid_providers[@]}"; do
        if validate_certificate_provider "$provider"; then
            echo "✓ Valid provider accepted: $provider"
        else
            echo "ERROR: Valid provider rejected: $provider"
            failed=1
        fi
    done
    
    for provider in "${invalid_providers[@]}"; do
        if validate_certificate_provider "$provider"; then
            echo "ERROR: Invalid provider accepted: $provider"
            failed=1
        else
            echo "✓ Invalid provider rejected: $provider"
        fi
    done
    
    return $failed
}

# Test 9: DNS provider validation
test_dns_provider_validation() {
    echo "Testing DNS provider validation..."
    
    local valid_providers=("cloudflare" "route53" "azuredns" "google" "digitalocean" "godaddy" "rackspace" "acmedns" "rfc2136")
    local invalid_providers=("Cloudflare" "aws" "azure" "gcp" "unknown" "")
    
    local failed=0
    
    for provider in "${valid_providers[@]}"; do
        if validate_dns_provider "$provider"; then
            echo "✓ Valid DNS provider accepted: $provider"
        else
            echo "ERROR: Valid DNS provider rejected: $provider"
            failed=1
        fi
    done
    
    for provider in "${invalid_providers[@]}"; do
        if validate_dns_provider "$provider"; then
            echo "ERROR: Invalid DNS provider accepted: $provider"
            failed=1
        else
            echo "✓ Invalid DNS provider rejected: $provider"
        fi
    done
    
    return $failed
}

# Test 10: Resource generation
test_resource_generation() {
    echo "Testing resource generation..."
    
    local test_config="${SCRIPT_DIR}/../examples/multi-gateway-config.yaml"
    # Adjust path if running from bin/lib
    if [[ "$SCRIPT_DIR" == *"/lib" ]]; then
        test_config="${SCRIPT_DIR}/../../examples/multi-gateway-config.yaml"
    fi
    
    if [ ! -f "$test_config" ]; then
        echo "ERROR: Test configuration file not found: $test_config"
        return 1
    fi
    
    CONFIG_FILE="$test_config"
    
    # Test namespace generation
    local namespace_yaml
    namespace_yaml=$(generate_namespace "test-namespace" "test-gateway")
    
    if [ -z "$namespace_yaml" ]; then
        echo "ERROR: Failed to generate namespace"
        return 1
    fi
    
    echo "✓ Namespace generation successful"
    
    # Test gateway class generation
    local gatewayclass_yaml
    gatewayclass_yaml=$(generate_gateway_class "eg")
    
    if [ -z "$gatewayclass_yaml" ]; then
        echo "ERROR: Failed to generate gateway class"
        return 1
    fi
    
    echo "✓ Gateway class generation successful"
    
    # Test gateway generation
    local gateway_yaml
    gateway_yaml=$(generate_gateway "test-gateway" "test-namespace" "eg" "external")
    
    if [ -z "$gateway_yaml" ]; then
        echo "ERROR: Failed to generate gateway"
        return 1
    fi
    
    echo "✓ Gateway generation successful"
    
    return 0
}

# Main test execution
main() {
    echo "=========================================="
    echo "Gateway Configuration Test Suite"
    echo "=========================================="
    echo ""
    
    # Run all tests
    run_test "Required Commands Check" test_required_commands
    run_test "Configuration File Parsing" test_config_parsing
    run_test "Configuration Validation" test_config_validation
    run_test "Gateway Name Validation" test_gateway_name_validation
    run_test "Namespace Name Validation" test_namespace_validation
    run_test "Gateway Type Validation" test_gateway_type_validation
    run_test "Domain Validation" test_domain_validation
    run_test "Certificate Provider Validation" test_cert_provider_validation
    run_test "DNS Provider Validation" test_dns_provider_validation
    run_test "Resource Generation" test_resource_generation
    
    # Print summary
    echo ""
    echo "=========================================="
    echo "Test Summary"
    echo "=========================================="
    echo "Total tests run: $TESTS_RUN"
    echo "Tests passed: $TESTS_PASSED"
    echo "Tests failed: $TESTS_FAILED"
    
    if [ $TESTS_FAILED -gt 0 ]; then
        echo ""
        echo "Failed tests:"
        for test in "${FAILED_TESTS[@]}"; do
            echo "  - $test"
        done
        echo ""
        exit 1
    else
        echo ""
        echo "✓ All tests passed!"
        echo ""
        exit 0
    fi
}

# Run main function
main "$@"
