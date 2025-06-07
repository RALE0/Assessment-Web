#!/usr/bin/env python3
"""
Test script to verify metrics update in real-time after predictions.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_real_time_updates():
    """Test that dashboard metrics update immediately after predictions."""
    
    print("Testing Real-Time Dashboard Updates")
    print("=" * 50)
    
    # Login
    print("\n1. Logging in...")
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
            print(f"Login successful! User: {data.get('username')}")
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
    
    # Get initial metrics
    print("\n2. Getting initial metrics...")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/user/{user_id}/metrics", headers=headers)
        if response.status_code == 200:
            initial_metrics = response.json()
            initial_predictions = initial_metrics.get('predictions_generated', 0)
            initial_crops = initial_metrics.get('crops_analyzed', 0)
            print(f"Initial predictions: {initial_predictions}")
            print(f"Initial crops analyzed: {initial_crops}")
        else:
            print(f"Failed to get initial metrics: {response.json()}")
            return
    except Exception as e:
        print(f"Error getting initial metrics: {e}")
        return
    
    # Make a prediction
    print("\n3. Making a test prediction...")
    prediction_data = {
        "N": 90,
        "P": 42,
        "K": 43,
        "temperature": 20.87,
        "humidity": 82.0,
        "ph": 6.5,
        "rainfall": 202.9
    }
    
    try:
        response = requests.post(f"{BASE_URL}/predict", json=prediction_data, headers=headers)
        if response.status_code == 200:
            prediction_result = response.json()
            predicted_crop = prediction_result.get('predicted_crop')
            confidence = prediction_result.get('confidence')
            print(f"Prediction successful! Crop: {predicted_crop}, Confidence: {confidence:.2f}")
        else:
            print(f"Prediction failed: {response.json()}")
            return
    except Exception as e:
        print(f"Prediction error: {e}")
        return
    
    # Wait a moment for database to update
    print("\n4. Waiting 2 seconds for processing...")
    time.sleep(2)
    
    # Check metrics immediately after prediction
    print("\n5. Checking metrics immediately after prediction...")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/user/{user_id}/metrics", headers=headers)
        if response.status_code == 200:
            updated_metrics = response.json()
            updated_predictions = updated_metrics.get('predictions_generated', 0)
            updated_crops = updated_metrics.get('crops_analyzed', 0)
            
            print(f"Updated predictions: {updated_predictions}")
            print(f"Updated crops analyzed: {updated_crops}")
            
            # Check if metrics increased
            predictions_increased = updated_predictions > initial_predictions
            crops_may_increase = updated_crops >= initial_crops  # May stay same if crop already seen
            
            if predictions_increased:
                print("✓ Predictions count increased correctly!")
            else:
                print("✗ Predictions count did NOT increase")
            
            if crops_may_increase:
                print("✓ Crops count is correct")
            else:
                print("✗ Crops count decreased unexpectedly")
            
        else:
            print(f"Failed to get updated metrics: {response.json()}")
            return
    except Exception as e:
        print(f"Error getting updated metrics: {e}")
        return
    
    # Test crop distribution update
    print("\n6. Checking crop distribution...")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/user/{user_id}/crop-distribution", headers=headers)
        if response.status_code == 200:
            crop_data = response.json()
            crops = crop_data.get('data', [])
            
            # Look for the predicted crop
            predicted_crop_found = False
            for crop in crops:
                if crop['crop'] == predicted_crop:
                    predicted_crop_found = True
                    print(f"✓ Found predicted crop '{predicted_crop}' with count: {crop['count']}")
                    break
            
            if not predicted_crop_found and len(crops) > 0:
                print(f"Note: Predicted crop '{predicted_crop}' not in top 5, but distribution updated")
            elif len(crops) == 0:
                print("Note: No crops in distribution yet (expected for new users)")
                
        else:
            print(f"Failed to get crop distribution: {response.json()}")
    except Exception as e:
        print(f"Error getting crop distribution: {e}")
    
    # Test cache clearing endpoint
    print("\n7. Testing manual cache clear...")
    try:
        response = requests.post(f"{BASE_URL}/api/dashboard/cache/clear", headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Cache cleared: {result['message']}")
        else:
            print(f"Failed to clear cache: {response.json()}")
    except Exception as e:
        print(f"Error clearing cache: {e}")
    
    print(f"\n8. Test completed!")
    print(f"Summary:")
    print(f"  - Initial predictions: {initial_predictions}")
    print(f"  - Final predictions: {updated_predictions}")
    print(f"  - Increase: +{updated_predictions - initial_predictions}")

if __name__ == "__main__":
    test_real_time_updates()