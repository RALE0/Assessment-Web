#!/usr/bin/env python3
"""
Test script for user-specific analytics endpoints.
"""

import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:5000"

def test_user_analytics_endpoints(token):
    """Test all user-specific analytics endpoints with authentication."""
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    print("Testing User-Specific Analytics Endpoints")
    print("=" * 50)
    
    # Test 1: User Response Time Data
    print("\n1. Testing /api/analytics/user/response-time-data")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/user/response-time-data", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response time data points: {len(data.get('data', []))}")
            if data.get('data'):
                print(f"Sample data: {data['data'][0]}")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: User Predictions
    print("\n2. Testing /api/analytics/user/predictions")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/user/predictions", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Predictions count: {len(data.get('predictions', []))}")
            if data.get('predictions'):
                print(f"Sample prediction: {data['predictions'][0]}")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: User Model Metrics
    print("\n3. Testing /api/analytics/user/model-metrics")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/user/model-metrics", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Metrics count: {len(data.get('metrics', []))}")
            for metric in data.get('metrics', []):
                print(f"  - {metric['name']}: {metric['value']} (target: {metric['target']}, status: {metric['status']})")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: User Performance Metrics
    print("\n4. Testing /api/analytics/user/performance-metrics")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/user/performance-metrics", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Average response time: {data.get('average_response_time', 0)}s")
            print(f"P95 response time: {data.get('p95_response_time', 0)}s")
            print(f"P99 response time: {data.get('p99_response_time', 0)}s")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Test without authentication
    print("\n5. Testing endpoints without authentication")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/user/response-time-data")
        print(f"Status Code (no auth): {response.status_code}")
        print(f"Expected: 401 Unauthorized")
        if response.status_code != 401:
            print("WARNING: Endpoint accessible without authentication!")
    except Exception as e:
        print(f"Error: {e}")

def login_and_get_token():
    """Login and get authentication token."""
    print("Logging in to get authentication token...")
    
    # Use test credentials
    login_data = {
        "username": "ian",
        "password": "ian123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"Login successful! User: {data.get('username')}")
            return token
        else:
            print(f"Login failed: {response.json()}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

if __name__ == "__main__":
    # First, get authentication token
    token = login_and_get_token()
    
    if token:
        # Test the endpoints
        test_user_analytics_endpoints(token)
    else:
        print("Cannot test endpoints without authentication token.")
        print("\nTo test manually, use curl with authentication:")
        print("curl -H 'Authorization: Bearer YOUR_TOKEN' http://localhost:5000/api/analytics/user/response-time-data")