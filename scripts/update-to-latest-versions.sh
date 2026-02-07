#!/bin/bash
# Update helm-chart-versions.yaml to latest 2025.1 versions from helm repo
# This queries the actual helm repository instead of just replacing version strings

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_VERSIONS_FILE="$SCRIPT_DIR/../helm-chart-versions.yaml"
SYSTEM_VERSIONS_FILE="/etc/genestack/helm-chart-versions.yaml"

echo "Updating chart versions to latest 2025.1 from helm repository..."
echo ""

# OpenStack services to update
SERVICES=(
    "barbican" "blazar" "ceilometer" "cinder" "cloudkitty" "freezer"
    "glance" "gnocchi" "heat" "horizon" "ironic" "keystone" "libvirt"
    "magnum" "manila" "masakari" "neutron" "nova" "octavia" "placement"
    "trove" "zaqar"
)

# Function to get latest 2025.1 version for a service
get_latest_version() {
    local service=$1
    helm search repo openstack-helm/$service --versions 2>/dev/null | \
        grep "2025.1" | head -1 | awk '{print $2}'
}

# Update repo file
if [ -f "$REPO_VERSIONS_FILE" ]; then
    echo "Updating: $REPO_VERSIONS_FILE"
    cp "$REPO_VERSIONS_FILE" "$REPO_VERSIONS_FILE.backup"
    
    for service in "${SERVICES[@]}"; do
        latest=$(get_latest_version "$service")
        if [ -n "$latest" ]; then
            echo "  $service: $latest"
            # Use sed with proper escaping for YAML
            sed -i "s/^  ${service}: .*$/  ${service}: ${latest}/" "$REPO_VERSIONS_FILE"
        else
            echo "  $service: no 2025.1 version found, skipping"
        fi
    done
    
    echo "✓ Repo file updated (backup: $REPO_VERSIONS_FILE.backup)"
else
    echo "⚠ Repo file not found: $REPO_VERSIONS_FILE"
fi

echo ""

# Update system file
if [ -f "$SYSTEM_VERSIONS_FILE" ]; then
    echo "Updating: $SYSTEM_VERSIONS_FILE"
    sudo cp "$SYSTEM_VERSIONS_FILE" "$SYSTEM_VERSIONS_FILE.backup"
    
    for service in "${SERVICES[@]}"; do
        latest=$(get_latest_version "$service")
        if [ -n "$latest" ]; then
            sudo sed -i "s/^  ${service}: .*$/  ${service}: ${latest}/" "$SYSTEM_VERSIONS_FILE"
        fi
    done
    
    echo "✓ System file updated (backup: $SYSTEM_VERSIONS_FILE.backup)"
else
    echo "⚠ System file not found: $SYSTEM_VERSIONS_FILE"
fi

echo ""
echo "Updated versions (from system file):"
grep -E "keystone|nova|glance|neutron|cinder|placement|libvirt" "$SYSTEM_VERSIONS_FILE" 2>/dev/null | head -10 || echo "Could not read system file"
