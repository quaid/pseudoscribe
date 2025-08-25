#!/bin/bash

# Cloud-based Container Testing Script for PseudoScribe
# Runs in Kubernetes pods using pseudoscribe-agent infrastructure

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test configuration
TEST_RESULTS_DIR="/test-results"
WORKSPACE_DIR="/workspace"
DATABASE_URL="${DATABASE_URL:-postgresql://test_user:test_password@localhost:5432/pseudoscribe_test}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
REDIS_URL="${REDIS_URL:-redis://localhost:6379}"

# Ensure test results directory exists
mkdir -p "$TEST_RESULTS_DIR"

# Function to wait for service to be ready
wait_for_service() {
    local service_name="$1"
    local host="$2"
    local port="$3"
    local max_attempts=30
    local attempt=1
    
    log_info "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            log_success "$service_name is ready"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    log_error "$service_name failed to start within timeout"
    return 1
}

# Function to test database connectivity
test_database() {
    log_info "Testing PostgreSQL database connectivity..."
    
    # Wait for PostgreSQL to be ready
    wait_for_service "PostgreSQL" "localhost" "5432"
    
    # Test database connection
    if PGPASSWORD=test_password psql -h localhost -U test_user -d pseudoscribe_test -c "SELECT 1;" > /dev/null 2>&1; then
        log_success "Database connectivity test passed"
        return 0
    else
        log_error "Database connectivity test failed"
        return 1
    fi
}

# Function to test Redis connectivity
test_redis() {
    log_info "Testing Redis connectivity..."
    
    # Wait for Redis to be ready
    wait_for_service "Redis" "localhost" "6379"
    
    # Test Redis connection
    if redis-cli -h localhost ping | grep -q "PONG"; then
        log_success "Redis connectivity test passed"
        return 0
    else
        log_error "Redis connectivity test failed"
        return 1
    fi
}

# Function to test Ollama service
test_ollama() {
    log_info "Testing Ollama AI service..."
    
    # Wait for Ollama to be ready
    wait_for_service "Ollama" "localhost" "11434"
    
    # Test Ollama API
    if curl -s "$OLLAMA_BASE_URL/api/tags" > /dev/null; then
        log_success "Ollama service test passed"
        return 0
    else
        log_error "Ollama service test failed"
        return 1
    fi
}

# Function to run container build tests
test_container_build() {
    log_info "Testing PseudoScribe container build..."
    
    cd "$WORKSPACE_DIR"
    
    # Build the main application container
    if podman build -t pseudoscribe:test -f Dockerfile .; then
        log_success "PseudoScribe container build test passed"
        return 0
    else
        log_error "PseudoScribe container build test failed"
        return 1
    fi
}

# Function to run API container tests
test_api_containers() {
    log_info "Testing API containers..."
    
    cd "$WORKSPACE_DIR"
    
    # Start API container in background
    local container_id
    container_id=$(podman run -d \
        --name pseudoscribe-api-test \
        -p 8000:8000 \
        -e DATABASE_URL="$DATABASE_URL" \
        -e OLLAMA_BASE_URL="$OLLAMA_BASE_URL" \
        -e REDIS_URL="$REDIS_URL" \
        pseudoscribe:test)
    
    # Wait for API to be ready
    sleep 10
    
    # Test API health endpoint
    local api_test_passed=false
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        log_success "API container health test passed"
        api_test_passed=true
    else
        log_error "API container health test failed"
    fi
    
    # Cleanup
    podman stop "$container_id" || true
    podman rm "$container_id" || true
    
    if [ "$api_test_passed" = true ]; then
        return 0
    else
        return 1
    fi
}

# Function to run integration tests
test_integration() {
    log_info "Running integration tests..."
    
    cd "$WORKSPACE_DIR"
    
    # Run Python integration tests
    if python -m pytest tests/integration/ -v --junitxml="$TEST_RESULTS_DIR/integration-results.xml"; then
        log_success "Integration tests passed"
        return 0
    else
        log_error "Integration tests failed"
        return 1
    fi
}

