#!/bin/bash
# Integration Testing Checklist Script
# This script helps guide through the integration testing process

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results file
RESULTS_FILE="${SCRIPT_DIR}/../integration-test-results.txt"

function print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

function print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

function print_error() {
    echo -e "${RED}✗ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

function print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

function prompt_continue() {
    echo -e "\n${YELLOW}Press Enter to continue or Ctrl+C to exit...${NC}"
    read -r
}

function record_result() {
    local phase="$1"
    local status="$2"
    local details="$3"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Phase: $phase | Status: $status | Details: $details" >> "$RESULTS_FILE"
}

function check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local all_good=true
    
    # Check if environment file exists
    if [ -f ~/lab-env.sh ]; then
        print_success "Environment file found: ~/lab-env.sh"
    else
        print_error "Environment file not found: ~/lab-env.sh"
        print_info "Create it using the template in docs/LAB_ENVIRONMENT_SETUP.md"
        all_good=false
    fi
    
    # Check if OpenStack CLI is available
    if command -v openstack &> /dev/null; then
        print_success "OpenStack CLI is installed"
    else
        print_error "OpenStack CLI not found"
        print_info "Install with: pip install python-openstackclient"
        all_good=false
    fi
    
    # Check if kubectl is available
    if command -v kubectl &> /dev/null; then
        print_success "kubectl is installed"
    else
        print_error "kubectl not found"
        print_info "Install kubectl: https://kubernetes.io/docs/tasks/tools/"
        all_good=false
    fi
    
    # Check if in correct directory
    if [ -f "${PROJECT_ROOT}/scripts/hyperconverged-lab.sh" ]; then
        print_success "Genestack repository found"
    else
        print_error "Not in Genestack repository"
        print_info "Clone repository to /opt/genestack"
        all_good=false
    fi
    
    if [ "$all_good" = true ]; then
        print_success "All prerequisites met"
        record_result "Prerequisites" "PASS" "All checks passed"
        return 0
    else
        print_error "Some prerequisites not met"
        record_result "Prerequisites" "FAIL" "Missing requirements"
        return 1
    fi
}


function phase1_lab_deployment() {
    print_header "Phase 1: Lab Deployment (Subtask 15.1)"
    
    print_info "This phase deploys a fresh lab environment with Caracal"
    print_info "Expected duration: 20-30 minutes"
    
    echo -e "\n${YELLOW}Steps to complete:${NC}"
    echo "1. Source environment variables: source ~/lab-env.sh"
    echo "2. Verify OpenStack connectivity"
    echo "3. Deploy lab: cd ${PROJECT_ROOT} && ./scripts/hyperconverged-lab.sh kubespray -x"
    echo "4. Wait for deployment to complete"
    echo "5. Document lab IP and SSH access"
    echo "6. SSH into lab and verify deployment"
    
    prompt_continue
    
    print_info "Checking if environment variables are set..."
    if [ -z "$ACME_EMAIL" ] || [ -z "$GATEWAY_DOMAIN" ] || [ -z "$OS_CLOUD" ]; then
        print_warning "Environment variables not set. Run: source ~/lab-env.sh"
    else
        print_success "Environment variables are set"
    fi
    
    echo -e "\n${YELLOW}Have you completed the lab deployment? (yes/no)${NC}"
    read -r response
    
    if [ "$response" = "yes" ]; then
        echo -e "\n${YELLOW}Enter the Jump Host IP:${NC}"
        read -r jump_host_ip
        
        echo -e "\n${YELLOW}Did all pods reach Running state? (yes/no)${NC}"
        read -r pods_running
        
        echo -e "\n${YELLOW}Are all OpenStack services healthy? (yes/no)${NC}"
        read -r services_healthy
        
        if [ "$pods_running" = "yes" ] && [ "$services_healthy" = "yes" ]; then
            print_success "Phase 1 completed successfully"
            record_result "Phase 1: Lab Deployment" "PASS" "Jump Host: $jump_host_ip"
            echo "$jump_host_ip" > "${SCRIPT_DIR}/../lab-ip.txt"
            return 0
        else
            print_error "Phase 1 has issues"
            record_result "Phase 1: Lab Deployment" "FAIL" "Pods or services not healthy"
            return 1
        fi
    else
        print_warning "Phase 1 not completed"
        record_result "Phase 1: Lab Deployment" "SKIP" "User skipped"
        return 1
    fi
}

