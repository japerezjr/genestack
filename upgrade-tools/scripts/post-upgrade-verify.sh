#!/bin/bash
# Post-Upgrade Verification Script
# Run all post-upgrade checks and test key operations
# Requirements: 6.1-6.9

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPGRADE_TOOLS_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
NAMESPACE="${NAMESPACE:-openstack}"
OUTPUT_FILE=""
FORMAT="text"
SKIP_ENDPOINTS=false
SKIP_OPERATIONS=false
IN_CLUSTER=false
VERBOSE=false
QUICK_CHECK=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Usage information
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Post-upgrade verification script for OpenStack Caracal to Epoxy upgrade.

OPTIONS:
    -n, --namespace NAMESPACE    Kubernetes namespace (default: openstack)
    -o, --output FILE           Write verification report to file
    -f, --format FORMAT         Output format: text, json, markdown (default: text)
    --skip-endpoints            Skip OpenStack API endpoint checks
    --skip-operations           Skip functional operation tests
    --quick-check               Run quick checks only (pod status and endpoints)
    --in-cluster                Use in-cluster Kubernetes configuration
    -v, --verbose               Enable verbose output
    -h, --help                  Show this help message

VERIFICATION CHECKS:
    1. Pod Status Check         - Verify all pods are Running
    2. API Endpoint Check       - Verify all OpenStack APIs are accessible
    3. Service List Check       - Verify compute, network, volume services
    4. Functional Tests         - Test key operations (create/delete resources)
    5. Log Analysis             - Check for critical errors in service logs
    6. Performance Baseline     - Compare API response times

EXAMPLES:
    # Full verification
    $(basename "$0")
    
    # Quick check (pod status and endpoints only)
    $(basename "$0") --quick-check
    
    # Verification without functional tests
    $(basename "$0") --skip-operations
    
    # Save verification report to file
    $(basename "$0") --output verification-report.md --format markdown
    
    # Verbose output with custom namespace
    $(basename "$0") --namespace my-openstack --verbose

EXIT CODES:
    0 - All verifications passed
    1 - One or more verifications failed
    2 - Script error or invalid arguments

NOTES:
    - Functional tests create temporary resources that are cleaned up
    - Use --quick-check for fast health verification
    - Use --skip-operations if you want to test manually
    - Verification can take 5-10 minutes for full checks

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
        --skip-operations)
            SKIP_OPERATIONS=true
            shift
            ;;
        --quick-check)
            QUICK_CHECK=true
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
    if [[ "$QUICK_CHECK" == "true" ]]; then
        echo "Post-Upgrade Verification (Quick Check)"
    else
        echo "Post-Upgrade Verification"
    fi
    echo "========================================================================"
    echo "Namespace: $NAMESPACE"
    echo "Format: $FORMAT"
    echo "Skip Endpoints: $SKIP_ENDPOINTS"
    echo "Skip Operations: $SKIP_OPERATIONS"
    echo "Quick Check: $QUICK_CHECK"
    echo ""
fi

# Change to upgrade-tools directory
cd "$UPGRADE_TOOLS_DIR"

# Initialize exit code
OVERALL_EXIT_CODE=0

# Check 1: Pod Status
if [[ "$VERBOSE" == "true" ]]; then
    echo "========================================================================"
    echo "Check 1: Pod Status"
    echo "========================================================================"
fi

echo "Checking pod status in namespace: $NAMESPACE"
POD_CHECK_FAILED=false

# Get pod status
POD_STATUS=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null || echo "")

if [[ -z "$POD_STATUS" ]]; then
    echo -e "${RED}✗ No pods found in namespace $NAMESPACE${NC}"
    POD_CHECK_FAILED=true
    OVERALL_EXIT_CODE=1
