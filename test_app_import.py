#!/usr/bin/env python3
"""
Test script to verify app import and router registration
"""

try:
    print("🔍 Testing app import...")
    from pseudoscribe.api.app import app
    print("✅ App imported successfully")
    
    print("\n🔍 Testing router registration...")
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append(f"{route.methods} {route.path}")
    
    print(f"📋 Found {len(routes)} routes:")
    for route in sorted(routes):
        print(f"  {route}")
    
    # Check for Ollama routes specifically
    ollama_routes = [r for r in routes if 'ollama' in r.lower()]
    print(f"\n🤖 Ollama routes ({len(ollama_routes)}):")
    for route in ollama_routes:
        print(f"  {route}")
    
    if ollama_routes:
        print("✅ Ollama routes found!")
    else:
        print("❌ No Ollama routes found!")
        
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
