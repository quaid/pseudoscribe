"""
Test script for Style API endpoints.

This script demonstrates how to use the Style API endpoints and can be used
to verify that the API is functioning correctly in the containerized environment.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TENANT_HEADER = {"X-Tenant-ID": "test-tenant"}


async def test_style_analyze():
    """Test the style analysis endpoint."""
    url = f"{BASE_URL}/api/style/analyze"
    
    # Sample text for analysis
    payload = {
        "text": "This is a sample text for style analysis. It demonstrates how the Style API works."
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=TENANT_HEADER)
        
        print("\n=== Style Analysis Test ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2))
            return result
        else:
            print(f"Error: {response.text}")
            return None


async def test_style_compare():
    """Test the style comparison endpoint."""
    url = f"{BASE_URL}/api/style/compare"
    
    # Sample texts for comparison
    payload = {
        "text1": "This is a formal document written in a professional tone. The language is precise and structured.",
        "text2": "Hey there! This is written in a casual style, you know? It's pretty relaxed and conversational."
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=TENANT_HEADER)
        
        print("\n=== Style Comparison Test ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2))
            return result
        else:
            print(f"Error: {response.text}")
            return None


async def test_style_adapt():
    """Test the style adaptation endpoint."""
    url = f"{BASE_URL}/api/style/adapt"
    
    # Sample text and target style
    payload = {
        "text": "This is a casual message. I'm writing to tell you about our new product.",
        "target_style": {
            "complexity": 0.8,
            "formality": 0.9,
            "tone": 0.7,
            "readability": 0.6
        },
        "strength": 0.7
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=TENANT_HEADER)
        
        print("\n=== Style Adaptation Test ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2))
            return result
        else:
            print(f"Error: {response.text}")
            return None


async def test_style_check():
    """Test the style check endpoint."""
    url = f"{BASE_URL}/api/style/check"
    
    # Sample text and target style
    payload = {
        "text": "This is a sample text that we want to check against a target style.",
        "target_style": {
            "complexity": 0.5,
            "formality": 0.7,
            "tone": 0.6,
            "readability": 0.8
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=TENANT_HEADER)
        
        print("\n=== Style Check Test ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2))
            return result
        else:
            print(f"Error: {response.text}")
            return None


async def run_all_tests():
    """Run all Style API tests."""
    await test_style_analyze()
    await test_style_compare()
    await test_style_adapt()
    await test_style_check()


if __name__ == "__main__":
    print("Running Style API tests...")
    asyncio.run(run_all_tests())
    print("\nTests completed.")
