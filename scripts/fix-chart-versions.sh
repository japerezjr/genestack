#!/bin/bash
# Temporary workaround to fix chart versions to 2025.1
# This should be done by the version updater but it's not working

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_VERSIONS_FILE="$SCRIPT_DIR/../helm-chart-versions.yaml"
SYSTEM_VERSIONS_FILE="/etc/genestack/helm-chart-versions.yaml"

echo "Fixing chart versions (replacing 2024.2 with 2025.1)..."
echo ""

# Fix repo file
if [ -f "$REPO_VERSIONS_FILE" ]; then
    echo "Updating: $REPO_VERSIONS_FILE"
    cp "$REPO_VERSIONS_FILE" "$REPO_VERSIONS_FILE.backup"
    sed -i.tmp 's/2024\.2\./2025.1./g' "$REPO_VERSIONS_FILE"
    rm -f "$REPO_VERSIONS_FILE.tmp"
    echo "✓ Repo file updated (backup: $REPO_VERSIONS_FILE.backup)"
else
    echo "⚠ Repo file not found: $REPO_VERSIONS_FILE"
fi

echo ""

# Fix system file (used by install scripts)
if [ -f "$SYSTEM_VERSIONS_FILE" ]; then
    echo "Updating: $SYSTEM_VERSIONS_FILE"
    sudo cp "$SYSTEM_VERSIONS_FILE" "$SYSTEM_VERSIONS_FILE.backup"
    sudo sed -i 's/2024\.2\./2025.1./g' "$SYSTEM_VERSIONS_FILE"
    echo "✓ System file updated (backup: $SYSTEM_VERSIONS_FILE.backup)"
else
    echo "⚠ System file not found: $SYSTEM_VERSIONS_FILE"
fi

echo ""
echo "Updated versions (from system file):"
grep -E "keystone|nova|glance|neutron|cinder|placement" "$SYSTEM_VERSIONS_FILE" 2>/dev/null | head -10 || echo "Could not read system file"
