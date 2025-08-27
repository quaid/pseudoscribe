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
}

# Trap cleanup on exit
trap cleanup EXIT

# Main testing function
main() {
    log_info "Starting Rancher/Kubernetes testing pipeline..."

    # Validate kubectl environment
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

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
    kubectl wait --for=condition=available --timeout=5m deployment/api
    log_success "All deployments are ready"

    # Run backend tests
    log_info "Running backend tests..."
    if ! kubectl wait --for=condition=complete --timeout=5m job/backend-test; then
        log_error "Backend tests failed"
        kubectl logs job/backend-test
        exit 1
    fi
    log_success "Backend tests passed"

    # Run VSCode extension tests
    log_info "Running VSCode extension tests..."
    if ! kubectl wait --for=condition=complete --timeout=5m job/vscode-extension-test; then
        log_error "VSCode extension tests failed"
        kubectl logs job/vscode-extension-test
        exit 1
    fi
    log_success "VSCode extension tests passed"

    log_success "All Rancher/Kubernetes tests completed successfully!"
}

# Run main function
main "$@"
