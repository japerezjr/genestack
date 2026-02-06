#!/bin/bash
# Temporary workaround to fix chart versions to 2025.1
# This should be done by the version updater but it's not working

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSIONS_FILE="$SCRIPT_DIR/../helm-chart-versions.yaml"

echo "Fixing chart versions in $VERSIONS_FILE"
echo "Replacing 2024.2 with 2025.1..."

# Backup original file
cp "$VERSIONS_FILE" "$VERSIONS_FILE.backup"

# Replace 2024.2 with 2025.1 for OpenStack services
sed -i.tmp 's/2024\.2\./2025.1./g' "$VERSIONS_FILE"
rm -f "$VERSIONS_FILE.tmp"

echo "✓ Chart versions updated"
echo "Backup saved to: $VERSIONS_FILE.backup"
echo ""
echo "Updated versions:"
grep -E "keystone|nova|glance|neutron|cinder|placement" "$VERSIONS_FILE" | head -10
