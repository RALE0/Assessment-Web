"""
Test script for user-specific dashboard endpoints
"""

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:5002"
TEST_USER_ID = 1  # Replace with actual test user ID
TEST_TOKEN = "your_test_token_here"  # Replace with actual JWT token

headers = {
    "Authorization": f"Bearer {TEST_TOKEN}",
    "Content-Type": "application/json"
}

def test_user_metrics():
    """Test user-specific metrics endpoint"""
    print("\n=== Testing User Metrics ===")
    
    url = f"{BASE_URL}/api/dashboard/user/{TEST_USER_ID}/metrics"
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response Data:")
            print(f"  Predictions Generated: {data.get('predictions_generated')}")
            print(f"  Predictions Change: {data.get('predictions_change')}%")
            print(f"  Model Accuracy: {data.get('model_accuracy')}%")
            print(f"  Accuracy Change: {data.get('accuracy_change')}%")
            print(f"  Crops Analyzed: {data.get('crops_analyzed')}")
            print(f"  New Crops: {data.get('new_crops')}")
            print(f"  Active Users: {data.get('active_users')}")
            print(f"  Users Change: {data.get('users_change')}%")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing user metrics: {e}")

def test_user_monthly_predictions():
    """Test user-specific monthly predictions endpoint"""
    print("\n=== Testing User Monthly Predictions ===")
    
    url = f"{BASE_URL}/api/dashboard/user/{TEST_USER_ID}/monthly-predictions"
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Monthly Predictions:")
            for month_data in data.get('data', []):
                print(f"  {month_data['month']}: {month_data['predictions']} predictions")
            print(f"Timestamp: {data.get('timestamp')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing monthly predictions: {e}")

def test_user_crop_distribution():
    """Test user-specific crop distribution endpoint"""
    print("\n=== Testing User Crop Distribution ===")
    
    url = f"{BASE_URL}/api/dashboard/user/{TEST_USER_ID}/crop-distribution"
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Crop Distribution:")
            for crop_data in data.get('data', []):
                print(f"  {crop_data['crop']}: {crop_data['count']} (Color: {crop_data['color']})")
            print(f"Timestamp: {data.get('timestamp')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing crop distribution: {e}")

def test_unauthorized_access():
    """Test accessing another user's data (should fail)"""
    print("\n=== Testing Unauthorized Access ===")
    
    OTHER_USER_ID = 999  # Different user ID
    url = f"{BASE_URL}/api/dashboard/user/{OTHER_USER_ID}/metrics"
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("Success: Unauthorized access properly blocked")
            print(f"Error message: {response.json().get('error')}")
        else:
            print(f"Unexpected response: {response.text}")
            
    except Exception as e:
        print(f"Error testing unauthorized access: {e}")

def test_no_auth():
    """Test accessing endpoints without authentication"""
    print("\n=== Testing No Authentication ===")
    
    url = f"{BASE_URL}/api/dashboard/user/{TEST_USER_ID}/metrics"
    
    try:
        response = requests.get(url)  # No headers
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("Success: Authentication properly required")
            print(f"Error message: {response.json().get('error')}")
        else:
            print(f"Unexpected response: {response.text}")
            
    except Exception as e:
        print(f"Error testing no auth: {e}")

def main():
    """Run all tests"""
    print("Starting User Dashboard Endpoint Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print("=" * 50)
    
    # NOTE: You need to get a valid JWT token first
    # You can do this by logging in with the /api/auth/login endpoint
    
    if TEST_TOKEN == "your_test_token_here":
        print("\nWARNING: Please update TEST_TOKEN with a valid JWT token")
        print("You can get a token by logging in with POST /api/auth/login")
        print("Example:")
        print('  curl -X POST http://localhost:5002/api/auth/login \\')
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"username": "your_username", "password": "your_password"}\'')
        return
    
    # Run tests
    test_user_metrics()
    test_user_monthly_predictions()
    test_user_crop_distribution()
    test_unauthorized_access()
    test_no_auth()
    
    print("\n" + "=" * 50)
    print("All tests completed")

if __name__ == "__main__":
    main()