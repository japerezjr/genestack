#!/bin/bash
# Script to detect and fix control characters in YAML files

if [ $# -eq 0 ]; then
    echo "Usage: $0 <yaml-file>"
    echo ""
    echo "This script detects and removes control characters from YAML files"
    echo "that can cause 'control characters are not allowed' errors in yq."
    exit 1
fi

YAML_FILE="$1"

if [ ! -f "$YAML_FILE" ]; then
    echo "ERROR: File not found: $YAML_FILE"
    exit 1
fi

echo "Checking for control characters in: $YAML_FILE"
echo ""

# Check for control characters (excluding tab, newline, carriage return)
if grep -P '[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]' "$YAML_FILE" > /dev/null 2>&1; then
    echo "⚠ Control characters detected!"
    echo ""
    echo "Showing lines with control characters:"
    grep -n -P '[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]' "$YAML_FILE" | head -10
    echo ""
    
    # Create backup
    BACKUP_FILE="${YAML_FILE}.backup.$(date +%Y%m%d-%H%M%S)"
    cp "$YAML_FILE" "$BACKUP_FILE"
    echo "✓ Created backup: $BACKUP_FILE"
    
    # Remove control characters (keep tab, newline, carriage return)
    # This uses tr to delete control characters except \t (tab), \n (newline), \r (carriage return)
    tr -d '\000-\010\013\014\016-\037\177' < "$YAML_FILE" > "${YAML_FILE}.tmp"
    mv "${YAML_FILE}.tmp" "$YAML_FILE"
    
    echo "✓ Removed control characters from: $YAML_FILE"
    echo ""
    echo "Testing with yq..."
    if yq eval '.gateways | keys' "$YAML_FILE" > /dev/null 2>&1; then
        echo "✓ File is now valid YAML"
    else
        echo "✗ File still has issues. Check yq output:"
        yq eval '.gateways | keys' "$YAML_FILE" 2>&1 | head -5
        echo ""
        echo "You can restore from backup: cp $BACKUP_FILE $YAML_FILE"
        exit 1
    fi
else
    echo "✓ No control characters detected"
    echo ""
    echo "Testing with yq..."
    if yq eval '.gateways | keys' "$YAML_FILE" > /dev/null 2>&1; then
        echo "✓ File is valid YAML"
    else
        echo "✗ File has other YAML syntax issues:"
        yq eval '.gateways | keys' "$YAML_FILE" 2>&1 | head -10
        exit 1
    fi
fi

echo ""
echo "File is ready to use!"