# Function to run performance tests
test_performance() {
    log_info "Running performance tests..."
    
    cd "$WORKSPACE_DIR"
    
    # Run performance tests with locust or similar
    if python -m pytest tests/performance/ -v --junitxml="$TEST_RESULTS_DIR/performance-results.xml"; then
        log_success "Performance tests passed"
        return 0
    else
        log_error "Performance tests failed"
        return 1
    fi
}

# Function to run security tests
test_security() {
    log_info "Running security tests..."
    
    cd "$WORKSPACE_DIR"
    
    # Run security scans on containers
    local security_passed=true
    
    # Scan the built container
    if command -v trivy &> /dev/null; then
        if trivy image pseudoscribe:test --exit-code 1 --severity HIGH,CRITICAL; then
            log_success "Container security scan passed"
        else
            log_warning "Container security scan found issues"
            security_passed=false
        fi
    else
        log_warning "Trivy not available, skipping container security scan"
    fi
    
    # Run Python security tests
    if python -m pytest tests/security/ -v --junitxml="$TEST_RESULTS_DIR/security-results.xml"; then
        log_success "Security tests passed"
    else
        log_error "Security tests failed"
        security_passed=false
    fi
    
    if [ "$security_passed" = true ]; then
        return 0
    else
        return 1
    fi
}

# Function to generate test report
generate_test_report() {
    log_info "Generating test report..."
    
    local report_file="$TEST_RESULTS_DIR/test-summary.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "cloud-kubernetes",
    "test_results": {
        "database": $database_result,
        "redis": $redis_result,
        "ollama": $ollama_result,
        "container_build": $build_result,
        "api_containers": $api_result,
        "integration": $integration_result,
        "performance": $performance_result,
        "security": $security_result
    },
    "overall_status": "$overall_status"
}
EOF
    
    log_success "Test report generated: $report_file"
}

# Main test execution
main() {
    log_info "Starting PseudoScribe cloud container tests..."
    log_info "Test environment: Kubernetes pods with Intuit Service Paved Road"
    
    local exit_code=0
    local database_result="false"
    local redis_result="false"
    local ollama_result="false"
    local build_result="false"
    local api_result="false"
    local integration_result="false"
    local performance_result="false"
    local security_result="false"
    
    # Run all tests
    if test_database; then database_result="true"; else exit_code=1; fi
    if test_redis; then redis_result="true"; else exit_code=1; fi
    if test_ollama; then ollama_result="true"; else exit_code=1; fi
    if test_container_build; then build_result="true"; else exit_code=1; fi
    if test_api_containers; then api_result="true"; else exit_code=1; fi
    if test_integration; then integration_result="true"; else exit_code=1; fi
    if test_performance; then performance_result="true"; else exit_code=1; fi
    if test_security; then security_result="true"; else exit_code=1; fi
    
    # Determine overall status
    local overall_status="FAILED"
    if [ $exit_code -eq 0 ]; then
        overall_status="PASSED"
        log_success "All cloud container tests passed!"
    else
        log_error "Some cloud container tests failed"
    fi
    
    # Generate test report
    generate_test_report
    
    # Summary
    echo ""
    log_info "Test Summary:"
    echo "  - Database connectivity: $([ "$database_result" = "true" ] && echo "✓ PASS" || echo "✗ FAIL")"
    echo "  - Redis connectivity: $([ "$redis_result" = "true" ] && echo "✓ PASS" || echo "✗ FAIL")"
    echo "  - Ollama service: $([ "$ollama_result" = "true" ] && echo "✓ PASS" || echo "✗ FAIL")"
    echo "  - Container build: $([ "$build_result" = "true" ] && echo "✓ PASS" || echo "✗ FAIL")"
    echo "  - API containers: $([ "$api_result" = "true" ] && echo "✓ PASS" || echo "✗ FAIL")"
    echo "  - Integration tests: $([ "$integration_result" = "true" ] && echo "✓ PASS" || echo "✗ FAIL")"
    echo "  - Performance tests: $([ "$performance_result" = "true" ] && echo "✓ PASS" || echo "✗ FAIL")"
    echo "  - Security tests: $([ "$security_result" = "true" ] && echo "✓ PASS" || echo "✗ FAIL")"
    echo ""
    echo "Overall Status: $overall_status"
    
    exit $exit_code
}

# Run main function
main "$@"
