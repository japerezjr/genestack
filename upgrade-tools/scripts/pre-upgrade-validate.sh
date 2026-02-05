#!/bin/bash
# Pre-Upgrade Validation Script
# Wrapper for running validation checks before OpenStack upgrade
# Requirements: 4.1-4.9

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPGRADE_TOOLS_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
NAMESPACE="${NAMESPACE:-openstack}"
OUTPUT_FILE=""
FORMAT="text"
SKIP_ENDPOINTS=false
IN_CLUSTER=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Usage information
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Pre-upgrade validation script for OpenStack Caracal to Epoxy upgrade.

OPTIONS:
    -n, --namespace NAMESPACE    Kubernetes namespace (default: openstack)
    -o, --output FILE           Write report to file instead of stdout
    -f, --format FORMAT         Output format: text, json, markdown (default: text)
    --skip-endpoints            Skip OpenStack API endpoint checks
    --in-cluster                Use in-cluster Kubernetes configuration
    -v, --verbose               Enable verbose output
    -h, --help                  Show this help message

EXAMPLES:
    # Basic validation
    $(basename "$0")
    
    # Validation with custom namespace
    $(basename "$0") --namespace my-openstack
    
    # Save validation report to file
    $(basename "$0") --output validation-report.md --format markdown
    
    # Skip endpoint checks (useful if APIs are down)
    $(basename "$0") --skip-endpoints

EXIT CODES:
    0 - All validations passed
    1 - One or more validations failed
    2 - Script error or invalid arguments

EOF
    exit 0
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        --skip-endpoints)
            SKIP_ENDPOINTS=true
            shift
            ;;
        --in-cluster)
            IN_CLUSTER=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}" >&2
            echo "Use --help for usage information" >&2
            exit 2
            ;;
    esac
done

# Validate format
if [[ ! "$FORMAT" =~ ^(text|json|markdown)$ ]]; then
    echo -e "${RED}Error: Invalid format '$FORMAT'. Must be text, json, or markdown${NC}" >&2
    exit 2
fi

# Print header
if [[ "$VERBOSE" == "true" ]]; then
    echo "========================================================================"
    echo "Pre-Upgrade Validation"
    echo "========================================================================"
    echo "Namespace: $NAMESPACE"
    echo "Format: $FORMAT"
    echo "Skip Endpoints: $SKIP_ENDPOINTS"
    echo "In-Cluster: $IN_CLUSTER"
    echo ""
fi

# Build command
CMD="python3 -m cli --validate-only --namespace $NAMESPACE --format $FORMAT"

if [[ "$SKIP_ENDPOINTS" == "true" ]]; then
    CMD="$CMD --skip-endpoints"
fi

if [[ "$IN_CLUSTER" == "true" ]]; then
    CMD="$CMD --in-cluster"
fi

if [[ "$VERBOSE" == "true" ]]; then
    CMD="$CMD --verbose"
fi

if [[ -n "$OUTPUT_FILE" ]]; then
    CMD="$CMD --output $OUTPUT_FILE"
fi

# Change to upgrade-tools directory
cd "$UPGRADE_TOOLS_DIR"

# Run validation
if [[ "$VERBOSE" == "true" ]]; then
    echo "Running: $CMD"
    echo ""
fi

# Execute validation
if eval "$CMD"; then
    EXIT_CODE=0
    if [[ "$VERBOSE" == "true" ]]; then
        echo ""
        echo -e "${GREEN}✓ Pre-upgrade validation passed${NC}"
    fi
else
    EXIT_CODE=$?
    if [[ "$VERBOSE" == "true" ]]; then
        echo ""
        echo -e "${RED}✗ Pre-upgrade validation failed${NC}"
    fi
fi

# Print output file location if specified
if [[ -n "$OUTPUT_FILE" ]] && [[ "$VERBOSE" == "true" ]]; then
    echo ""
    echo "Validation report written to: $OUTPUT_FILE"
fi

exit $EXIT_CODE
