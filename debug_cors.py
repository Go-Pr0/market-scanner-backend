#!/usr/bin/env python3
"""
Debug script to test CORS and OPTIONS requests
"""

import requests
import json
import sys

def test_cors_and_options(base_url="http://localhost:8000"):
    """Test CORS and OPTIONS requests to the auth endpoints"""
    
    print(f"Testing CORS and OPTIONS requests to {base_url}")
    print("=" * 60)
    
    # Test 1: OPTIONS request to check-email
    print("\n1. Testing OPTIONS request to /api/auth/check-email")
    try:
        response = requests.options(
            f"{base_url}/api/auth/check-email",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: POST request to check-email
    print("\n2. Testing POST request to /api/auth/check-email")
    try:
        response = requests.post(
            f"{base_url}/api/auth/check-email",
            json={"email": "test@example.com"},
            headers={
                "Origin": "http://localhost:3000",
                "Content-Type": "application/json"
            }
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Health check
    print("\n3. Testing health endpoint")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Check CORS headers on a simple GET request
    print("\n4. Testing CORS headers on health endpoint")
    try:
        response = requests.get(
            f"{base_url}/health",
            headers={"Origin": "http://localhost:3000"}
        )
        print(f"   Status: {response.status_code}")
        cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        print(f"   CORS Headers: {cors_headers}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_cors_and_options(base_url)