#!/usr/bin/env python3
"""
Test script to debug prediction history issue.
"""

import requests
import json
import time
import random

BASE_URL = "http://172.28.69.96:8443"

def test_complete_flow():
    """Test the complete flow: signup, predict, get history."""
    
    # Create a unique test user
    timestamp = int(time.time())
    test_username = f"testuser_{timestamp}"
    test_email = f"test_{timestamp}@example.com"
    test_password = "testpass123"
    
    print(f"Testing with user: {test_username}")
    
    # 1. Signup
    print("\n1. Testing signup...")
    signup_data = {
        "username": test_username,
        "email": test_email,
        "password": test_password
    }
    
    signup_response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
    print(f"Signup status: {signup_response.status_code}")
    
    if signup_response.status_code != 201:
        print(f"Signup failed: {signup_response.text}")
        return
    
    signup_result = signup_response.json()
    print(f"Signup response: {signup_result}")
    
    # Handle both possible response formats
    if 'data' in signup_result:
        token = signup_result['data']['token']
        user_id = signup_result['data']['user']['id']
    else:
        token = signup_result['token']
        user_id = signup_result['user']['id']
    
    print(f"User created: {user_id}")
    print(f"Token: {token[:50]}...")
    
    # 2. Make a prediction
    print("\n2. Making a prediction...")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    prediction_data = {
        "N": random.randint(10, 50),
        "P": random.randint(10, 50), 
        "K": random.randint(10, 50),
        "temperature": random.randint(15, 35),
        "humidity": random.randint(40, 90),
        "ph": round(random.uniform(5.5, 8.5), 1),
        "rainfall": random.randint(100, 300)
    }
    
    predict_response = requests.post(f"{BASE_URL}/predict", json=prediction_data, headers=headers)
    print(f"Prediction status: {predict_response.status_code}")
    
    if predict_response.status_code == 200:
        predict_result = predict_response.json()
        print(f"Predicted crop: {predict_result['predicted_crop']}")
        print(f"Confidence: {predict_result['confidence']:.4f}")
    else:
        print(f"Prediction failed: {predict_response.text}")
        return
    
    # 3. Save prediction log manually (to simulate what frontend does)
    print("\n3. Saving prediction log...")
    log_data = {
        "userId": user_id,
        "inputFeatures": prediction_data,
        "prediction": {
            "predicted_crop": predict_result['predicted_crop'],
            "confidence": predict_result['confidence'],
            "top_predictions": predict_result.get('top_predictions', [])
        },
        "processingTime": 100,
        "sessionId": "test_session"
    }
    
    log_response = requests.post(f"{BASE_URL}/api/prediction-logs", json=log_data, headers=headers)
    print(f"Log save status: {log_response.status_code}")
    
    if log_response.status_code == 201:
        log_result = log_response.json()
        print(f"Log response: {log_result}")
        
        # Handle both possible response formats
        if 'data' in log_result:
            log_id = log_result['data']['logId']
        else:
            log_id = log_result['logId']
        print(f"Log saved with ID: {log_id}")
    else:
        print(f"Log save failed: {log_response.text}")
    
    # 4. Wait a moment and then get history
    print("\n4. Getting prediction history...")
    time.sleep(1)
    
    history_url = f"{BASE_URL}/api/users/{user_id}/prediction-logs"
    history_response = requests.get(history_url, headers=headers)
    print(f"History status: {history_response.status_code}")
    
    if history_response.status_code == 200:
        history_result = history_response.json()
        print(f"Response structure: {list(history_result.keys())}")
        
        if 'data' in history_result:
            data = history_result['data']
            print(f"Data keys: {list(data.keys())}")
            logs = data.get('logs', [])
            pagination = data.get('pagination', {})
            
            print(f"Number of logs returned: {len(logs)}")
            print(f"Pagination: {pagination}")
            
            if logs:
                print("First log:")
                first_log = logs[0]
                for key, value in first_log.items():
                    if key == 'inputFeatures':
                        print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print("No logs returned!")
        else:
            print(f"Unexpected response format: {history_result}")
    else:
        print(f"History failed: {history_response.text}")

if __name__ == "__main__":
    test_complete_flow()