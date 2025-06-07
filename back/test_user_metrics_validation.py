#!/usr/bin/env python3
"""
Test script to validate user-specific metrics are correct and not inflated.
"""

import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:5000"

def test_user_metrics(token, user_id):
    """Test and validate user-specific metrics."""
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    print("Testing User-Specific Metrics Validation")
    print("=" * 50)
    
    # Test 1: Dashboard Metrics
    print(f"\n1. Testing Dashboard Metrics for user {user_id}")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/user/{user_id}/metrics", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Predictions Generated (this month): {data.get('predictions_generated', 0)}")
            print(f"Model Accuracy: {data.get('model_accuracy', 0)}% (rounded to 2 decimals)")
            print(f"Crops Analyzed (distinct): {data.get('crops_analyzed', 0)}")
            print(f"New Crops (last 30 days): {data.get('new_crops', 0)}")
            print(f"Weekly Predictions: {data.get('weekly_predictions', 0)}")
            
            # Validate the data
            if data.get('predictions_generated', 0) > 1000:
                print("WARNING: Predictions count seems too high for a single user!")
            if data.get('crops_analyzed', 0) > 20:
                print("WARNING: Crops analyzed count seems too high!")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Monthly Predictions
    print(f"\n2. Testing Monthly Predictions for user {user_id}")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/user/{user_id}/monthly-predictions", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            monthly_data = data.get('data', [])
            print(f"Monthly predictions data:")
            total_predictions = 0
            for month in monthly_data:
                print(f"  - {month['month']}: {month['predictions']} predictions")
                total_predictions += month['predictions']
            print(f"Total predictions (6 months): {total_predictions}")
            
            if total_predictions > 5000:
                print("WARNING: Total predictions over 6 months seems too high!")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Crop Distribution
    print(f"\n3. Testing Crop Distribution for user {user_id}")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/user/{user_id}/crop-distribution", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            crops = data.get('data', [])
            print(f"Crop distribution (last 30 days):")
            total_count = 0
            for crop in crops:
                print(f"  - {crop['crop']}: {crop['count']} predictions")
                total_count += crop['count']
            print(f"Total predictions in distribution: {total_count}")
            
            if len(crops) > 10:
                print("WARNING: Too many different crops for a single user!")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: User Analytics Endpoints
    print(f"\n4. Testing User Analytics Endpoints")
    
    # Response Time Data
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/user/response-time-data", headers=headers)
        print(f"\nResponse Time Data - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Data points: {len(data.get('data', []))}")
    except Exception as e:
        print(f"Error: {e}")
    
    # User Predictions
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/user/predictions", headers=headers)
        print(f"\nUser Predictions - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            print(f"Recent predictions: {len(predictions)}")
            if predictions:
                print(f"Sample: {predictions[0]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Model Metrics
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/user/model-metrics", headers=headers)
        print(f"\nModel Metrics - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            metrics = data.get('metrics', [])
            for metric in metrics:
                print(f"  - {metric['name']}: {metric['value']}% (target: {metric['target']}%)")
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
            user_id = data.get('user_id')
            print(f"Login successful! User: {data.get('username')} (ID: {user_id})")
            return token, user_id
        else:
            print(f"Login failed: {response.json()}")
            return None, None
    except Exception as e:
        print(f"Login error: {e}")
        return None, None

if __name__ == "__main__":
    # First, get authentication token
    token, user_id = login_and_get_token()
    
    if token and user_id:
        # Test the metrics
        test_user_metrics(token, user_id)
    else:
        print("Cannot test metrics without authentication.")