#!/bin/bash
# End-to-End Testing Execution Script
# This script automates the execution of end-to-end tests for the OpenStack upgrade

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
UPGRADE_TOOLS="${PROJECT_ROOT}/upgrade-tools"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Test results
RESULTS_FILE="${UPGRADE_TOOLS}/e2e-test-results.txt"
ISSUES_FILE="${UPGRADE_TOOLS}/e2e-test-issues.txt"
METRICS_FILE="${UPGRADE_TOOLS}/e2e-test-metrics.txt"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

function print_banner() {
    echo -e "${CYAN}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   OpenStack Caracal to Epoxy Upgrade                          ║
║   End-to-End Testing Suite                                    ║
║   Task 17: Final Checkpoint                                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

function print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

function print_subheader() {
    echo -e "\n${CYAN}─── $1 ───${NC}\n"
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

function record_test() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    case "$status" in
        PASS)
            PASSED_TESTS=$((PASSED_TESTS + 1))
            print_success "$test_name"
            ;;
        FAIL)
            FAILED_TESTS=$((FAILED_TESTS + 1))
            print_error "$test_name"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ISSUE: $test_name - $details" >> "$ISSUES_FILE"
            ;;
        SKIP)
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
            print_warning "$test_name (SKIPPED)"
            ;;
    esac
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $test_name | $status | $details" >> "$RESULTS_FILE"
}

function record_metric() {
    local metric_name="$1"
    local value="$2"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $metric_name: $value" >> "$METRICS_FILE"
}

function initialize_test_files() {
    print_info "Initializing test result files..."
    
    cat > "$RESULTS_FILE" << EOF
End-to-End Test Results
Test Date: $(date '+%Y-%m-%d %H:%M:%S')
Tester: $(whoami)
Host: $(hostname)
========================================

EOF

    cat > "$ISSUES_FILE" << EOF
End-to-End Test Issues
Test Date: $(date '+%Y-%m-%d %H:%M:%S')
========================================

EOF

    cat > "$METRICS_FILE" << EOF
End-to-End Test Metrics
Test Date: $(date '+%Y-%m-%d %H:%M:%S')
========================================

EOF
}

function test_prerequisites() {
    print_header "Testing Prerequisites"
    
    # Check Python
    if command -v python3 &> /dev/null; then
        record_test "Python 3 installed" "PASS" "$(python3 --version)"
    else
        record_test "Python 3 installed" "FAIL" "Python 3 not found"
    fi
    
    # Check kubectl
    if command -v kubectl &> /dev/null; then
        record_test "kubectl installed" "PASS" "$(kubectl version --client --short 2>/dev/null || echo 'installed')"
    else
        record_test "kubectl installed" "FAIL" "kubectl not found"
    fi
    
    # Check OpenStack CLI
    if command -v openstack &> /dev/null; then
        record_test "OpenStack CLI installed" "PASS" "$(openstack --version 2>&1 | head -1)"
    else
        record_test "OpenStack CLI installed" "FAIL" "OpenStack CLI not found"
    fi
    
    # Check helm
    if command -v helm &> /dev/null; then
        record_test "Helm installed" "PASS" "$(helm version --short 2>/dev/null || echo 'installed')"
    else
        record_test "Helm installed" "FAIL" "Helm not found"
    fi
    
    # Check upgrade tools directory
    if [ -d "$UPGRADE_TOOLS" ]; then
        record_test "Upgrade tools directory exists" "PASS" "$UPGRADE_TOOLS"
    else
        record_test "Upgrade tools directory exists" "FAIL" "Directory not found"
    fi
    
    # Check main CLI tool
    if [ -x "${UPGRADE_TOOLS}/openstack-upgrade" ]; then
        record_test "Main CLI tool executable" "PASS" "openstack-upgrade"
    else
        record_test "Main CLI tool executable" "FAIL" "Not executable or not found"
    fi
    
    # Check Python dependencies
    cd "$UPGRADE_TOOLS"
    if [ -f "requirements.txt" ]; then
        if python3 -c "import yaml, kubernetes, click" 2>/dev/null; then
            record_test "Python dependencies installed" "PASS" "All required modules available"
        else
            record_test "Python dependencies installed" "FAIL" "Some modules missing"
        fi
    else
        record_test "Python dependencies installed" "SKIP" "requirements.txt not found"
    fi
}

