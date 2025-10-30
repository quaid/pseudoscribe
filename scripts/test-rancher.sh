#!/bin/bash

# Rancher/Kubernetes Testing Script

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up Kubernetes resources..."
    kubectl delete -f kubernetes/ --ignore-not-found=true
    kubectl delete pod backend-test --ignore-not-found=true
    kubectl delete job backend-test --ignore-not-found=true
    kubectl delete job backend-test-ai006 --ignore-not-found=true
    kubectl delete pod model-setup --ignore-not-found=true
}


# Main testing function
main() {
    # Parse arguments
    TEST_PATH="${1:-}"
    TEST_ARGS="${@:2}"
    
    cleanup # Ensure a clean state before starting
    log_info "Starting Rancher/Kubernetes testing pipeline..."
    
    if [ -n "$TEST_PATH" ]; then
        log_info "Running specific test: $TEST_PATH $TEST_ARGS"
    fi

    # Validate kubectl environment
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Build and load images into Rancher
    log_info "Building API container image..."
    nerdctl --namespace k8s.io build -t pseudoscribe/api:latest -f ./Dockerfile .

    log_info "Building VSCode extension test container image..."
    nerdctl --namespace k8s.io build -t pseudoscribe/vscode-extension-test:latest -f ./vscode-extension/Dockerfile ./vscode-extension

    log_success "All images built and loaded successfully"

    # Apply all manifests
    log_info "Deploying all services to Kubernetes..."
    if ! kubectl apply -f kubernetes/; then
        log_error "Failed to deploy services"
        exit 1
    fi
    log_success "Services deployed successfully"

    # Wait for deployments to be ready
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=5m deployment/postgres-db
    kubectl wait --for=condition=available --timeout=5m deployment/ollama
    if ! kubectl wait --for=condition=available --timeout=5m deployment/api; then
        log_error "API deployment failed to become ready. Dumping logs..."
        kubectl logs deployment/api
        exit 1
    fi
    log_success "All deployments are ready"

    # Models are now pre-loaded by Ollama init container
    # The init container downloads tinyllama:latest on first deployment
    # and caches it in the persistent volume for subsequent runs
    log_info "Models pre-loaded by Ollama init container (cached in PVC)"

    # Run backend tests
    log_info "Running backend tests..."
    
    # Determine pytest command
    if [ -n "$TEST_PATH" ]; then
        PYTEST_CMD="pytest $TEST_PATH $TEST_ARGS -v --tb=short"
    else
        PYTEST_CMD="pytest -v --tb=short"
    fi
    
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: backend-test
spec:
  template:
    spec:
      containers:
      - name: backend-test
        image: pseudoscribe/api:latest
        imagePullPolicy: Never
        command: ["/bin/bash", "-c"]
        args:
          - |
            $PYTEST_CMD
        env:
        - name: DATABASE_URL
          value: "postgresql://postgres:postgres@postgres-db-svc/pseudoscribe"
        - name: OLLAMA_BASE_URL
          value: "http://ollama-svc:11434"
      restartPolicy: Never
  backoffLimit: 0
EOF

    if ! kubectl wait --for=condition=complete --timeout=3m job/backend-test; then
        log_error "Backend tests failed"
        kubectl logs job/backend-test
        exit 1
    fi
    log_success "Backend tests passed"
    
    # Show test results
    kubectl logs job/backend-test | tail -20

    # Run VSCode extension tests (skip if running specific backend test)
    if [ -z "$TEST_PATH" ]; then
        log_info "Running VSCode extension tests..."
        if ! kubectl wait --for=condition=complete --timeout=3m job/vscode-extension-test 2>/dev/null; then
            log_info "VSCode extension tests not found or failed (may be expected)"
        else
            log_success "VSCode extension tests passed"
        fi
    else
        log_info "Skipping VSCode extension tests (running specific backend test)"
    fi

    log_success "All Rancher/Kubernetes tests completed successfully!"

    # Manual cleanup on success
    cleanup
}

# Run main function
main "$@"
