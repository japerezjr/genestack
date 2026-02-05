#!/bin/bash
# Upgrade Execution Script
# Wrapper for running full OpenStack Caracal to Epoxy upgrade
# Requirements: 5.1-5.9

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPGRADE_TOOLS_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
NAMESPACE="${NAMESPACE:-openstack}"
OUTPUT_FILE=""
FORMAT="text"
DRY_RUN=false
SKIP_OPTIONAL=false
SKIP_PRE_VALIDATION=false
SKIP_POST_VALIDATION=false
SKIP_ENDPOINTS=false
IN_CLUSTER=false
VERBOSE=false
TIMEOUT=600
NO_HALT_ON_FAILURE=false
SERVICES=""
SOURCE_RELEASE="2024.2"
TARGET_RELEASE="2025.1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Trap for cleanup on interrupt
cleanup() {
    echo ""
    echo -e "${YELLOW}Upgrade interrupted by user${NC}"
    echo "Current state has been preserved"
    echo "You can rollback using: $(basename "$0" | sed 's/upgrade-execute/rollback/')"
    exit 130
}

trap cleanup SIGINT SIGTERM

# Usage information
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Execute OpenStack Caracal to Epoxy upgrade.

OPTIONS:
    -n, --namespace NAMESPACE    Kubernetes namespace (default: openstack)
    -o, --output FILE           Write upgrade report to file
    -f, --format FORMAT         Output format: text, json, markdown (default: text)
    --dry-run                   Show what would be changed without making changes
    --skip-optional             Skip optional services (only upgrade core services)
    --skip-pre-validation       Skip pre-upgrade validation (not recommended)
    --skip-post-validation      Skip post-upgrade validation
    --skip-endpoints            Skip OpenStack API endpoint checks
    --in-cluster                Use in-cluster Kubernetes configuration
    --timeout SECONDS           Timeout per service in seconds (default: 600)
    --no-halt-on-failure        Continue upgrade even if a service fails
    --services SERVICE...       Specific services to upgrade (space-separated)
    --source-release VERSION    Source OpenStack release (default: 2024.2)
    --target-release VERSION    Target OpenStack release (default: 2025.1)
    -v, --verbose               Enable verbose output
    -h, --help                  Show this help message

EXAMPLES:
    # Dry-run to see what would be changed
    $(basename "$0") --dry-run
    
    # Full upgrade with default settings
    $(basename "$0")
    
    # Upgrade only core services
    $(basename "$0") --skip-optional
    
    # Upgrade specific services
    $(basename "$0") --services keystone glance nova
    
    # Upgrade with custom timeout
    $(basename "$0") --timeout 900
    
    # Save upgrade report to file
    $(basename "$0") --output upgrade-report.md --format markdown

EXIT CODES:
    0   - Upgrade completed successfully
    1   - Upgrade failed
    2   - Script error or invalid arguments
    130 - Upgrade interrupted by user

NOTES:
    - Pre-upgrade validation is strongly recommended
    - A backup is automatically created before upgrade
    - Use --dry-run to preview changes before executing
    - Upgrade can be interrupted with Ctrl+C
    - Use rollback.sh if upgrade fails

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
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-optional)
            SKIP_OPTIONAL=true
            shift
            ;;
        --skip-pre-validation)
            SKIP_PRE_VALIDATION=true
            shift
            ;;
        --skip-post-validation)
            SKIP_POST_VALIDATION=true
            shift
            ;;
        --skip-endpoints)
            SKIP_ENDPOINTS=true
            shift
            ;;
        --in-cluster)
            IN_CLUSTER=true
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --no-halt-on-failure)
            NO_HALT_ON_FAILURE=true
            shift
            ;;
        --services)
            shift
            while [[ $# -gt 0 ]] && [[ ! "$1" =~ ^- ]]; do
                SERVICES="$SERVICES $1"
                shift
            done
            ;;
        --source-release)
            SOURCE_RELEASE="$2"
            shift 2
            ;;
        --target-release)
            TARGET_RELEASE="$2"
            shift 2
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

# Validate timeout
if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}Error: Invalid timeout '$TIMEOUT'. Must be a positive integer${NC}" >&2
    exit 2