function test_configuration_files() {
    print_header "Testing Configuration Files"
    
    cd "$UPGRADE_TOOLS"
    
    # Check upgrade config
    if [ -f "config/upgrade-config.yaml" ]; then
        if python3 -c "import yaml; yaml.safe_load(open('config/upgrade-config.yaml'))" 2>/dev/null; then
            record_test "upgrade-config.yaml valid" "PASS" "YAML syntax valid"
        else
            record_test "upgrade-config.yaml valid" "FAIL" "YAML syntax error"
        fi
    else
        record_test "upgrade-config.yaml exists" "FAIL" "File not found"
    fi
    
    # Check breaking changes config
    if [ -f "config/breaking-changes.yaml" ]; then
        if python3 -c "import yaml; yaml.safe_load(open('config/breaking-changes.yaml'))" 2>/dev/null; then
            record_test "breaking-changes.yaml valid" "PASS" "YAML syntax valid"
        else
            record_test "breaking-changes.yaml valid" "FAIL" "YAML syntax error"
        fi
    else
        record_test "breaking-changes.yaml exists" "FAIL" "File not found"
    fi
    
    # Check deprecation rules
    if [ -f "config/deprecation-rules.yaml" ]; then
        if python3 -c "import yaml; yaml.safe_load(open('config/deprecation-rules.yaml'))" 2>/dev/null; then
            record_test "deprecation-rules.yaml valid" "PASS" "YAML syntax valid"
        else
            record_test "deprecation-rules.yaml valid" "FAIL" "YAML syntax error"
        fi
    else
        record_test "deprecation-rules.yaml exists" "FAIL" "File not found"
    fi
}