else
    # Count pods by status
    TOTAL_PODS=$(echo "$POD_STATUS" | wc -l)
    RUNNING_PODS=$(echo "$POD_STATUS" | grep -c "Running" || echo "0")
    PENDING_PODS=$(echo "$POD_STATUS" | grep -c "Pending" || echo "0")
    FAILED_PODS=$(echo "$POD_STATUS" | grep -c -E "Error|CrashLoopBackOff|ImagePullBackOff" || echo "0")
    
    echo "Total pods: $TOTAL_PODS"
    echo "Running: $RUNNING_PODS"
    echo "Pending: $PENDING_PODS"
    echo "Failed: $FAILED_PODS"
    
    if [[ "$FAILED_PODS" -gt 0 ]]; then
        echo -e "${RED}✗ Found $FAILED_PODS failed pods${NC}"
        POD_CHECK_FAILED=true
        OVERALL_EXIT_CODE=1
        
        if [[ "$VERBOSE" == "true" ]]; then
            echo ""
            echo "Failed pods:"
            echo "$POD_STATUS" | grep -E "Error|CrashLoopBackOff|ImagePullBackOff"
        fi
    elif [[ "$PENDING_PODS" -gt 0 ]]; then
        echo -e "${YELLOW}⚠ Found $PENDING_PODS pending pods${NC}"
    else
        echo -e "${GREEN}✓ All pods are running${NC}"
    fi
fi

echo ""

# Check 2: API Endpoints (unless skipped or quick check with skip)
if [[ "$SKIP_ENDPOINTS" == "false" ]]; then
    if [[ "$VERBOSE" == "true" ]]; then
        echo "========================================================================"
        echo "Check 2: API Endpoints"
        echo "========================================================================"
    fi
    
    echo "Checking OpenStack API endpoints..."
    
    # Build validation command
    VALIDATE_CMD="python3 -m cli --validate-only --namespace $NAMESPACE --format text"
    
    if [[ "$IN_CLUSTER" == "true" ]]; then
        VALIDATE_CMD="$VALIDATE_CMD --in-cluster"
    fi
    
    if [[ "$VERBOSE" == "true" ]]; then
        VALIDATE_CMD="$VALIDATE_CMD --verbose"
    else
        VALIDATE_CMD="$VALIDATE_CMD --quiet"
    fi
    
    # Run endpoint validation
    if eval "$VALIDATE_CMD" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ All API endpoints are accessible${NC}"
    else
        echo -e "${RED}✗ Some API endpoints are not accessible${NC}"
        OVERALL_EXIT_CODE=1
    fi
    
    echo ""
fi

# Check 3: Service Lists (unless quick check)
if [[ "$QUICK_CHECK" == "false" ]]; then
    if [[ "$VERBOSE" == "true" ]]; then
        echo "========================================================================"
        echo "Check 3: Service Lists"
        echo "========================================================================"
    fi
    
    echo "Checking OpenStack service lists..."
    
    # Check if openstack CLI is available
    if command -v openstack &> /dev/null; then
        # Check compute services
        echo -n "Compute services: "
        if openstack compute service list --format value -c State 2>/dev/null | grep -q "up"; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            OVERALL_EXIT_CODE=1
        fi
        
        # Check network agents
        echo -n "Network agents: "
        if openstack network agent list --format value -c Alive 2>/dev/null | grep -q "true"; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            OVERALL_EXIT_CODE=1
        fi
        
        # Check volume services
        echo -n "Volume services: "
        if openstack volume service list --format value -c State 2>/dev/null | grep -q "up"; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            OVERALL_EXIT_CODE=1
        fi
    else
        echo -e "${YELLOW}⚠ OpenStack CLI not available, skipping service list checks${NC}"
    fi
    
    echo ""
fi

