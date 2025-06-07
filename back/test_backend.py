#!/usr/bin/env python3
"""
Comprehensive backend test with timeouts.
"""
import sys
import signal
import requests
import time
import subprocess
import json
from contextlib import contextmanager

@contextmanager
def timeout(duration):
    """Context manager for timing out code execution"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {duration} seconds")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(duration)
    
    try:
        yield
    finally:
        signal.alarm(0)

def test_database_connection():
    """Test direct database connection"""
    print("Testing database connection...")
    try:
        with timeout(10):
            from test_db_connection import test_db_connection
            result = test_db_connection()
            if result:
                print("✓ Database connection successful")
                return True
            else:
                print("✗ Database connection failed")
                return False
    except TimeoutError:
        print("✗ Database connection timed out")
        return False
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        return False

def test_inference_engine():
    """Test inference engine"""
    print("Testing inference engine...")
    try:
        with timeout(30):
            from test_inference import test_inference_engine
            return test_inference_engine()
    except TimeoutError:
        print("✗ Inference engine test timed out")
        return False
    except Exception as e:
        print(f"✗ Inference engine error: {e}")
        return False

def start_backend_server():
    """Start the backend server"""
    print("Starting backend server...")
    try:
        # Start server in background
        process = subprocess.Popen([
            'python3', '/home/Ciscos/back/app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✓ Backend server started")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"✗ Backend server failed to start: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"✗ Error starting backend server: {e}")
        return None

def test_api_endpoints(base_url="http://localhost:8443"):
    """Test API endpoints with timeout"""
    print("Testing API endpoints...")
    
    endpoints = [
        ("/health", "GET"),
        ("/crops", "GET"),
        ("/features", "GET")
    ]
    
    for endpoint, method in endpoints:
        try:
            with timeout(10):
                if method == "GET":
                    response = requests.get(f"{base_url}{endpoint}", timeout=5)
                    if response.status_code == 200:
                        print(f"✓ {endpoint} endpoint working")
                    else:
                        print(f"✗ {endpoint} endpoint failed: {response.status_code}")
                        return False
        except TimeoutError:
            print(f"✗ {endpoint} endpoint timed out")
            return False
        except requests.exceptions.ConnectRefused:
            print(f"✗ Cannot connect to {endpoint}")
            return False
        except Exception as e:
            print(f"✗ {endpoint} error: {e}")
            return False
    
    # Test prediction endpoint
    try:
        with timeout(15):
            test_data = {
                'N': 90,
                'P': 42,
                'K': 43,
                'temperature': 20.87,
                'humidity': 82.00,
                'ph': 6.50,
                'rainfall': 202.93
            }
            
            response = requests.post(
                f"{base_url}/predict", 
                json=test_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Prediction endpoint working: {result.get('predicted_crop')}")
                return True
            else:
                print(f"✗ Prediction endpoint failed: {response.status_code}")
                return False
                
    except TimeoutError:
        print("✗ Prediction endpoint timed out")
        return False
    except Exception as e:
        print(f"✗ Prediction endpoint error: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Backend Test Suite ===\n")
    
    tests = [
        test_database_connection,
        test_inference_engine,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    # Start server and test endpoints
    server_process = start_backend_server()
    if server_process:
        try:
            time.sleep(3)  # Give server time to fully start
            if test_api_endpoints():
                passed += 1
            total += 1
        finally:
            # Stop server
            server_process.terminate()
            server_process.wait()
            print("✓ Backend server stopped")
    else:
        total += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return True
    else:
        print("✗ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)