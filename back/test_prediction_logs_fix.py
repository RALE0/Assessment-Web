#!/usr/bin/env python3
"""
Test script to verify prediction logs functionality after fixes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prediction_log_models import PredictionLogDatabase
import json

def test_prediction_logs():
    """Test prediction logs database functionality."""
    print("=== Testing Prediction Logs Functionality ===\n")
    
    # Database configuration
    DB_CONFIG = {
        'host': '172.28.69.148',
        'port': 5432,
        'user': 'cropapi',
        'password': 'cropapi123',
        'database': 'crop_recommendations',
        'connect_timeout': 10
    }
    
    try:
        # Initialize database
        db = PredictionLogDatabase(DB_CONFIG)
        user_id = '567ab65a-486e-486d-89de-c06aa6fee544'
        
        print(f"1. Testing get_user_prediction_logs for user: {user_id}")
        result = db.get_user_prediction_logs(user_id)
        print(f"   ✓ Success! Found {len(result['logs'])} logs")
        print(f"   ✓ Total count: {result['pagination']['total']}")
        print(f"   ✓ Has more: {result['pagination']['hasMore']}")
        
        if result['logs']:
            first_log = result['logs'][0]
            print(f"   ✓ First log: {first_log['predictedCrop']} (confidence: {first_log['confidence']})")
        
        print(f"\n2. Testing get_user_prediction_statistics for user: {user_id}")
        stats = db.get_user_prediction_statistics(user_id)
        if stats:
            print(f"   ✓ Total predictions: {stats['statistics']['totalPredictions']}")
            print(f"   ✓ Success rate: {stats['statistics']['successRate']}%")
            print(f"   ✓ Avg confidence: {stats['statistics']['avgConfidence']}")
            print(f"   ✓ Most predicted crop: {stats['statistics']['mostPredictedCrop']}")
            print(f"   ✓ Crop distribution items: {len(stats['cropDistribution'])}")
            print(f"   ✓ Timeline items: {len(stats['timeline'])}")
        else:
            print("   ✗ No statistics returned")
        
        print(f"\n3. Testing with filters")
        filtered_result = db.get_user_prediction_logs(user_id, filters={'crop': 'wheat'})
        print(f"   ✓ Filtered logs (wheat): {len(filtered_result['logs'])}")
        
        print(f"\n4. Testing export functionality")
        csv_content = db.export_user_prediction_logs_csv(user_id)
        if csv_content:
            lines = csv_content.split('\n')
            print(f"   ✓ CSV export successful: {len(lines)} lines")
            print(f"   ✓ Header: {lines[0]}")
        else:
            print("   ✗ CSV export failed")
        
        print(f"\n5. Testing pagination")
        paginated_result = db.get_user_prediction_logs(
            user_id, 
            pagination={'limit': 10, 'offset': 0}
        )
        print(f"   ✓ Paginated logs: {len(paginated_result['logs'])}")
        print(f"   ✓ Pagination info: {paginated_result['pagination']}")
        
        print("\n=== All Tests Passed! ===")
        return True
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_prediction_logs()
    sys.exit(0 if success else 1)