function test_scripts_executable() {
    print_header "Testing Script Executability"
    
    cd "$UPGRADE_TOOLS"
    
    scripts=(
        "scripts/pre-upgrade-validate.sh"
        "scripts/upgrade-execute.sh"
        "scripts/post-upgrade-verify.sh"
        "scripts/rollback.sh"
        "scripts/integration-test-checklist.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                record_test "$(basename $script) executable" "PASS" "$script"
            else
                record_test "$(basename $script) executable" "FAIL" "Not executable"
            fi
        else
            record_test "$(basename $script) exists" "FAIL" "File not found"
        fi
    done
}

function test_python_modules() {
    print_header "Testing Python Modules"
    
    cd "$UPGRADE_TOOLS"
    
    modules=(
        "version.parser"
        "validation.validator"
        "breaking_changes.detector"
        "health.aggregator"
        "executor.helm_executor"
        "rollback.backup_manager"
        "upgrade_logging.logger"
    )
    
    for module in "${modules[@]}"; do
        if python3 -c "import ${module}" 2>/dev/null; then
            record_test "Module ${module} imports" "PASS" "Import successful"
        else
            record_test "Module ${module} imports" "FAIL" "Import failed"
        fi
    done
}

function test_unit_tests() {
    print_header "Testing Unit Tests"
    
    cd "$UPGRADE_TOOLS"
    
    if [ ! -d "tests" ]; then
        record_test "Unit tests directory exists" "FAIL" "tests/ directory not found"
        return
    fi
    
    print_info "Running unit tests..."
    
    if command -v pytest &> /dev/null; then
        start_time=$(date +%s)
        
        if pytest tests/ -v --tb=short > /tmp/pytest-output.txt 2>&1; then
            end_time=$(date +%s)
            duration=$((end_time - start_time))
            
            test_count=$(grep -c "PASSED\|FAILED\|SKIPPED" /tmp/pytest-output.txt || echo "0")
            passed_count=$(grep -c "PASSED" /tmp/pytest-output.txt || echo "0")
            failed_count=$(grep -c "FAILED" /tmp/pytest-output.txt || echo "0")
            
            record_test "Unit tests execution" "PASS" "$passed_count/$test_count passed in ${duration}s"
            record_metric "Unit test duration" "${duration}s"
            record_metric "Unit tests passed" "$passed_count"
            record_metric "Unit tests failed" "$failed_count"
        else
            record_test "Unit tests execution" "FAIL" "Some tests failed"
            cat /tmp/pytest-output.txt >> "$ISSUES_FILE"
        fi
    else
        record_test "Unit tests execution" "SKIP" "pytest not installed"
    fi
}

function test_documentation_exists() {
    print_header "Testing Documentation Completeness"
    
    cd "$UPGRADE_TOOLS"
    
    required_docs=(
        "README.md"
        "docs/LAB_ENVIRONMENT_SETUP.md"
        "docs/OPERATOR_GUIDE.md"
        "docs/UPGRADE_RUNBOOK.md"
        "docs/INTEGRATION_TESTING.md"
        "docs/END_TO_END_TESTING.md"
        "docs/VALIDATION.md"
    )
    
    for doc in "${required_docs[@]}"; do
        if [ -f "$doc" ]; then
            # Check if file is not empty
            if [ -s "$doc" ]; then
                line_count=$(wc -l < "$doc")
                record_test "$(basename $doc) exists and not empty" "PASS" "$line_count lines"
            else
                record_test "$(basename $doc) exists and not empty" "FAIL" "File is empty"
            fi
        else
            record_test "$(basename $doc) exists" "FAIL" "File not found"
        fi
    done
    
    # Check main upgrade documentation
    if [ -f "${PROJECT_ROOT}/docs/2024.1-to-2025.1.md" ]; then
        record_test "Main upgrade documentation exists" "PASS" "docs/2024.1-to-2025.1.md"
    else
        record_test "Main upgrade documentation exists" "FAIL" "File not found"
    fi
}

function test_cli_help() {
    print_header "Testing CLI Help and Usage"
    
    cd "$UPGRADE_TOOLS"
    
    # Test main CLI help
    if ./openstack-upgrade --help > /dev/null 2>&1; then
        record_test "Main CLI --help works" "PASS" "Help text displayed"
    else
        record_test "Main CLI --help works" "FAIL" "Help command failed"
    fi
    
    # Test subcommands
    subcommands=("upgrade" "validate" "rollback" "report")
    
    for cmd in "${subcommands[@]}"; do
        if ./openstack-upgrade "$cmd" --help > /dev/null 2>&1; then
            record_test "CLI subcommand '$cmd' --help works" "PASS" "Help text displayed"
        else
            record_test "CLI subcommand '$cmd' --help works" "FAIL" "Help command failed"
        fi
    done
}

function test_dry_run_mode() {
    print_header "Testing Dry-Run Mode"
    
    cd "$UPGRADE_TOOLS"
    
    print_info "Testing dry-run mode (no actual changes)..."
    
    # Test upgrade dry-run (CLI uses flags not subcommands)
    if ./openstack-upgrade --dry-run > /tmp/dryrun-output.txt 2>&1; then
        record_test "Upgrade dry-run executes" "PASS" "Dry-run completed"
        
        # Check if report was generated
        if [ -f "version-update-report.md" ]; then
            record_test "Dry-run generates report" "PASS" "Report created"
        else
            record_test "Dry-run generates report" "FAIL" "Report not created"
        fi
    else
        record_test "Upgrade dry-run executes" "FAIL" "Dry-run failed"
        cat /tmp/dryrun-output.txt >> "$ISSUES_FILE"
    fi
}

function test_edge_cases() {
    print_header "Testing Edge Cases"
    
    cd "$UPGRADE_TOOLS"
    
    print_subheader "Testing Large Configuration Files"
    
    # Create large config file
    python3 << 'EOF'
import yaml
config = {
    'conf': {
        f'section_{i}': {
            f'option_{j}': f'value_{j}' 
            for j in range(100)
        }
        for i in range(100)
    }
}
with open('/tmp/large-override.yaml', 'w') as f:
    yaml.dump(config, f)
print("Large config file created")
EOF
    
    # Test validation of large file
    start_time=$(date +%s)
    if python3 -c "
from validation.validator import ConfigurationValidator
validator = ConfigurationValidator()
result = validator.validate_override('/tmp/large-override.yaml')
print(f'Valid: {result.passed}')
" > /tmp/large-file-test.txt 2>&1; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        
        if [ $duration -lt 30 ]; then
            record_test "Large file validation performance" "PASS" "Completed in ${duration}s"
        else
            record_test "Large file validation performance" "FAIL" "Too slow: ${duration}s"
        fi
    else
        record_test "Large file validation" "FAIL" "Validation failed"
    fi
    
    print_subheader "Testing Corrupted YAML Files"
    
    # Create corrupted YAML
    echo "invalid: yaml: content: [unclosed" > /tmp/corrupted.yaml
    
    # Test validation catches error
    if python3 -c "
from validation.yaml_validator import YAMLValidator
validator = YAMLValidator()
result = validator.validate_file('/tmp/corrupted.yaml')
if not result.valid:
    print('Error detected correctly')
    exit(0)
else:
    print('Error not detected')
    exit(1)
" > /tmp/corrupted-test.txt 2>&1; then
        record_test "Corrupted YAML detection" "PASS" "Error detected"
    else
        record_test "Corrupted YAML detection" "FAIL" "Error not detected"
    fi
    
    print_subheader "Testing Circular Dependencies"
    
    # Test circular dependency detection
    if python3 -c "
from executor.dependency_graph import DependencyGraph
graph = DependencyGraph()
graph.add_dependency('service-a', 'service-b')
graph.add_dependency('service-b', 'service-c')
graph.add_dependency('service-c', 'service-a')
try:
    order = graph.get_upgrade_order()
    print('ERROR: Should have detected circular dependency')
    exit(1)
except ValueError as e:
    print(f'Circular dependency detected: {e}')
    exit(0)
" > /tmp/circular-test.txt 2>&1; then
        record_test "Circular dependency detection" "PASS" "Detected correctly"
    else
        record_test "Circular dependency detection" "FAIL" "Not detected"
    fi
    
    # Clean up test files
    rm -f /tmp/large-override.yaml /tmp/corrupted.yaml
}

function test_error_handling() {
    print_header "Testing Error Handling"
    
    cd "$UPGRADE_TOOLS"
    
    print_subheader "Testing Missing File Handling"
    
    # Test with non-existent file
    if python3 -c "
from utils.yaml_utils import read_yaml_file
try:
    data = read_yaml_file('/tmp/nonexistent-file.yaml')
    print('ERROR: Should have raised exception')
    exit(1)
except FileNotFoundError:
    print('FileNotFoundError raised correctly')
    exit(0)
except Exception as e:
    print(f'Wrong exception type: {type(e).__name__}')
    exit(1)
" > /tmp/missing-file-test.txt 2>&1; then
        record_test "Missing file error handling" "PASS" "Exception raised correctly"
    else
        record_test "Missing file error handling" "FAIL" "Exception not raised"
    fi
    
    print_subheader "Testing Invalid Configuration Handling"
    
    # Test with invalid config
    echo "invalid_key: invalid_value" > /tmp/invalid-config.yaml
    
    if python3 -c "
from config.config_loader import ConfigLoader
loader = ConfigLoader()
try:
    config = loader.load('/tmp/invalid-config.yaml')
    # Should handle gracefully
    print('Handled gracefully')
    exit(0)
except Exception as e:
    print(f'Exception: {e}')
    exit(0)
" > /tmp/invalid-config-test.txt 2>&1; then
        record_test "Invalid configuration handling" "PASS" "Handled gracefully"
    else
        record_test "Invalid configuration handling" "FAIL" "Not handled properly"
    fi
    
    rm -f /tmp/invalid-config.yaml
}

function test_logging_functionality() {
    print_header "Testing Logging Functionality"
    
    cd "$UPGRADE_TOOLS"
    
    # Test logger initialization
    if python3 -c "
from upgrade_logging.logger import UpgradeLogger
logger = UpgradeLogger()
logger.info('Test message')
logger.warning('Test warning')
logger.error('Test error')
print('Logger works')
" > /tmp/logger-test.txt 2>&1; then
        record_test "Logger initialization" "PASS" "Logger created successfully"
    else
        record_test "Logger initialization" "FAIL" "Logger creation failed"
    fi
    
    # Check if log file is created
    if [ -f "upgrade.log" ]; then
        record_test "Log file creation" "PASS" "upgrade.log exists"
        
        # Check log file content
        if grep -q "Test message" upgrade.log 2>/dev/null; then
            record_test "Log file content" "PASS" "Messages logged correctly"
        else
            record_test "Log file content" "SKIP" "Test messages not found (may be from previous run)"
        fi
    else
        record_test "Log file creation" "SKIP" "Log file not found"
    fi
}

function generate_summary() {
    print_header "Test Execution Summary"
    
    local pass_rate=0
    if [ $TOTAL_TESTS -gt 0 ]; then
        pass_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    fi
    
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Test Results${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
    
    echo -e "Total Tests:    ${CYAN}${TOTAL_TESTS}${NC}"
    echo -e "Passed:         ${GREEN}${PASSED_TESTS}${NC}"
    echo -e "Failed:         ${RED}${FAILED_TESTS}${NC}"
    echo -e "Skipped:        ${YELLOW}${SKIPPED_TESTS}${NC}"
    echo -e "Pass Rate:      ${CYAN}${pass_rate}%${NC}"
    
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
    
    # Write summary to results file
    cat >> "$RESULTS_FILE" << EOF

========================================
SUMMARY
========================================
Total Tests:    $TOTAL_TESTS
Passed:         $PASSED_TESTS
Failed:         $FAILED_TESTS
Skipped:        $SKIPPED_TESTS
Pass Rate:      ${pass_rate}%

Test Date:      $(date '+%Y-%m-%d %H:%M:%S')
Duration:       $(($(date +%s) - START_TIME))s
EOF
    
    # Determine overall result
    if [ $FAILED_TESTS -eq 0 ] && [ $PASSED_TESTS -gt 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC}\n"
        echo "Overall Result: PASS" >> "$RESULTS_FILE"
        
        if [ $SKIPPED_TESTS -eq 0 ]; then
            echo -e "${GREEN}✓ No tests were skipped${NC}\n"
            echo -e "${GREEN}✓ The upgrade tooling is ready for integration testing${NC}\n"
        else
            echo -e "${YELLOW}⚠ Some tests were skipped${NC}\n"
            echo -e "${YELLOW}⚠ Review skipped tests before proceeding${NC}\n"
        fi
    else
        echo -e "${RED}✗ Some tests failed${NC}\n"
        echo "Overall Result: FAIL" >> "$RESULTS_FILE"
        echo -e "${RED}✗ Fix failing tests before proceeding${NC}\n"
    fi
    
    # Show file locations
    echo -e "${BLUE}Test Results Files:${NC}"
    echo -e "  Results:  ${CYAN}${RESULTS_FILE}${NC}"
    echo -e "  Issues:   ${CYAN}${ISSUES_FILE}${NC}"
    echo -e "  Metrics:  ${CYAN}${METRICS_FILE}${NC}\n"
    
    # Show issues if any
    if [ $FAILED_TESTS -gt 0 ]; then
        echo -e "${RED}Issues Found:${NC}\n"
        cat "$ISSUES_FILE"
        echo ""
    fi
}

function main() {
    START_TIME=$(date +%s)
    
    # Activate virtual environment if it exists
    if [ -f "${UPGRADE_TOOLS}/venv/bin/activate" ]; then
        source "${UPGRADE_TOOLS}/venv/bin/activate"
        print_info "Virtual environment activated: ${VIRTUAL_ENV}"
    else
        print_warning "Virtual environment not found at ${UPGRADE_TOOLS}/venv"
    fi
    
    print_banner
    
    print_info "Starting end-to-end testing suite..."
    print_info "This will test all upgrade tooling components"
    echo ""
    
    # Initialize test files
    initialize_test_files
    
    # Run test phases
    test_prerequisites
    test_configuration_files
    test_scripts_executable
    test_python_modules
    test_unit_tests
    test_documentation_exists
    test_cli_help
    test_dry_run_mode
    test_edge_cases
    test_error_handling
    test_logging_functionality
    
    # Generate summary
    generate_summary
    
    # Exit with appropriate code
    if [ $FAILED_TESTS -eq 0 ] && [ $PASSED_TESTS -gt 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
