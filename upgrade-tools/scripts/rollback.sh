#!/bin/bash
# Rollback Script
# Wrapper for initiating rollback to previous OpenStack version
# Requirements: 7.1-7.8

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPGRADE_TOOLS_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
NAMESPACE="${NAMESPACE:-openstack}"
OUTPUT_FILE=""
FORMAT="text"
DRY_RUN=false
IN_CLUSTER=false
VERBOSE=false
BACKUP_PATH="/var/backups/openstack"
FORCE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Trap for cleanup on interrupt
cleanup() {
    echo ""
    echo -e "${YELLOW}Rollback interrupted by user${NC}"
    echo "System may be in an inconsistent state"
    echo "Please review logs and contact support if needed"
    exit 130
}

trap cleanup SIGINT SIGTERM

# Usage information
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Rollback OpenStack to previous version after failed upgrade.

OPTIONS:
    -n, --namespace NAMESPACE    Kubernetes namespace (default: openstack)
    -o, --output FILE           Write rollback report to file
    -f, --format FORMAT         Output format: text, json, markdown (default: text)
    --dry-run                   Show what would be done without making changes
    --backup-path PATH          Path to backup directory (default: /var/backups/openstack)
    --in-cluster                Use in-cluster Kubernetes configuration
    --force                     Skip confirmation prompt
    -v, --verbose               Enable verbose output
    -h, --help                  Show this help message

EXAMPLES:
    # Rollback with confirmation
    $(basename "$0")
    
    # Dry-run to see what would be done
    $(basename "$0") --dry-run
    
    # Rollback with custom backup path
    $(basename "$0") --backup-path /custom/backup/path
    
    # Force rollback without confirmation
    $(basename "$0") --force
    
    # Save rollback report to file
    $(basename "$0") --output rollback-report.md --format markdown

EXIT CODES:
    0   - Rollback completed successfully
    1   - Rollback failed
    2   - Script error or invalid arguments
    130 - Rollback interrupted by user

NOTES:
    - Rollback restores from the most recent backup
    - All services will be reverted to previous versions
    - Database backups will be restored if schema changes occurred
    - Service health is verified after rollback
    - Use --dry-run to preview rollback actions

WARNING:
    Rollback is a critical operation. Ensure you understand the implications
    before proceeding. Review backup contents if uncertain.

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
        --backup-path)
            BACKUP_PATH="$2"
            shift 2
            ;;
        --in-cluster)
            IN_CLUSTER=true
            shift
            ;;
        --force)
            FORCE=true
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

# Check if backup path exists
if [[ ! -d "$BACKUP_PATH" ]] && [[ "$DRY_RUN" == "false" ]]; then
    echo -e "${RED}Error: Backup path does not exist: $BACKUP_PATH${NC}" >&2
    echo "Please verify the backup path and try again" >&2
    exit 2
fi

# Print header
if [[ "$VERBOSE" == "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
    echo "========================================================================"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}Rollback (DRY-RUN MODE)${NC}"
    else
        echo "Rollback to Previous Version"
    fi
    echo "========================================================================"
    echo "Namespace: $NAMESPACE"
    echo "Backup Path: $BACKUP_PATH"
    echo "Format: $FORMAT"
    echo ""
fi

# Warning for production
if [[ "$DRY_RUN" == "false" ]] && [[ "$FORCE" == "false" ]]; then
    echo -e "${YELLOW}WARNING: This will rollback OpenStack to the previous version${NC}"
    echo "This operation will:"
    echo "  - Restore previous helm chart versions"
    echo "  - Restore previous configurations"
    echo "  - Potentially restore database backups"
    echo "  - Restart all OpenStack services"
    echo ""
    echo "Current state will be lost if not backed up separately"
    echo ""
    read -p "Continue with rollback? (yes/no): " -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Rollback cancelled"
        exit 0
    fi
fi

# Build command
CMD="python3 -m cli --rollback --namespace $NAMESPACE --format $FORMAT"
CMD="$CMD --backup-path $BACKUP_PATH"

if [[ "$DRY_RUN" == "true" ]]; then
    CMD="$CMD --dry-run"
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

# Run rollback
if [[ "$VERBOSE" == "true" ]]; then
    echo "Running: $CMD"
    echo ""
fi

# Execute rollback
if eval "$CMD"; then
    EXIT_CODE=0
    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "${GREEN}✓ Dry-run completed successfully${NC}"
        echo "Review the output above to see what would be done"
        echo "Run without --dry-run to execute the rollback"
    else
        echo ""
        echo -e "${GREEN}✓ Rollback completed successfully${NC}"
        echo ""
        echo "OpenStack has been restored to the previous version"
        echo "Please verify service functionality"
    fi
else
    EXIT_CODE=$?
    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "${RED}✗ Dry-run failed${NC}"
    else
        echo ""
        echo -e "${RED}✗ Rollback failed${NC}"
        echo ""
        echo "System may be in an inconsistent state"
        echo "Please review logs and contact support"
        echo ""
        echo "Manual recovery steps may be required:"
        echo "  1. Check pod status: kubectl get pods -n $NAMESPACE"
        echo "  2. Review logs: kubectl logs -n $NAMESPACE <pod-name>"
        echo "  3. Check helm releases: helm list -n $NAMESPACE"
        echo "  4. Verify backup integrity in: $BACKUP_PATH"
    fi
fi

# Print output file location if specified
if [[ -n "$OUTPUT_FILE" ]] && [[ "$VERBOSE" == "true" ]]; then
    echo ""
    echo "Rollback report written to: $OUTPUT_FILE"
fi

exit $EXIT_CODE
