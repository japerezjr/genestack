#!/bin/bash
# Unit test for build_yq_path function

# Source the function
build_yq_path() {
    local path="$1"
    
    # Ensure path starts with a dot for yq v4 compatibility
    if [[ ! "$path" =~ ^\. ]]; then
        path=".$path"
    fi
    
    # Split path by dots and rebuild with bracket notation for hyphenated keys
    local result=""
    local IFS='.'
    local parts=($path)
    
    for part in "${parts[@]}"; do
        if [ -z "$part" ]; then
            continue
        fi
        
        # If part contains a hyphen, use bracket notation
        if [[ "$part" =~ - ]]; then
            result="${result}[\"${part}\"]"
        else
            # Use dot notation for non-hyphenated keys
            if [ -z "$result" ]; then
                result=".${part}"
            else
                result="${result}.${part}"
            fi
        fi
    done
    
    echo "$result"
}

# Test cases
echo "Testing build_yq_path function"
echo "==============================="
echo ""

test_case() {
    local input="$1"
    local expected="$2"
    local result
    result=$(build_yq_path "$input")
    
    if [ "$result" = "$expected" ]; then
        echo "✓ PASS: '$input' -> '$result'"
    else
        echo "✗ FAIL: '$input'"
        echo "  Expected: '$expected'"
        echo "  Got:      '$result'"
        exit 1
    fi
}

# Test cases
test_case "gateways.external.enabled" ".gateways.external.enabled"
test_case "gateways.rackspace-internal.enabled" ".gateways[\"rackspace-internal\"].enabled"
test_case "gateways.prometheus-internal.namespace" ".gateways[\"prometheus-internal\"].namespace"
test_case "gateways.openstack-external.certificate.provider" ".gateways[\"openstack-external\"].certificate.provider"
test_case ".gateways.longhorn-internal.domain" ".gateways[\"longhorn-internal\"].domain"
test_case "global.namespace_isolation" ".global.namespace_isolation"

echo ""
echo "==============================="
echo "All tests passed! ✓"
