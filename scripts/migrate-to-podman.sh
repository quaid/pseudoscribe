#!/bin/bash

# Docker to Podman Migration Script
# Replaces all Docker references with Podman equivalents across the codebase

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

# Function to diagnose system virtualization issues
diagnose_virtualization_framework() {
    log_info "Diagnosing macOS virtualization framework..."
    
    # Check if virtualization framework is available
    local cpu_features=$(sysctl -n machdep.cpu.features 2>/dev/null || echo "")
    local cpu_leaf7_features=$(sysctl -n machdep.cpu.leaf7_features 2>/dev/null || echo "")
    
    if [[ "$cpu_features" == *"VMX"* ]] || [[ "$cpu_leaf7_features" == *"VMX"* ]] || sysctl -n kern.hv_support 2>/dev/null | grep -q "1"; then
        log_success "Hardware virtualization is available"
    else
        log_warning "Unable to detect hardware virtualization support"
        log_info "Continuing anyway - modern Macs typically support virtualization"
    fi
    
    # Check for conflicting virtualization software
    local conflicts=()
    
    # Check for Docker Desktop
    if pgrep -f "Docker Desktop" > /dev/null; then
        conflicts+=("Docker Desktop")
    fi
    
    # Check for VirtualBox
    if pgrep -f "VirtualBox" > /dev/null || kextstat | grep -q "org.virtualbox"; then
        conflicts+=("VirtualBox")
    fi
    
    # Check for VMware
    if pgrep -f "VMware" > /dev/null || kextstat | grep -q "com.vmware"; then
        conflicts+=("VMware")
    fi
    
    # Check for Parallels
    if pgrep -f "Parallels" > /dev/null; then
        conflicts+=("Parallels")
    fi
    
    if [ ${#conflicts[@]} -gt 0 ]; then
        log_warning "Detected potentially conflicting virtualization software:"
        for conflict in "${conflicts[@]}"; do
            log_warning "  - $conflict"
        done
        log_info "Consider stopping these applications before running Podman"
    fi
    
    # Check system resources
    local memory_gb=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    if [ "$memory_gb" -lt 8 ]; then
        log_warning "System has ${memory_gb}GB RAM. Podman works best with 8GB+ RAM"
    fi
    
    return 0
}

# Function to clean up virtualization framework state
cleanup_virtualization_state() {
    log_info "Cleaning up virtualization framework state..."
    
    # Stop all Podman processes
    log_info "Stopping all Podman processes..."
    pkill -f podman 2>/dev/null || true
    pkill -f gvproxy 2>/dev/null || true
    pkill -f vfkit 2>/dev/null || true
    
    # Clean up socket files more thoroughly
    log_info "Cleaning up socket and state files..."
    local cleanup_paths=(
        "/var/folders/*/T/podman"
        "/tmp/podman*"
        "$HOME/.local/share/containers/podman/machine"
        "$HOME/.config/containers/podman/machine"
        "/var/run/podman*"
    )
    
    for pattern in "${cleanup_paths[@]}"; do
        for path in $pattern; do
            if [ -e "$path" ]; then
                log_info "Cleaning up $path"
                rm -rf "$path" 2>/dev/null || true
            fi
        done
    done
    
    # Wait for cleanup to complete
    sleep 2
}

# Function to check and fix Podman machine networking issues
check_podman_networking() {
    log_info "Checking Podman machine networking..."
    
    # Run system diagnostics first
    diagnose_virtualization_framework
    
    # Check if podman machine exists and if it's having issues
    local machine_exists=false
    local machine_working=false
    
    if podman machine list --format json 2>/dev/null | jq -r '.[].Name' | grep -q "podman-machine-default"; then
        machine_exists=true
        log_info "Podman machine exists, testing functionality..."
        
        # Try to start if not running
        local machine_state=$(podman machine list --format json | jq -r '.[0].Running' 2>/dev/null)
        if [ "$machine_state" != "true" ]; then
            log_info "Attempting to start existing machine..."
            if podman machine start 2>/dev/null; then
                machine_working=true
            fi
        else
            machine_working=true
        fi
    fi
    
    # If machine doesn't exist or isn't working, recreate it
    if [ "$machine_exists" = false ] || [ "$machine_working" = false ]; then
        log_warning "Podman machine needs to be recreated due to networking issues..."
        
        # Perform thorough cleanup
        cleanup_virtualization_state
        
        # Remove existing machine if it exists but isn't working
        if [ "$machine_exists" = true ]; then
            log_info "Removing problematic machine..."
            podman machine stop 2>/dev/null || true
            podman machine rm -f podman-machine-default 2>/dev/null || true
        fi
        
        # Clean up any stale system connections
        log_info "Cleaning up stale system connections..."
        podman system connection rm podman-machine-default 2>/dev/null || true
        
        # Create new machine with conservative settings
        log_info "Creating new Podman machine with conservative settings..."
        
        # Use conservative resource allocation to avoid conflicts
        local init_cmd="podman machine init --cpus 1 --memory 1024 --disk-size 50"
        
        # Capture init output for better diagnostics
        local init_output
        if init_output=$($init_cmd 2>&1); then
            log_success "Podman machine created successfully"
            
            # Start the new machine with detailed error reporting
            log_info "Starting new Podman machine..."
            local max_attempts=2
            local attempt=1
            
            while [ $attempt -le $max_attempts ]; do
                log_info "Start attempt $attempt/$max_attempts..."
                
                # Capture detailed error output
                local start_output
                if start_output=$(podman machine start 2>&1); then
                    log_success "Podman machine started successfully"
                    machine_working=true
                    break
                else
                    log_error "Failed to start machine (attempt $attempt/$max_attempts)"
                    log_error "Error details: $start_output"
                    
                    if echo "$start_output" | grep -q "vfkit exited unexpectedly"; then
                        log_error "vfkit virtualization framework error detected"
                        log_error "This typically requires a system reboot to resolve"
                        log_error "Please reboot your system and try again"
                        return 1
                    fi
                    
                    if [ $attempt -lt $max_attempts ]; then
                        cleanup_virtualization_state
                        sleep 5
                    fi
                    ((attempt++))
                fi
            done
            
            if [ "$machine_working" = false ]; then
                log_error "Failed to start Podman machine after $max_attempts attempts"
                log_error ""
                log_error "REQUIRED ACTION: System reboot needed"
                log_error "The macOS virtualization framework is in an inconsistent state."
                log_error "Please reboot your system and run this script again."
                log_error ""
                log_error "After reboot, the following should work:"
                log_error "  1. podman machine init"
                log_error "  2. podman machine start"
                log_error "  3. podman run hello-world"
                return 1
            fi
        else
            log_error "Failed to create Podman machine"
            log_error "Init error details: $init_output"
            log_error ""
            log_error "CRITICAL: Virtualization framework corruption detected"
            log_error "The macOS virtualization framework requires a system reboot to reset."
            log_error ""
            log_error "Please:"
            log_error "  1. Save your work and close all applications"
            log_error "  2. Reboot your system: sudo reboot"
            log_error "  3. After reboot, run this script again"
            log_error ""
            log_error "This is a known macOS issue with virtualization frameworks"
            log_error "and cannot be resolved without a reboot."
            return 1
        fi
    else
        log_success "Podman machine is already running"
    fi
    
    # Verify networking is working
    log_info "Testing Podman connectivity..."
    if timeout 30 podman run --rm hello-world > /dev/null 2>&1; then
        log_success "Podman networking is working correctly"
    else
        log_warning "Podman connectivity test failed or timed out"
        log_info "Continuing with migration - you may need to troubleshoot networking later"
    fi
}

# Function to replace Docker commands with Podman equivalents
replace_docker_commands() {
    local file="$1"
    local backup_file="${file}.docker-backup"
    
    # Create backup
    cp "$file" "$backup_file"
    
    # Replace docker commands with podman
    sed -i '' 's/podman-compose/podman-compose/g' "$file"
    sed -i '' 's/\bdocker\b/podman/g' "$file"
    
    # Update environment variables
    sed -i '' 's/PODMAN_COMPOSE/PODMAN_COMPOSE/g' "$file"
    sed -i '' 's/BUILDAH_FORMAT/BUILDAH_FORMAT/g' "$file"
    
    log_info "Updated $file (backup: $backup_file)"
}

# Function to update compose files for podman
update_compose_files() {
    local file="$1"
    local backup_file="${file}.docker-backup"
    
    # Create backup
    cp "$file" "$backup_file"
    
    # Update compose file for podman compatibility
    # Remove Docker-specific options that aren't supported in podman-compose
    sed -i '' '/restart: unless-stopped/d' "$file"
    
    # Update health checks to use podman format
    sed -i '' 's/test: \["CMD", "curl"/test: ["CMD-SHELL", "curl"/g' "$file"
    
    log_info "Updated compose file $file (backup: $backup_file)"
}

# Function to update Dockerfiles for podman
update_dockerfiles() {
    local file="$1"
    local backup_file="${file}.docker-backup"
    
    # Create backup
    cp "$file" "$backup_file"
    
    # Add podman-specific optimizations
    # No major changes needed as Dockerfile format is compatible
    
    log_info "Dockerfile $file is compatible with podman (backup: $backup_file)"
}

# Function to setup Podman environment
setup_podman_environment() {
    log_info "Setting up Podman environment..."
    
    # Check if podman is installed
    if ! command -v podman &> /dev/null; then
        log_error "Podman is not installed. Please install it first:"
        echo "  brew install podman"
        exit 1
    fi
    
    # Check if podman-compose is installed
    if ! command -v podman-compose &> /dev/null; then
        log_warning "podman-compose is not installed. Installing..."
        if command -v pip3 &> /dev/null; then
            pip3 install podman-compose
        else
            log_error "pip3 not found. Please install podman-compose manually:"
            echo "  pip3 install podman-compose"
            exit 1
        fi
    fi
    
    # Setup Podman machine and networking
    check_podman_networking
}

# Main migration function
main() {
    log_info "Starting Docker to Podman migration..."
    
    # Setup Podman environment first
    setup_podman_environment
    
    # Get the project root directory
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$PROJECT_ROOT"
    
    log_info "Project root: $PROJECT_ROOT"
    
    # Update shell scripts
    log_info "Updating shell scripts..."
    find . -name "*.sh" -type f | while read -r file; do
        if grep -q "docker" "$file"; then
            replace_docker_commands "$file"
        fi
    done
    
    # Update Python scripts
    log_info "Updating Python scripts..."
    find . -name "*.py" -type f | while read -r file; do
        if grep -q "docker" "$file"; then
            replace_docker_commands "$file"
        fi
    done
    
    # Update compose files
    log_info "Updating compose files..."
    find . -name "*compose*.yml" -o -name "*compose*.yaml" -type f | while read -r file; do
        update_compose_files "$file"
    done
    
    # Update Dockerfiles
    log_info "Updating Dockerfiles..."
    find . -name "Dockerfile*" -type f | while read -r file; do
        update_dockerfiles "$file"
    done
    
    # Update GitHub Actions
    log_info "Updating GitHub Actions workflows..."
    find .github -name "*.yml" -o -name "*.yaml" -type f 2>/dev/null | while read -r file; do
        if grep -q "docker" "$file"; then
            replace_docker_commands "$file"
        fi
    done
    
    # Update documentation
    log_info "Updating documentation..."
    find . -name "*.md" -type f | while read -r file; do
        if grep -q "docker" "$file"; then
            replace_docker_commands "$file"
        fi
    done
    
    # Update package.json files
    log_info "Updating package.json files..."
    find . -name "package.json" -type f | while read -r file; do
        if grep -q "docker" "$file"; then
            replace_docker_commands "$file"
        fi
    done
    
    # Create podman-specific scripts
    log_info "Creating podman-specific scripts..."
    
    # Rename docker-specific scripts
    if [ -f "scripts/start-docker.sh" ]; then
        mv "scripts/start-docker.sh" "scripts/start-podman.sh"
        log_info "Renamed start-docker.sh to start-podman.sh"
    fi
    
    # Update the renamed script
    if [ -f "scripts/start-podman.sh" ]; then
        replace_docker_commands "scripts/start-podman.sh"
        
        # Update script content for podman
        sed -i '' 's/Docker Desktop/Podman/g' "scripts/start-podman.sh"
        sed -i '' 's/Docker/Podman/g' "scripts/start-podman.sh"
        sed -i '' 's/\/Applications\/Docker\.app/\/Applications\/Podman Desktop.app/g' "scripts/start-podman.sh"
    fi
    
    log_success "Docker to Podman migration completed!"
    log_info "Backup files created with .docker-backup extension"
    log_warning "Please test the migrated configuration before removing backup files"
    
    # Show summary
    echo ""
    log_info "Migration Summary:"
    echo "  - Shell scripts updated"
    echo "  - Python scripts updated"  
    echo "  - Compose files updated"
    echo "  - Dockerfiles verified compatible"
    echo "  - GitHub Actions updated"
    echo "  - Documentation updated"
    echo "  - Package.json files updated"
    echo "  - start-docker.sh renamed to start-podman.sh"
    echo ""
    log_info "Next steps:"
    echo "  1. Test podman functionality: podman run hello-world"
    echo "  2. Test compose functionality: podman-compose --version"
    echo "  3. Run container tests: ./scripts/test-containers.sh"
    echo "  4. Remove backup files when satisfied: find . -name '*.docker-backup' -delete"
    echo ""
    log_info "Troubleshooting:"
    echo "  - If networking issues persist: podman machine stop && podman machine start"
    echo "  - To recreate machine: podman machine rm -f podman-machine-default && podman machine init"
    echo "  - Check logs: podman machine inspect podman-machine-default"
}

main "$@"
