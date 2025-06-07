#!/usr/bin/env python3
"""
Test script for authentication endpoints.
Run this after the database is set up and the API is running.
"""

import requests
import json
import sys

BASE_URL = "http://172.28.69.96:8443"

def test_signup():
    """Test user registration."""
    print("Testing user signup...")
    
    signup_data = {
        "username": "testuser123",
        "email": "testuser@example.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
    print(f"Signup Status Code: {response.status_code}")
    print(f"Signup Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        return response.json().get('token')
    return None

def test_login():
    """Test user login."""
    print("\nTesting user login...")
    
    login_data = {
        "username": "testuser123",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login Status Code: {response.status_code}")
    print(f"Login Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        return response.json().get('token')
    return None

def test_verify(token):
    """Test token verification."""
    print("\nTesting token verification...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/verify", headers=headers)
    print(f"Verify Status Code: {response.status_code}")
    print(f"Verify Response: {json.dumps(response.json(), indent=2)}")

def test_protected_predict(token):
    """Test authenticated prediction."""
    print("\nTesting authenticated prediction...")
    
    headers = {"Authorization": f"Bearer {token}"}
    predict_data = {
        "N": 90,
        "P": 42,
        "K": 43,
        "temperature": 20.87,
        "humidity": 82.00,
        "ph": 6.50,
        "rainfall": 202.93
    }
    
    response = requests.post(f"{BASE_URL}/predict", json=predict_data, headers=headers)
    print(f"Predict Status Code: {response.status_code}")
    print(f"Predict Response: {json.dumps(response.json(), indent=2)}")

def test_logout(token):
    """Test user logout."""
    print("\nTesting user logout...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
    print(f"Logout Status Code: {response.status_code}")
    print(f"Logout Response: {json.dumps(response.json(), indent=2)}")

def test_password_reset():
    """Test password reset request."""
    print("\nTesting password reset...")
    
    reset_data = {"email": "testuser@example.com"}
    response = requests.post(f"{BASE_URL}/auth/reset-password", json=reset_data)
    print(f"Reset Status Code: {response.status_code}")
    print(f"Reset Response: {json.dumps(response.json(), indent=2)}")

def test_health_check():
    """Test health check endpoint."""
    print("Testing health check...")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health Status Code: {response.status_code}")
    print(f"Health Response: {json.dumps(response.json(), indent=2)}")

def main():
    """Run all authentication tests."""
    print(f"Testing authentication API at {BASE_URL}")
    print("=" * 50)
    
    try:
        # Test health check first
        test_health_check()
        
        # Test signup
        token = test_signup()
        if not token:
            print("Signup failed, trying login...")
            token = test_login()
        
        if token:
            # Test authenticated endpoints
            test_verify(token)
            test_protected_predict(token)
            test_logout(token)
        else:
            print("No valid token obtained, skipping authenticated tests")
        
        # Test password reset
        test_password_reset()
        
        print("\n" + "=" * 50)
        print("Authentication tests completed!")
        
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to {BASE_URL}")
        print("Make sure the API server is running")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()