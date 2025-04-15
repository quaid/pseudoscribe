#!/usr/bin/env python3
"""
Debugging script to check Python module structure in the container.
"""

import sys
import os
import pkgutil

print("Python path:")
for path in sys.path:
    print(f"  - {path}")

try:
    import pseudoscribe
    print("\npseudoscribe package:")
    print(f"  - Location: {pseudoscribe.__file__}")
    print("\nSubpackages:")
    for _, name, ispkg in pkgutil.iter_modules(pseudoscribe.__path__, pseudoscribe.__name__ + "."):
        if ispkg:
            print(f"  - {name}")
            try:
                module = __import__(name)
                print(f"    - Loaded successfully")
            except Exception as e:
                print(f"    - Failed to load: {str(e)}")

    print("\nChecking specific modules:")
    try:
        import pseudoscribe.api
        print(f"  - pseudoscribe.api: {pseudoscribe.api.__file__}")
    except Exception as e:
        print(f"  - pseudoscribe.api: Failed to import - {str(e)}")
    try:
        import pseudoscribe.infrastructure
        print(f"  - pseudoscribe.infrastructure: {pseudoscribe.infrastructure.__file__}")
    except Exception as e:
        print(f"  - pseudoscribe.infrastructure: Failed to import - {str(e)}")
    try:
        import pseudoscribe.models
        print(f"  - pseudoscribe.models: {pseudoscribe.models.__file__}")
    except Exception as e:
        print(f"  - pseudoscribe.models: Failed to import - {str(e)}")

    print("\nChecking API app module:")
    try:
        from pseudoscribe.api import app
        print(f"  - app module: {app.__file__}")
    except Exception as e:
        print(f"  - app module: Failed to import - {str(e)}")
except Exception as e:
    print(f"Error importing pseudoscribe package: {str(e)}")