fi

# Print header
if [[ "$VERBOSE" == "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
    echo "========================================================================"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}Upgrade Execution (DRY-RUN MODE)${NC}"
    else
        echo "Upgrade Execution"
    fi
    echo "========================================================================"
    echo "Namespace: $NAMESPACE"
    echo "Source Release: $SOURCE_RELEASE"
    echo "Target Release: $TARGET_RELEASE"
    echo "Format: $FORMAT"
    echo "Timeout per service: ${TIMEOUT}s"
    echo "Skip Optional: $SKIP_OPTIONAL"
    echo "Skip Pre-Validation: $SKIP_PRE_VALIDATION"
    echo "Skip Post-Validation: $SKIP_POST_VALIDATION"
    if [[ -n "$SERVICES" ]]; then
        echo "Services:$SERVICES"
    fi
    echo ""
fi

# Warning for production
if [[ "$DRY_RUN" == "false" ]] && [[ "$SKIP_PRE_VALIDATION" == "false" ]]; then
    echo -e "${YELLOW}WARNING: This will upgrade OpenStack from $SOURCE_RELEASE to $TARGET_RELEASE${NC}"
    echo "A backup will be created automatically before upgrade"
    echo ""
    read -p "Continue with upgrade? (yes/no): " -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Upgrade cancelled"
        exit 0
    fi
fi

# Build command
CMD="python3 -m cli --namespace $NAMESPACE --format $FORMAT --timeout $TIMEOUT"
CMD="$CMD --source-release $SOURCE_RELEASE --target-release $TARGET_RELEASE"

if [[ "$DRY_RUN" == "true" ]]; then
    CMD="$CMD --dry-run"
fi

if [[ "$SKIP_OPTIONAL" == "true" ]]; then
    CMD="$CMD --skip-optional"
fi

if [[ "$SKIP_PRE_VALIDATION" == "true" ]]; then
    CMD="$CMD --skip-pre-validation"
fi

if [[ "$SKIP_POST_VALIDATION" == "true" ]]; then
    CMD="$CMD --skip-post-validation"
fi

if [[ "$SKIP_ENDPOINTS" == "true" ]]; then
    CMD="$CMD --skip-endpoints"
fi

if [[ "$IN_CLUSTER" == "true" ]]; then
    CMD="$CMD --in-cluster"
fi

if [[ "$NO_HALT_ON_FAILURE" == "true" ]]; then
    CMD="$CMD --no-halt-on-failure"
fi

if [[ "$VERBOSE" == "true" ]]; then
    CMD="$CMD --verbose"
fi

if [[ -n "$OUTPUT_FILE" ]]; then
    CMD="$CMD --output $OUTPUT_FILE"
fi

if [[ -n "$SERVICES" ]]; then
    CMD="$CMD --services$SERVICES"
fi

# Change to upgrade-tools directory
cd "$UPGRADE_TOOLS_DIR"

# Run upgrade
if [[ "$VERBOSE" == "true" ]]; then
    echo "Running: $CMD"
    echo ""
fi

# Execute upgrade
if eval "$CMD"; then
    EXIT_CODE=0
    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "${GREEN}✓ Dry-run completed successfully${NC}"
        echo "Review the output above to see what would be changed"
        echo "Run without --dry-run to execute the upgrade"
    else
        echo ""
        echo -e "${GREEN}✓ Upgrade completed successfully${NC}"
    fi
else
    EXIT_CODE=$?
    if [[ $EXIT_CODE -eq 130 ]]; then
        # User cancelled
        echo ""
        echo -e "${YELLOW}Upgrade cancelled by user${NC}"
    elif [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "${RED}✗ Dry-run failed${NC}"
    else
        echo ""
        echo -e "${RED}✗ Upgrade failed${NC}"
        echo ""
        echo "You can rollback using: $(dirname "$0")/rollback.sh"
    fi
fi

# Print output file location if specified
if [[ -n "$OUTPUT_FILE" ]] && [[ "$VERBOSE" == "true" ]]; then
    echo ""
    echo "Upgrade report written to: $OUTPUT_FILE"
fi

exit $EXIT_CODE
