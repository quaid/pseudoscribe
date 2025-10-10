#!/usr/bin/env python3
"""
Debug script to test Ollama endpoints directly
"""

import requests
import json

def test_ollama_endpoints():
    """Test Ollama endpoints to debug routing issues"""
    base_url = "http://localhost:8000"
    headers = {"X-Tenant-ID": "test-tenant"}
    
    endpoints = [
        "/api/v1/ai/ollama/health",
        "/api/v1/ai/ollama/models", 
        "/api/v1/ai/ollama/config",
        "/api/v1/ai/ollama/metrics",
        "/api/v1/ai/ollama/sla-status"
    ]
    
    print("🔍 Testing Ollama endpoints...")
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n📡 Testing: {url}")
            
            response = requests.get(url, headers=headers, timeout=5)
            
            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)}")
                except:
                    print(f"   Response: {response.text}")
            else:
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   Exception: {e}")
    
    # Test POST endpoint
    try:
        url = f"{base_url}/api/v1/ai/ollama/validate"
        print(f"\n📡 Testing POST: {url}")
        response = requests.post(url, headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    test_ollama_endpoints()
