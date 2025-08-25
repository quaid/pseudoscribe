#!/bin/bash

# Podman Desktop Startup Script
# Ensures Podman is running before container tests

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

# Check if Podman is running
check_podman_running() {
    if podman info &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Start Podman Desktop
start_podman_desktop() {
    log_info "Starting Podman Desktop..."
    
    # Try to start Podman Desktop
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if [ -d "/Applications/Podman Desktop.app" ]; then
            open -a "Podman Desktop"
        else
            log_error "Podman Desktop not found in /Applications/Podman Desktop.app"
            log_info "Please install Podman Desktop: https://podman-desktop.io/"
            exit 1
        fi
    else
        log_error "Unsupported OS: $OSTYPE"
        exit 1
    fi
    
    # Wait for Podman to start
    log_info "Waiting for Podman Desktop to start..."
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if check_podman_running; then
            log_success "Podman Desktop is running!"
            return 0
        fi
        
        sleep 2
        attempt=$((attempt + 1))
        echo -n "."
    done
    
    echo ""
    log_error "Podman Desktop failed to start within 2 minutes"
    exit 1
}

# Main function
main() {
    log_info "Checking Podman Desktop status..."
    
    if check_podman_running; then
        log_success "Podman Desktop is already running"
    else
        start_podman_desktop
    fi
    
    # Verify Podman Compose is available
    if podman-compose --version &> /dev/null; then
        log_success "Podman Compose is available"
    elif podman compose version &> /dev/null; then
        log_success "Podman Compose (v2) is available"
    else
        log_error "Podman Compose is not available"
        exit 1
    fi
    
    log_success "Podman environment is ready for testing"
}

main "$@"
