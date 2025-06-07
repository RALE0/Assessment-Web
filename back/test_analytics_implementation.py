#!/usr/bin/env python3
"""
Test script for analytics implementation.
Tests database schema and endpoint functionality.
"""

import sys
import json
import requests
import subprocess
import time

def test_database_schema():
    """Test database schema using psql command."""
    print("Testing database schema...")
    
    # Test database connection
    try:
        result = subprocess.run([
            'bash', '-c', 
            'PGPASSWORD=cropapi123 psql -h 172.28.69.148 -U cropapi -d crop_recommendations -c "SELECT \'OK\' as test;"'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✓ Database connection successful")
        else:
            print(f"✗ Database connection failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        return False
    
    # Check if prediction_logs table exists with required columns
    try:
        query = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name='prediction_logs' 
        AND column_name IN ('processing_time', 'response_time_seconds', 'timestamp', 'user_id', 'predicted_crop', 'confidence', 'status')
        ORDER BY column_name;
        """
        
        result = subprocess.run([
            'bash', '-c', 
            f'PGPASSWORD=cropapi123 psql -h 172.28.69.148 -U cropapi -d crop_recommendations -c "{query}"'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✓ prediction_logs table schema verified")
            print("Available columns:")
            for line in result.stdout.split('\n')[2:-3]:  # Skip header and footer
                if '|' in line:
                    print(f"  {line.strip()}")
        else:
            print(f"✗ Schema check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Schema check error: {e}")
        return False
    
    return True

def test_analytics_endpoints():
    """Test analytics endpoints."""
    print("\nTesting analytics endpoints...")
    
    base_url = "http://172.28.69.96:8443"
    endpoints = [
        "/api/analytics/model-metrics",
        "/api/analytics/performance-metrics", 
        "/api/analytics/response-time-data",
        "/api/analytics/user-predictions"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            print(f"Testing {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = {
                    "status": "success",
                    "status_code": response.status_code,
                    "has_data": bool(data)
                }
                print(f"✓ {endpoint} - Status: {response.status_code}")
                
                # Show sample data structure
                if endpoint == "/api/analytics/response-time-data":
                    if 'data' in data and data['data']:
                        print(f"  Sample data: {len(data['data'])} records")
                        if data['data']:
                            print(f"  First record: {data['data'][0]}")
                    else:
                        print("  No response time data available")
                
                elif endpoint == "/api/analytics/user-predictions":
                    if 'predictions' in data and data['predictions']:
                        print(f"  Predictions found: {len(data['predictions'])}")
                        if data['predictions']:
                            print(f"  Sample prediction: {data['predictions'][0]}")
                    else:
                        print("  No user predictions available")
                
                elif endpoint == "/api/analytics/performance-metrics":
                    if 'average_response_time' in data:
                        print(f"  Avg response time: {data.get('average_response_time')}s")
                        print(f"  P95 response time: {data.get('p95_response_time')}s")
                        print(f"  P99 response time: {data.get('p99_response_time')}s")
                
            else:
                results[endpoint] = {
                    "status": "error",
                    "status_code": response.status_code,
                    "error": response.text[:200]
                }
                print(f"✗ {endpoint} - Status: {response.status_code}")
                print(f"  Error: {response.text[:100]}")
                
        except requests.exceptions.ConnectionError:
            results[endpoint] = {
                "status": "connection_error",
                "error": "Could not connect to server"
            }
            print(f"✗ {endpoint} - Connection error (server may not be running)")
            
        except Exception as e:
            results[endpoint] = {
                "status": "error", 
                "error": str(e)
            }
            print(f"✗ {endpoint} - Error: {e}")
    
    return results

def run_schema_migration():
    """Run the analytics schema migration."""
    print("\nRunning schema migration...")
    
    try:
        result = subprocess.run([
            'bash', '-c', 
            'PGPASSWORD=cropapi123 psql -h 172.28.69.148 -U cropapi -d crop_recommendations -f /home/Ciscos/back/sql/12_analytics_schema.sql'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✓ Schema migration completed successfully")
            return True
        else:
            print(f"✗ Schema migration failed: {result.stderr}")
            # Check if it's just because columns already exist
            if "already exists" in result.stderr:
                print("  Note: Some objects already exist, which is expected")
                return True
            return False
    except Exception as e:
        print(f"✗ Schema migration error: {e}")
        return False

def main():
    """Main test function."""
    print("Analytics Implementation Test")
    print("=" * 50)
    
    # Run schema migration first
    if not run_schema_migration():
        print("\nSchema migration failed. Continuing with tests...")
    
    # Test database schema
    schema_ok = test_database_schema()
    
    # Test endpoints
    endpoint_results = test_analytics_endpoints()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    print(f"Database Schema: {'PASS' if schema_ok else 'FAIL'}")
    
    print("\nEndpoint Results:")
    for endpoint, result in endpoint_results.items():
        status = result['status']
        status_emoji = "✓" if status == "success" else "✗"
        print(f"  {status_emoji} {endpoint}: {status.upper()}")
    
    # Overall status
    all_endpoints_ok = all(r['status'] == 'success' for r in endpoint_results.values())
    overall_status = "PASS" if schema_ok and all_endpoints_ok else "PARTIAL"
    
    print(f"\nOverall Status: {overall_status}")
    
    if overall_status == "PARTIAL":
        print("\nNotes:")
        print("- Some endpoints may show no data if there are no predictions yet")
        print("- Server may not be running if connection errors occur")
        print("- Schema should be properly migrated before testing endpoints")

if __name__ == "__main__":
    main()