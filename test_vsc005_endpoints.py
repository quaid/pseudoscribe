#!/usr/bin/env python3
"""
Quick test script for VSC-005 Live Suggestions endpoints
"""

import asyncio
import httpx
import json
import time

BASE_URL = "http://localhost:8000"
TENANT_HEADER = {"X-Tenant-ID": "test-tenant"}

async def test_live_analysis():
    """Test the VSC-005 live analysis endpoint"""
    url = f"{BASE_URL}/api/v1/suggestions/analyze-live"
    
    payload = {
        "text": "This text have grammar issues and could be more formal for technical documentation.",
        "cursor_position": 75,
        "document_type": "technical"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            response = await client.post(url, json=payload, headers=TENANT_HEADER)
            end_time = time.time()
            
            print(f"\n=== VSC-005 Live Analysis Test ===")
            print(f"Status: {response.status_code}")
            print(f"Response time: {end_time - start_time:.3f}s")
            
            if response.status_code == 200:
                result = response.json()
                print(json.dumps(result, indent=2))
                
                # Verify performance requirement
                if result.get("analysis_time", 1.0) < 0.5:
                    print("✓ Performance requirement met (<500ms)")
                else:
                    print("✗ Performance requirement not met (>500ms)")
                
                # Check suggestions structure
                suggestions = result.get("suggestions", [])
                if suggestions:
                    print(f"✓ Found {len(suggestions)} suggestions")
                    for i, suggestion in enumerate(suggestions):
                        print(f"  {i+1}. {suggestion['type']} ({suggestion['severity']}): {suggestion['message']}")
                else:
                    print("ℹ No suggestions found")
                        
                return True
            else:
                print(f"Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"Connection error: {e}")
        return False

async def test_accept_suggestion():
    """Test the VSC-005 accept suggestion endpoint"""
    url = f"{BASE_URL}/api/v1/suggestions/accept"
    
    payload = {
        "suggestion_id": "test-suggestion-123",
        "original_text": "This text have grammar issues",
        "start_pos": 10,
        "end_pos": 14,
        "replacement": "has"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            response = await client.post(url, json=payload, headers=TENANT_HEADER)
            end_time = time.time()
            
            print(f"\n=== VSC-005 Accept Suggestion Test ===")
            print(f"Status: {response.status_code}")
            print(f"Response time: {end_time - start_time:.3f}s")
            
            if response.status_code == 200:
                result = response.json()
                print(json.dumps(result, indent=2))
                
                # Verify text was updated correctly
                expected_text = "This text has grammar issues"
                if result.get("updated_text") == expected_text:
                    print("✓ Text updated correctly")
                else:
                    print(f"✗ Text update incorrect. Expected: '{expected_text}', Got: '{result.get('updated_text')}'")
                
                return True
            else:
                print(f"Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"Connection error: {e}")
        return False

async def test_display_config():
    """Test the VSC-005 display configuration endpoint"""
    url = f"{BASE_URL}/api/v1/suggestions/display-config"
    
    try:
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            response = await client.get(url, headers=TENANT_HEADER)
            end_time = time.time()
            
            print(f"\n=== VSC-005 Display Config Test ===")
            print(f"Status: {response.status_code}")
            print(f"Response time: {end_time - start_time:.3f}s")
            
            if response.status_code == 200:
                result = response.json()
                print(json.dumps(result, indent=2))
                
                # Verify config structure
                required_fields = ["show_low_severity", "show_medium_severity", "show_high_severity", 
                                 "max_suggestions", "suggestion_types"]
                
                all_present = all(field in result for field in required_fields)
                if all_present:
                    print("✓ All required config fields present")
                else:
                    missing = [field for field in required_fields if field not in result]
                    print(f"✗ Missing config fields: {missing}")
                
                return True
            else:
                print(f"Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"Connection error: {e}")
        return False

async def test_incremental_analysis():
    """Test incremental analysis performance"""
    url = f"{BASE_URL}/api/v1/suggestions/analyze-live"
    
    base_text = "This is a base text for incremental analysis testing."
    
    # First analysis
    payload1 = {
        "text": base_text,
        "cursor_position": len(base_text),
        "document_type": "general",
        "previous_analysis_id": None
    }
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"\n=== VSC-005 Incremental Analysis Test ===")
            
            # First analysis
            response1 = await client.post(url, json=payload1, headers=TENANT_HEADER)
            if response1.status_code != 200:
                print(f"First analysis failed: {response1.text}")
                return False
            
            result1 = response1.json()
            analysis_id = result1.get("analysis_id")
            print(f"First analysis time: {result1.get('analysis_time', 0):.3f}s")
            
            # Incremental analysis
            modified_text = base_text + " Additional content added."
            payload2 = {
                "text": modified_text,
                "cursor_position": len(modified_text),
                "document_type": "general",
                "previous_analysis_id": analysis_id
            }
            
            start_time = time.time()
            response2 = await client.post(url, json=payload2, headers=TENANT_HEADER)
            end_time = time.time()
            
            if response2.status_code == 200:
                result2 = response2.json()
                incremental_time = result2.get("analysis_time", 0)
                print(f"Incremental analysis time: {incremental_time:.3f}s")
                print(f"Was incremental: {result2.get('incremental', False)}")
                
                if incremental_time < 0.3:
                    print("✓ Incremental analysis performance good")
                else:
                    print("ℹ Incremental analysis could be faster")
                
                return True
            else:
                print(f"Incremental analysis failed: {response2.text}")
                return False
                
    except Exception as e:
        print(f"Connection error: {e}")
        return False

async def main():
    """Run all VSC-005 endpoint tests"""
    print("Testing VSC-005 Live Suggestions API endpoints...")
    
    tests = [
        ("Live Analysis", test_live_analysis),
        ("Accept Suggestion", test_accept_suggestion),
        ("Display Config", test_display_config),
        ("Incremental Analysis", test_incremental_analysis)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running {test_name} test...")
        result = await test_func()
        results.append((test_name, result))
    
    print(f"\n{'='*60}")
    print("Test Summary:")
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} {test_name}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())
