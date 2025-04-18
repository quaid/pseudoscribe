#!/usr/bin/env python3
"""
Test script for verifying the containerized PseudoScribe environment.

This script checks that all services are running properly and that the
Style API endpoints are accessible and functioning as expected.
"""

import argparse
import asyncio
import httpx
import json
import sys
import time
from typing import Dict, Any, List, Tuple

# Configuration
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TENANT_ID = "test-tenant"
DEFAULT_TIMEOUT = 30  # seconds


class ContainerTester:
    """Test the containerized PseudoScribe environment."""

    def __init__(self, base_url: str, tenant_id: str, timeout: int):
        """Initialize the tester with configuration."""
        self.base_url = base_url
        self.tenant_id = tenant_id
        self.timeout = timeout
        self.headers = {"X-Tenant-ID": tenant_id} if tenant_id else {}
        self.results: List[Tuple[str, bool, str]] = []

    async def wait_for_api(self) -> bool:
        """Wait for the API to become available."""
        print(f"Waiting for API at {self.base_url} (timeout: {self.timeout}s)...")
        
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(f"{self.base_url}/docs")
                    if response.status_code == 200:
                        print("✅ API is available!")
                        return True
            except (httpx.ConnectError, httpx.ReadTimeout):
                pass
            
            # Wait before retrying
            await asyncio.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()
        
        print("\n❌ API did not become available within the timeout period.")
        return False

    async def test_style_analyze(self) -> bool:
        """Test the style analysis endpoint."""
        test_name = "Style Analysis"
        url = f"{self.base_url}/api/style/analyze"
        
        payload = {
            "text": "This is a sample text for style analysis. It demonstrates how the Style API works."
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if all(k in result for k in ["complexity", "formality", "tone", "readability"]):
                        self.results.append((test_name, True, "All style characteristics present"))
                        return True
                    else:
                        self.results.append((test_name, False, f"Missing style characteristics: {result}"))
                        return False
                else:
                    self.results.append((test_name, False, f"HTTP {response.status_code}: {response.text}"))
                    return False
        except Exception as e:
            self.results.append((test_name, False, f"Exception: {str(e)}"))
            return False

    async def test_style_compare(self) -> bool:
        """Test the style comparison endpoint."""
        test_name = "Style Comparison"
        url = f"{self.base_url}/api/style/compare"
        
        payload = {
            "text1": "This is a formal document written in a professional tone.",
            "text2": "Hey there! This is written in a casual style, you know?"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if all(k in result for k in ["overall", "vector_similarity", "characteristics_similarity"]):
                        self.results.append((test_name, True, "All comparison metrics present"))
                        return True
                    else:
                        self.results.append((test_name, False, f"Missing comparison metrics: {result}"))
                        return False
                else:
                    self.results.append((test_name, False, f"HTTP {response.status_code}: {response.text}"))
                    return False
        except Exception as e:
            self.results.append((test_name, False, f"Exception: {str(e)}"))
            return False

    async def test_style_adapt(self) -> bool:
        """Test the style adaptation endpoint."""
        test_name = "Style Adaptation"
        url = f"{self.base_url}/api/style/adapt"
        
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
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if all(k in result for k in ["original_text", "adapted_text", "similarity"]):
                        self.results.append((test_name, True, "Adaptation successful"))
                        return True
                    else:
                        self.results.append((test_name, False, f"Missing adaptation fields: {result}"))
                        return False
                else:
                    self.results.append((test_name, False, f"HTTP {response.status_code}: {response.text}"))
                    return False
        except Exception as e:
            self.results.append((test_name, False, f"Exception: {str(e)}"))
            return False

    async def test_style_check(self) -> bool:
        """Test the style check endpoint."""
        test_name = "Style Check"
        url = f"{self.base_url}/api/style/check"
        
        payload = {
            "text": "This is a sample text that we want to check against a target style.",
            "target_style": {
                "complexity": 0.5,
                "formality": 0.7,
                "tone": 0.6,
                "readability": 0.8
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if "consistency" in result:
                        self.results.append((test_name, True, "Style check successful"))
                        return True
                    else:
                        self.results.append((test_name, False, f"Missing consistency metric: {result}"))
                        return False
                else:
                    self.results.append((test_name, False, f"HTTP {response.status_code}: {response.text}"))
                    return False
        except Exception as e:
            self.results.append((test_name, False, f"Exception: {str(e)}"))
            return False

    async def run_all_tests(self) -> bool:
        """Run all tests and return overall success status."""
        if not await self.wait_for_api():
            return False
        
        print("\nRunning Style API tests...")
        await self.test_style_analyze()
        await self.test_style_compare()
        await self.test_style_adapt()
        await self.test_style_check()
        
        return self.print_results()

    def print_results(self) -> bool:
        """Print test results and return overall success status."""
        print("\n=== Test Results ===")
        
        all_passed = True
        for name, passed, message in self.results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {name}: {message}")
            if not passed:
                all_passed = False
        
        print("\n=== Summary ===")
        if all_passed:
            print("✅ All tests passed! The containerized environment is working correctly.")
        else:
            print("❌ Some tests failed. Please check the container logs for more information.")
        
        return all_passed


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test the containerized PseudoScribe environment")
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help=f"Base URL of the API (default: {DEFAULT_BASE_URL})")
    parser.add_argument("--tenant", default=DEFAULT_TENANT_ID, help=f"Tenant ID to use (default: {DEFAULT_TENANT_ID})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--no-tenant", action="store_true", help="Don't use a tenant ID (test public endpoints)")
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    tenant_id = None if args.no_tenant else args.tenant
    
    tester = ContainerTester(args.url, tenant_id, args.timeout)
    success = await tester.run_all_tests()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    print("PseudoScribe Container Test")
    print("==========================")
    asyncio.run(main())