function phase2_pre_upgrade_validation() {
    print_header "Phase 2: Pre-Upgrade Validation Testing (Subtask 15.2)"
    
    print_info "This phase tests the pre-upgrade validation script"
    
    echo -e "\n${YELLOW}Steps to complete:${NC}"
    echo "1. SSH into lab environment"
    echo "2. Run: cd /opt/genestack/upgrade-tools && ./scripts/pre-upgrade-validate.sh"
    echo "3. Review validation report"
    echo "4. Test failure scenario: kubectl scale deployment -n openstack keystone-api --replicas=0"
    echo "5. Run validation again (should fail)"
    echo "6. Restore service: kubectl scale deployment -n openstack keystone-api --replicas=3"
    echo "7. Run validation again (should pass)"
    
    prompt_continue
    
    echo -e "\n${YELLOW}Did initial validation pass all checks? (yes/no)${NC}"
    read -r initial_pass
    
    echo -e "\n${YELLOW}Did validation detect the stopped service? (yes/no)${NC}"
    read -r failure_detected
    
    echo -e "\n${YELLOW}Did validation pass after service restoration? (yes/no)${NC}"
    read -r restored_pass
    
    if [ "$initial_pass" = "yes" ] && [ "$failure_detected" = "yes" ] && [ "$restored_pass" = "yes" ]; then
        print_success "Phase 2 completed successfully"
        record_result "Phase 2: Pre-Upgrade Validation" "PASS" "All validation tests passed"
        return 0
    else
        print_error "Phase 2 has issues"
        record_result "Phase 2: Pre-Upgrade Validation" "FAIL" "Some validation tests failed"
        return 1
    fi
}

function phase3_upgrade_execution() {
    print_header "Phase 3: Upgrade Execution Testing (Subtask 15.3)"
    
    print_info "This phase tests the complete upgrade process"
    print_warning "This will upgrade the lab from Caracal to Epoxy"
    
    echo -e "\n${YELLOW}Steps to complete:${NC}"
    echo "1. SSH into lab environment"
    echo "2. Create baseline snapshot"
    echo "3. Run dry-run: cd /opt/genestack/upgrade-tools && ./openstack-upgrade upgrade --dry-run"
    echo "4. Review planned changes"
    echo "5. Run actual upgrade: ./scripts/upgrade-execute.sh"
    echo "6. Monitor progress in another terminal"
    echo "7. Wait for upgrade to complete"
    echo "8. Verify all services upgraded successfully"
    
    prompt_continue
    
    echo -e "\n${YELLOW}Did dry-run show planned changes without applying them? (yes/no)${NC}"
    read -r dryrun_ok
    
    echo -e "\n${YELLOW}Did the actual upgrade complete successfully? (yes/no)${NC}"
    read -r upgrade_complete
    
    echo -e "\n${YELLOW}Are all pods in Running state after upgrade? (yes/no)${NC}"
    read -r pods_running
    
    echo -e "\n${YELLOW}Are all services reporting as healthy? (yes/no)${NC}"
    read -r services_healthy
    
    echo -e "\n${YELLOW}Enter upgrade duration in minutes:${NC}"
    read -r duration
    
    if [ "$dryrun_ok" = "yes" ] && [ "$upgrade_complete" = "yes" ] && [ "$pods_running" = "yes" ] && [ "$services_healthy" = "yes" ]; then
        print_success "Phase 3 completed successfully"
        record_result "Phase 3: Upgrade Execution" "PASS" "Duration: ${duration} minutes"
        return 0
    else
        print_error "Phase 3 has issues"
        record_result "Phase 3: Upgrade Execution" "FAIL" "Upgrade did not complete successfully"
        return 1
    fi
}

function phase4_post_upgrade_verification() {
    print_header "Phase 4: Post-Upgrade Verification Testing (Subtask 15.4)"
    
    print_info "This phase verifies all OpenStack functionality after upgrade"
    
    echo -e "\n${YELLOW}Steps to complete:${NC}"
    echo "1. SSH into lab environment"
    echo "2. Run: cd /opt/genestack/upgrade-tools && ./scripts/post-upgrade-verify.sh"
    echo "3. Test image operations"
    echo "4. Test network operations"
    echo "5. Test compute operations (create instance)"
    echo "6. Test volume operations (create and attach volume)"
    echo "7. Clean up test resources"
    echo "8. Verify service versions"
    
    prompt_continue
    
    echo -e "\n${YELLOW}Did post-upgrade verification pass all checks? (yes/no)${NC}"
    read -r verification_pass
    
    echo -e "\n${YELLOW}Did image operations work correctly? (yes/no)${NC}"
    read -r image_ok
    
    echo -e "\n${YELLOW}Did network creation succeed? (yes/no)${NC}"
    read -r network_ok
    
    echo -e "\n${YELLOW}Did instance creation succeed? (yes/no)${NC}"
    read -r instance_ok
    
    echo -e "\n${YELLOW}Did volume creation and attachment succeed? (yes/no)${NC}"
    read -r volume_ok
    
    if [ "$verification_pass" = "yes" ] && [ "$image_ok" = "yes" ] && [ "$network_ok" = "yes" ] && [ "$instance_ok" = "yes" ] && [ "$volume_ok" = "yes" ]; then
        print_success "Phase 4 completed successfully"
        record_result "Phase 4: Post-Upgrade Verification" "PASS" "All functional tests passed"
        return 0
    else
        print_error "Phase 4 has issues"
        record_result "Phase 4: Post-Upgrade Verification" "FAIL" "Some functional tests failed"
        return 1
    fi
}

