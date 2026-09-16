#!/bin/bash

# Agent Chat Hub - Production Validation Script
# Version: 1.0
# Purpose: Validate production readiness before deployment

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Print functions
print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

print_info() {
    echo "  $1"
}

# Validation functions

validate_environment() {
    print_header "1. Environment Validation"

    # Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        if [[ "$(echo $PYTHON_VERSION | cut -d. -f1)" -ge 3 ]] && [[ "$(echo $PYTHON_VERSION | cut -d. -f2)" -ge 14 ]]; then
            print_success "Python version: $PYTHON_VERSION"
        else
            print_error "Python version $PYTHON_VERSION < 3.14"
        fi
    else
        print_error "Python3 not found"
    fi

    # Check virtual environment
    if [ -d "venv" ]; then
        print_success "Virtual environment exists"
    else
        print_warning "Virtual environment not found (venv/)"
    fi

    # Check dependencies
    if [ -f "requirements.txt" ]; then
        print_success "requirements.txt exists"
        source venv/bin/activate 2>/dev/null || true
        if pip check &> /dev/null; then
            print_success "All dependencies satisfied"
        else
            print_error "Dependency conflicts detected"
        fi
    else
        print_error "requirements.txt not found"
    fi

    # Memory check
    TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -ge 2048 ]; then
        print_success "Memory: ${TOTAL_MEM}MB (>= 2GB)"
    else
        print_error "Memory: ${TOTAL_MEM}MB (< 2GB required)"
    fi

    # Disk space
    DISK_AVAIL=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$DISK_AVAIL" -ge 10 ]; then
        print_success "Disk space: ${DISK_AVAIL}GB (>= 10GB)"
    else
        print_warning "Disk space: ${DISK_AVAIL}GB (< 10GB recommended)"
    fi
}

validate_configuration() {
    print_header "2. Configuration Validation"

    # Config file exists
    if [ -f "config/config.json" ]; then
        print_success "config/config.json exists"

        # Validate JSON syntax
        if python3 -c "import json; json.load(open('config/config.json'))" 2>/dev/null; then
            print_success "config.json is valid JSON"
        else
            print_error "config.json has syntax errors"
        fi
    else
        print_error "config/config.json not found"
    fi

    # Check API keys (via environment or keyring)
    if [ -n "$ANTHROPIC_API_KEY" ] || python3 -c "import keyring; keyring.get_password('agent-chat-hub', 'ANTHROPIC_API_KEY')" &> /dev/null; then
        print_success "ANTHROPIC_API_KEY configured"
    else
        print_warning "ANTHROPIC_API_KEY not configured"
    fi

    if [ -n "$OPENAI_API_KEY" ] || python3 -c "import keyring; keyring.get_password('agent-chat-hub', 'OPENAI_API_KEY')" &> /dev/null; then
        print_success "OPENAI_API_KEY configured"
    else
        print_warning "OPENAI_API_KEY not configured"
    fi

    # Log directory
    if [ -d "logs" ]; then
        print_success "logs/ directory exists"
        if [ -w "logs" ]; then
            print_success "logs/ is writable"
        else
            print_error "logs/ is not writable"
        fi
    else
        print_error "logs/ directory not found"
    fi
}

validate_code_quality() {
    print_header "3. Code Quality Validation"

    # Check for TODO/FIXME in critical files
    TODO_COUNT=$(grep -r "TODO\|FIXME" src/ 2>/dev/null | wc -l)
    if [ "$TODO_COUNT" -gt 0 ]; then
        print_warning "Found $TODO_COUNT TODO/FIXME comments"
        print_info "Review: grep -r 'TODO\|FIXME' src/"
    else
        print_success "No TODO/FIXME comments"
    fi

    # Check for hardcoded secrets (basic patterns)
    SECRET_PATTERNS="sk-ant-|sk-proj-|API_KEY.*=.*['\"]sk"
    if grep -r -E "$SECRET_PATTERNS" src/ config/ 2>/dev/null | grep -v "example\|template" > /dev/null; then
        print_error "Potential hardcoded secrets found"
        print_info "Review: grep -r -E '$SECRET_PATTERNS' src/ config/"
    else
        print_success "No hardcoded secrets detected"
    fi

    # Lint check (if ruff available)
    if command -v ruff &> /dev/null; then
        if ruff check src/ --quiet 2>/dev/null; then
            print_success "Ruff lint passed"
        else
            print_warning "Ruff lint issues found"
        fi
    else
        print_info "Ruff not installed (optional)"
    fi

    # Type check (if mypy available)
    if command -v mypy &> /dev/null; then
        if mypy src/ --ignore-missing-imports --no-error-summary 2>/dev/null; then
            print_success "MyPy type check passed"
        else
            print_warning "MyPy type check issues found"
        fi
    else
        print_info "MyPy not installed (optional)"
    fi
}

