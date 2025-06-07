#!/usr/bin/env python3
"""
Script to verify all endpoints return real user data starting from 0.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_endpoints_with_new_user():
    """Test endpoints with a new user to verify they start from 0."""
    
    print("Testing Dashboard Endpoints with New User")
    print("=" * 50)
    
    # Create a new test user
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_user = {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "test123"
    }
    
    print(f"\n1. Creating new user: {new_user['username']}")
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=new_user)
        if response.status_code == 201:
            print("User created successfully")
        else:
            print(f"Failed to create user: {response.json()}")
            return
    except Exception as e:
        print(f"Error creating user: {e}")
        return
    
    # Login with new user
    print("\n2. Logging in with new user")
    try:
        login_data = {
            "username": new_user['username'],
            "password": new_user['password']
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            user_id = data.get('user_id')
            print(f"Login successful! Token obtained")
        else:
            print(f"Login failed: {response.json()}")
            return
    except Exception as e:
        print(f"Login error: {e}")
        return
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # Test all dashboard endpoints
    print("\n3. Testing Dashboard Metrics (should all be 0)")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/user/{user_id}/metrics", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"  - Predictions Generated: {data.get('predictions_generated')} (expected: 0)")
            print(f"  - Model Accuracy: {data.get('model_accuracy')}% (expected: 0)")
            print(f"  - Crops Analyzed: {data.get('crops_analyzed')} (expected: 0)")
            print(f"  - New Crops: {data.get('new_crops')} (expected: 0)")
            print(f"  - Weekly Predictions: {data.get('weekly_predictions')} (expected: 0)")
            
            # Verify all values are 0
            if (data.get('predictions_generated', -1) == 0 and
                data.get('crops_analyzed', -1) == 0 and
                data.get('weekly_predictions', -1) == 0):
                print("  ✓ All metrics correctly start at 0")
            else:
                print("  ✗ ERROR: Some metrics are not 0!")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n4. Testing Monthly Predictions (should all be 0)")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/user/{user_id}/monthly-predictions", headers=headers)
        if response.status_code == 200:
            data = response.json()
            monthly_data = data.get('data', [])
            all_zero = True
            for month in monthly_data:
                print(f"  - {month['month']}: {month['predictions']} predictions")
                if month['predictions'] != 0:
                    all_zero = False
            
            if all_zero:
                print("  ✓ All monthly predictions correctly start at 0")
            else:
                print("  ✗ ERROR: Some months have non-zero predictions!")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n5. Testing Crop Distribution (should be empty)")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/user/{user_id}/crop-distribution", headers=headers)
        if response.status_code == 200:
            data = response.json()
            crops = data.get('data', [])
            if len(crops) == 0:
                print("  ✓ Crop distribution correctly starts empty")
            else:
                print(f"  ✗ ERROR: Found {len(crops)} crops for new user!")
                for crop in crops:
                    print(f"    - {crop['crop']}: {crop['count']}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n6. Testing User Analytics Endpoints")
    
    # Test response time data
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/user/response-time-data", headers=headers)
        if response.status_code == 200:
            data = response.json()
            time_data = data.get('data', [])
            print(f"  - Response Time Data: {len(time_data)} points (expected: 0)")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test user predictions
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/user/predictions", headers=headers)
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            print(f"  - User Predictions: {len(predictions)} predictions (expected: 0)")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test model metrics
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/user/model-metrics", headers=headers)
        if response.status_code == 200:
            data = response.json()
            metrics = data.get('metrics', [])
            print(f"  - Model Metrics: {len(metrics)} metrics")
            if len(metrics) == 0:
                print("    ✓ No metrics for new user (correct)")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n7. Testing Compatibility Endpoints")
    
    # Test compatibility dashboard metrics
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"  - Compatibility Metrics: predictions_generated={data.get('predictions_generated')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_endpoints_with_new_user()