function phase5_rollback_testing() {
    print_header "Phase 5: Rollback Testing (Subtask 15.5)"
    
    print_info "This phase tests the rollback functionality"
    print_warning "This requires deploying a fresh lab environment"
    
    echo -e "\n${YELLOW}Steps to complete:${NC}"
    echo "1. Clean up existing lab: cd ${PROJECT_ROOT} && ./scripts/hyperconverged-lab-kubespray-uninstall.sh"
    echo "2. Deploy fresh lab: source ~/lab-env.sh && ./scripts/hyperconverged-lab.sh kubespray -x"
    echo "3. SSH into lab and create backup"
    echo "4. Start upgrade (let it complete or interrupt mid-process)"
    echo "5. Initiate rollback: cd /opt/genestack/upgrade-tools && ./scripts/rollback.sh"
    echo "6. Monitor rollback progress"
    echo "7. Verify system restored to Caracal"
    echo "8. Test service functionality after rollback"
    
    prompt_continue
    
    echo -e "\n${YELLOW}Did you deploy a fresh lab for rollback testing? (yes/no)${NC}"
    read -r fresh_lab
    
    if [ "$fresh_lab" != "yes" ]; then
        print_warning "Phase 5 skipped - fresh lab not deployed"
        record_result "Phase 5: Rollback Testing" "SKIP" "Fresh lab not deployed"
        return 1
    fi
    
    echo -e "\n${YELLOW}Did rollback execute successfully? (yes/no)${NC}"
    read -r rollback_ok
    
    echo -e "\n${YELLOW}Were chart versions restored to Caracal? (yes/no)${NC}"
    read -r versions_restored
    
    echo -e "\n${YELLOW}Are all services operational after rollback? (yes/no)${NC}"
    read -r services_ok
    
    echo -e "\n${YELLOW}Do basic operations work after rollback? (yes/no)${NC}"
    read -r operations_ok
    
    if [ "$rollback_ok" = "yes" ] && [ "$versions_restored" = "yes" ] && [ "$services_ok" = "yes" ] && [ "$operations_ok" = "yes" ]; then
        print_success "Phase 5 completed successfully"
        record_result "Phase 5: Rollback Testing" "PASS" "Rollback successful"
        return 0
    else
        print_error "Phase 5 has issues"
        record_result "Phase 5: Rollback Testing" "FAIL" "Rollback did not complete successfully"
        return 1
    fi
}

function generate_summary() {
    print_header "Integration Testing Summary"
    
    if [ -f "$RESULTS_FILE" ]; then
        echo -e "\n${BLUE}Test Results:${NC}"
        cat "$RESULTS_FILE"
        
        local pass_count=$(grep -c "PASS" "$RESULTS_FILE" || true)
        local fail_count=$(grep -c "FAIL" "$RESULTS_FILE" || true)
        local skip_count=$(grep -c "SKIP" "$RESULTS_FILE" || true)
        
        echo -e "\n${BLUE}Summary:${NC}"
        echo -e "${GREEN}Passed: $pass_count${NC}"
        echo -e "${RED}Failed: $fail_count${NC}"
        echo -e "${YELLOW}Skipped: $skip_count${NC}"
        
        if [ "$fail_count" -eq 0 ] && [ "$pass_count" -gt 0 ]; then
            print_success "All integration tests passed!"
            echo -e "\n${GREEN}The upgrade process is ready for production deployment.${NC}"
        else
            print_warning "Some tests failed or were skipped"
            echo -e "\n${YELLOW}Review the issues and retest before production deployment.${NC}"
        fi
    else
        print_warning "No test results found"
    fi
}

function main() {
    echo -e "${BLUE}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║   OpenStack Caracal to Epoxy Upgrade                      ║
║   Integration Testing Checklist                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    print_info "This script guides you through the integration testing process"
    print_info "Results will be saved to: $RESULTS_FILE"
    
    # Initialize results file
    echo "Integration Testing Results - $(date)" > "$RESULTS_FILE"
    echo "========================================" >> "$RESULTS_FILE"
    
    # Check prerequisites
    if ! check_prerequisites; then
        print_error "Prerequisites not met. Please fix the issues and try again."
        exit 1
    fi
    
    prompt_continue
    
    # Run test phases
    phase1_lab_deployment
    phase2_pre_upgrade_validation
    phase3_upgrade_execution
    phase4_post_upgrade_verification
    phase5_rollback_testing
    
    # Generate summary
    generate_summary
    
    print_info "Integration testing checklist complete"
    print_info "Review the results in: $RESULTS_FILE"
}

# Run main function
main "$@"
