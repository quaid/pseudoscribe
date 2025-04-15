#!/usr/bin/env python3
"""
Operate First Management Script

This script helps manage the containerized environment for PseudoScribe,
following the "operate first" approach. It allows for:
1. Starting the containerized environment with fully implemented APIs
2. Adding newly completed APIs to the container
3. Running tests against the containerized environment
4. Managing the deployment status of APIs

Usage:
    python operate_first.py start - Start the containerized environment
    python operate_first.py status - Check the status of APIs
    python operate_first.py test - Run tests against the containerized environment
    python operate_first.py deploy <api_name> - Deploy a newly completed API
"""

import os
import sys
import json
import subprocess
from typing import Dict, List, Any
from datetime import datetime

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS_FILE = os.path.join(PROJECT_ROOT, "deployment_status.json")
API_COMPONENTS = [
    "markdown_processor",
    "vault_sync",
    "ollama_service",
    "vector_store",
    "model_manager",
    "style_profiler",
    "style_checker",
    "style_adapter",
    "vector_generator"
]

# Default status for new deployment
DEFAULT_STATUS = {
    "last_updated": "",
    "apis": {
        "markdown_processor": {"status": "production", "deployed": True},
        "vault_sync": {"status": "production", "deployed": True},
        "ollama_service": {"status": "production", "deployed": True},
        "vector_store": {"status": "development", "deployed": False},
        "model_manager": {"status": "development", "deployed": False},
        "style_profiler": {"status": "stub", "deployed": False},
        "style_checker": {"status": "stub", "deployed": False},
        "style_adapter": {"status": "stub", "deployed": False},
        "vector_generator": {"status": "stub", "deployed": False}
    }
}

def load_status() -> Dict[str, Any]:
    """Load the current deployment status"""
    if not os.path.exists(STATUS_FILE):
        # Create default status file if it doesn't exist
        with open(STATUS_FILE, 'w') as f:
            json.dump(DEFAULT_STATUS, f, indent=2)
        return DEFAULT_STATUS
    
    with open(STATUS_FILE, 'r') as f:
        return json.load(f)

def save_status(status: Dict[str, Any]) -> None:
    """Save the current deployment status"""
    status["last_updated"] = datetime.now().isoformat()
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)

def start_environment() -> None:
    """Start the containerized environment"""
    print("Starting the containerized environment...")
    
    # Build and start the containers
    result = subprocess.run(
        ["docker-compose", "up", "--build", "-d"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error starting environment: {result.stderr}")
        sys.exit(1)
    
    print("Environment started successfully!")
    print("\nAccess the API at: http://localhost:8000")
    print("Ollama service at: http://localhost:11434")
    print("PostgreSQL at: localhost:5432")

def stop_environment() -> None:
    """Stop the containerized environment"""
    print("Stopping the containerized environment...")
    
    result = subprocess.run(
        ["docker-compose", "down"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error stopping environment: {result.stderr}")
        sys.exit(1)
    
    print("Environment stopped successfully!")

def check_status() -> None:
    """Check the status of APIs"""
    status = load_status()
    
    print("\n=== PseudoScribe API Deployment Status ===")
    print(f"Last Updated: {status['last_updated']}")
    print("\nAPI Components:")
    
    for api, details in status["apis"].items():
        emoji = "✅" if details["deployed"] else "❌"
        status_text = details["status"].upper()
        print(f"{emoji} {api}: {status_text}")
    
    # Check if containers are running
    result = subprocess.run(
        ["docker-compose", "ps"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    print("\nContainer Status:")
    print(result.stdout)

def run_tests() -> None:
    """Run tests against the containerized environment"""
    print("Running tests against the containerized environment...")
    
    # Run pytest in the API container
    result = subprocess.run(
        ["docker-compose", "exec", "api", "pytest", "-xvs", "tests/"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Tests failed: {result.stderr}")
        print(result.stdout)
        sys.exit(1)
    
    print("All tests passed successfully!")
    print(result.stdout)

def deploy_api(api_name: str) -> None:
    """Deploy a newly completed API"""
    if api_name not in API_COMPONENTS:
        print(f"Error: Unknown API '{api_name}'")
        print(f"Available APIs: {', '.join(API_COMPONENTS)}")
        sys.exit(1)
    
    status = load_status()
    
    if status["apis"][api_name]["deployed"]:
        print(f"API '{api_name}' is already deployed!")
        return
    
    print(f"Deploying API '{api_name}'...")
    
    # Update the status
    status["apis"][api_name]["status"] = "production"
    status["apis"][api_name]["deployed"] = True
    save_status(status)
    
    # Rebuild the containers to include the new API
    result = subprocess.run(
        ["docker-compose", "up", "--build", "-d"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error deploying API: {result.stderr}")
        # Revert status change
        status["apis"][api_name]["status"] = "development"
        status["apis"][api_name]["deployed"] = False
        save_status(status)
        sys.exit(1)
    
    print(f"API '{api_name}' deployed successfully!")

def print_help() -> None:
    """Print help information"""
    print(__doc__)

def main() -> None:
    """Main entry point"""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "start":
        start_environment()
    elif command == "stop":
        stop_environment()
    elif command == "status":
        check_status()
    elif command == "test":
        run_tests()
    elif command == "deploy":
        if len(sys.argv) < 3:
            print("Error: Missing API name")
            print_help()
            sys.exit(1)
        deploy_api(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
