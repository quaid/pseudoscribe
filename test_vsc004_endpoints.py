#!/usr/bin/env python3
"""
Quick test script for VSC-004 endpoints
"""

import asyncio
import httpx
import json
import time

BASE_URL = "http://localhost:8000"
TENANT_HEADER = {"X-Tenant-ID": "test-tenant"}

async def test_style_analyze():
    """Test the VSC-004 style analysis endpoint"""
    url = f"{BASE_URL}/api/v1/style/analyze"
    
    payload = {
        "text": "This is a sample paragraph for style analysis. It contains multiple sentences with varying complexity."
    }
    
    try:
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            response = await client.post(url, json=payload, headers=TENANT_HEADER)
            end_time = time.time()
            
            print(f"\n=== VSC-004 Style Analysis Test ===")
            print(f"Status: {response.status_code}")
            print(f"Response time: {end_time - start_time:.3f}s")
            
            if response.status_code == 200:
                result = response.json()
                print(json.dumps(result, indent=2))
                
                # Verify scores are in range
                for score_name in ["complexity", "formality", "tone", "readability"]:
                    score = result.get(score_name, -1)
                    if 0.0 <= score <= 1.0:
                        print(f"✓ {score_name}: {score:.3f} (valid range)")
                    else:
                        print(f"✗ {score_name}: {score} (invalid range)")
                        
                return True
            else:
                print(f"Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"Connection error: {e}")
        return False

async def test_style_transform():
    """Test the VSC-004 style transformation endpoint"""
    url = f"{BASE_URL}/api/v1/style/transform"
    
    payload = {
        "text": "I am writing to formally request your assistance in this matter.",
        "target_style": "casual",
        "preserve_meaning": True
    }
    
    try:
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            response = await client.post(url, json=payload, headers=TENANT_HEADER)
            end_time = time.time()
            
            print(f"\n=== VSC-004 Style Transform Test ===")
            print(f"Status: {response.status_code}")
            print(f"Response time: {end_time - start_time:.3f}s")
            
            if response.status_code == 200:
                result = response.json()
                print(json.dumps(result, indent=2))
                return True
            else:
                print(f"Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"Connection error: {e}")
        return False

async def test_consistency_check():
    """Test the VSC-004 consistency checking endpoint"""
    url = f"{BASE_URL}/api/v1/style/check-consistency"
    
    payload = {
        "paragraphs": [
            "This is a formal academic paragraph with sophisticated vocabulary and complex sentence structures.",
            "Yo, this is super casual and uses slang!",
            "The aforementioned considerations necessitate a comprehensive analysis of the underlying factors."
        ]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            response = await client.post(url, json=payload, headers=TENANT_HEADER)
            end_time = time.time()
            
            print(f"\n=== VSC-004 Consistency Check Test ===")
            print(f"Status: {response.status_code}")
            print(f"Response time: {end_time - start_time:.3f}s")
            
            if response.status_code == 200:
                result = response.json()
                print(json.dumps(result, indent=2))
                return True
            else:
                print(f"Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"Connection error: {e}")
        return False

async def main():
    """Run all VSC-004 endpoint tests"""
    print("Testing VSC-004 Advanced Extension Features API endpoints...")
    
    tests = [
        ("Style Analysis", test_style_analyze),
        ("Style Transform", test_style_transform),
        ("Consistency Check", test_consistency_check)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name} test...")
        result = await test_func()
        results.append((test_name, result))
    
    print(f"\n{'='*50}")
    print("Test Summary:")
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} {test_name}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())
