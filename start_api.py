#!/usr/bin/env python3
"""
Entry point script for the PseudoScribe API container.
This script ensures proper Python path setup and starts the FastAPI application.
"""

import os
import sys
import uvicorn
import importlib
import pkgutil

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath("."))

# Debug information about the Python path and module structure
print("Python path:")
for path in sys.path:
    print(f"  - {path}")

print("\nChecking pseudoscribe package structure:")
try:
    import pseudoscribe
    print(f"  - pseudoscribe package found at: {pseudoscribe.__file__}")
    print(f"  - pseudoscribe version: {pseudoscribe.__version__}")
    
    # Check subpackages
    print("\nSubpackages:")
    for _, name, ispkg in pkgutil.iter_modules(pseudoscribe.__path__, pseudoscribe.__name__ + '.'):
        if ispkg:
            print(f"  - {name}")
            try:
                module = importlib.import_module(name)
                print(f"    - Loaded successfully")
            except Exception as e:
                print(f"    - Failed to load: {str(e)}")
    
    # Check API module specifically
    print("\nChecking API module:")
    try:
        import pseudoscribe.api
        print(f"  - API module found at: {pseudoscribe.api.__file__}")
        print("  - API module contents:")
        for item in dir(pseudoscribe.api):
            if not item.startswith('__'):
                print(f"    - {item}")
    except Exception as e:
        print(f"  - Failed to import API module: {str(e)}")
        
    # Check app module specifically
    print("\nChecking app module:")
    try:
        from pseudoscribe.api import app
        print(f"  - App module found at: {app.__file__}")
        print(f"  - App has FastAPI instance: {'app' in dir(app)}")
    except Exception as e:
        print(f"  - Failed to import app module: {str(e)}")
        
except Exception as e:
    print(f"Error importing pseudoscribe package: {str(e)}")

if __name__ == "__main__":
    # Start the FastAPI application
    try:
        print("\nStarting FastAPI application...")
        uvicorn.run(
            "pseudoscribe.api.app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"Error starting FastAPI application: {str(e)}")