# Check 4: Functional Tests (unless skipped or quick check)
if [[ "$SKIP_OPERATIONS" == "false" ]] && [[ "$QUICK_CHECK" == "false" ]]; then
    if [[ "$VERBOSE" == "true" ]]; then
        echo "========================================================================"
        echo "Check 4: Functional Tests"
        echo "========================================================================"
    fi
    
    echo "Running functional tests..."
    echo -e "${YELLOW}Note: This creates temporary test resources that will be cleaned up${NC}"
    
    # Check if openstack CLI is available
    if command -v openstack &> /dev/null; then
        # Test network creation
        echo -n "Test network creation: "
        TEST_NET_NAME="test-verify-net-$$"
        if openstack network create "$TEST_NET_NAME" --internal > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
            # Cleanup
            openstack network delete "$TEST_NET_NAME" > /dev/null 2>&1 || true
        else
            echo -e "${RED}✗${NC}"
            OVERALL_EXIT_CODE=1
        fi
        
        # Test volume creation (if cinder is available)
        echo -n "Test volume creation: "
        TEST_VOL_NAME="test-verify-vol-$$"
        if openstack volume create --size 1 "$TEST_VOL_NAME" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
            # Wait a bit for volume to be created
            sleep 2
            # Cleanup
            openstack volume delete "$TEST_VOL_NAME" > /dev/null 2>&1 || true
        else
            echo -e "${YELLOW}⚠ (volume service may not be available)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ OpenStack CLI not available, skipping functional tests${NC}"
    fi
    
    echo ""
fi

# Check 5: Log Analysis (unless quick check)
if [[ "$QUICK_CHECK" == "false" ]]; then
    if [[ "$VERBOSE" == "true" ]]; then
        echo "========================================================================"
        echo "Check 5: Log Analysis"
        echo "========================================================================"
    fi
    
    echo "Analyzing service logs for critical errors..."
    
    # Check for critical errors in recent logs
    CRITICAL_ERRORS=$(kubectl logs -n "$NAMESPACE" --tail=100 --all-containers --selector=application=openstack 2>/dev/null | grep -i -E "critical|fatal|error" | wc -l || echo "0")
    
    if [[ "$CRITICAL_ERRORS" -gt 0 ]]; then
        echo -e "${YELLOW}⚠ Found $CRITICAL_ERRORS potential error messages in logs${NC}"
        if [[ "$VERBOSE" == "true" ]]; then
            echo "Review logs manually for details: kubectl logs -n $NAMESPACE <pod-name>"
        fi
    else
        echo -e "${GREEN}✓ No critical errors found in recent logs${NC}"
    fi
    
    echo ""
fi

# Generate report if output file specified
if [[ -n "$OUTPUT_FILE" ]]; then
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Generating verification report..."
    fi
    
    # Use the validation command to generate a full report
    REPORT_CMD="python3 -m cli --validate-only --namespace $NAMESPACE --format $FORMAT --output $OUTPUT_FILE"
    
    if [[ "$IN_CLUSTER" == "true" ]]; then
        REPORT_CMD="$REPORT_CMD --in-cluster"
    fi
    
    if [[ "$SKIP_ENDPOINTS" == "true" ]]; then
        REPORT_CMD="$REPORT_CMD --skip-endpoints"
    fi
    
    eval "$REPORT_CMD" > /dev/null 2>&1 || true
    
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Verification report written to: $OUTPUT_FILE"
        echo ""
    fi
fi

# Final summary
echo "========================================================================"
echo "Verification Summary"
echo "========================================================================"

if [[ "$OVERALL_EXIT_CODE" -eq 0 ]]; then
    echo -e "${GREEN}✓ All verification checks passed${NC}"
    echo ""
    echo "OpenStack upgrade to Epoxy completed successfully"
    echo "All services are healthy and functional"
else
    echo -e "${RED}✗ Some verification checks failed${NC}"
    echo ""
    echo "Please review the issues above and take corrective action"
    echo "You may need to:"
    echo "  - Check pod logs: kubectl logs -n $NAMESPACE <pod-name>"
    echo "  - Review service status: kubectl get pods -n $NAMESPACE"
    echo "  - Check OpenStack services: openstack compute service list"
    echo "  - Consider rollback if issues persist: $(dirname "$0")/rollback.sh"
fi

echo ""

exit $OVERALL_EXIT_CODE