validate_tests() {
    print_header "4. Test Suite Validation"

    source venv/bin/activate 2>/dev/null || true

    # Unit tests
    if pytest tests/unit/ -v --tb=short 2>&1 | tee /tmp/unit_test_output.txt; then
        UNIT_PASSED=$(grep -c "passed" /tmp/unit_test_output.txt || echo 0)
        print_success "Unit tests passed ($UNIT_PASSED tests)"
    else
        print_error "Unit tests failed"
        print_info "Review: pytest tests/unit/ -v"
    fi

    # Integration tests
    if [ -d "tests/integration" ]; then
        if pytest tests/integration/ -v --tb=short 2>&1 | tee /tmp/integration_test_output.txt; then
            INT_PASSED=$(grep -c "passed" /tmp/integration_test_output.txt || echo 0)
            print_success "Integration tests passed ($INT_PASSED tests)"
        else
            print_error "Integration tests failed"
        fi
    else
        print_warning "No integration tests found"
    fi

    # Benchmark tests
    if [ -d "tests/benchmark" ]; then
        if pytest tests/benchmark/ -v --tb=short -m benchmark 2>&1 | tee /tmp/benchmark_test_output.txt; then
            BENCH_PASSED=$(grep -c "passed" /tmp/benchmark_test_output.txt || echo 0)
            print_success "Benchmark tests passed ($BENCH_PASSED tests)"
        else
            print_error "Benchmark tests failed"
        fi
    else
        print_warning "No benchmark tests found"
    fi

    # Stress tests
    if [ -d "tests/stress" ]; then
        if pytest tests/stress/ -v --tb=short -m stress 2>&1 | tee /tmp/stress_test_output.txt; then
            STRESS_PASSED=$(grep -c "passed" /tmp/stress_test_output.txt || echo 0)
            print_success "Stress tests passed ($STRESS_PASSED tests)"
        else
            print_error "Stress tests failed"
        fi
    else
        print_warning "No stress tests found"
    fi

    # Coverage check
    if pytest tests/unit/ --cov=src --cov-report=term-missing --cov-report=json 2>&1 | tee /tmp/coverage_output.txt; then
        if [ -f "coverage.json" ]; then
            COVERAGE=$(python3 -c "import json; print(int(json.load(open('coverage.json'))['totals']['percent_covered']))")
            if [ "$COVERAGE" -ge 80 ]; then
                print_success "Test coverage: ${COVERAGE}% (>= 80%)"
            else
                print_warning "Test coverage: ${COVERAGE}% (< 80% target)"
            fi
        fi
    fi
}

validate_security() {
    print_header "5. Security Validation"

    # Check .env not in git
    if git ls-files .env 2>/dev/null | grep -q ".env"; then
        print_error ".env file is tracked by git"
    else
        print_success ".env not tracked by git"
    fi

    # Check .gitignore coverage
    if [ -f ".gitignore" ]; then
        if grep -q "\.env" .gitignore && grep -q "config/config.json" .gitignore; then
            print_success ".gitignore covers sensitive files"
        else
            print_warning ".gitignore may not cover all sensitive files"
        fi
    else
        print_error ".gitignore not found"
    fi

    # Dependency audit (if pip-audit available)
    if command -v pip-audit &> /dev/null; then
        if pip-audit --format json > /tmp/pip_audit.json 2>/dev/null; then
            VULN_COUNT=$(python3 -c "import json; print(len(json.load(open('/tmp/pip_audit.json'))))" 2>/dev/null || echo 0)
            if [ "$VULN_COUNT" -eq 0 ]; then
                print_success "No known vulnerabilities (pip-audit)"
            else
                print_error "Found $VULN_COUNT vulnerabilities"
                print_info "Review: pip-audit"
            fi
        fi
    else
        print_info "pip-audit not installed (recommended)"
    fi
}

validate_documentation() {
    print_header "6. Documentation Validation"

    # Essential docs
    ESSENTIAL_DOCS=(
        "README.md"
        "docs/QUICKSTART.md"
        "docs/CONFIGURATION.md"
        "docs/deployment/DEPLOYMENT_GUIDE.md"
        "docs/deployment/PRODUCTION_CHECKLIST.md"
    )

    for doc in "${ESSENTIAL_DOCS[@]}"; do
        if [ -f "$doc" ]; then
            print_success "$doc exists"
        else
            print_warning "$doc not found"
        fi
    done
}

validate_git_state() {
    print_header "7. Git State Validation"

    # Check for uncommitted changes
    if [ -z "$(git status --porcelain)" ]; then
        print_success "No uncommitted changes"
    else
        print_warning "Uncommitted changes detected"
        print_info "Run: git status"
    fi

    # Check current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
        print_warning "Currently on $CURRENT_BRANCH branch"
    else
        print_success "On feature branch: $CURRENT_BRANCH"
    fi

    # Check if ahead of remote
    if git status | grep -q "Your branch is ahead"; then
        print_warning "Branch is ahead of remote (unpushed commits)"
    else
        print_success "Branch synced with remote"
    fi
}

# Main execution
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║   Agent Chat Hub - Production Validation              ║"
    echo "║   Version: 1.0                                         ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""

    START_TIME=$(date +%s)

    validate_environment
    validate_configuration
    validate_code_quality
    validate_tests
    validate_security
    validate_documentation
    validate_git_state

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    # Final summary
    print_header "Validation Summary"

    echo -e "${GREEN}Passed:${NC}   $PASSED"
    echo -e "${RED}Failed:${NC}   $FAILED"
    echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
    echo ""
    echo "Duration: ${DURATION}s"
    echo ""

    if [ "$FAILED" -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  ✓ PRODUCTION READY                            ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
        echo ""
        exit 0
    elif [ "$FAILED" -le 2 ]; then
        echo -e "${YELLOW}╔════════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║  ⚠ REVIEW REQUIRED                             ║${NC}"
        echo -e "${YELLOW}║    Fix critical issues before deployment      ║${NC}"
        echo -e "${YELLOW}╚════════════════════════════════════════════════╝${NC}"
        echo ""
        exit 1
    else
        echo -e "${RED}╔════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║  ✗ NOT READY FOR PRODUCTION                    ║${NC}"
        echo -e "${RED}║    Address all failures before proceeding     ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════╝${NC}"
        echo ""
        exit 2
    fi
}

# Run main
main
