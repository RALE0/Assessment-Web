#!/usr/bin/env python3
"""
Test script for the inference engine with timeout handling.
"""
import sys
import signal
from contextlib import contextmanager
from gpu_client import GPUInferenceClient

@contextmanager
def timeout(duration):
    """Context manager for timing out code execution"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {duration} seconds")
    
    # Set the signal handler and a timeout alarm
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(duration)
    
    try:
        yield
    finally:
        # Disable the alarm
        signal.alarm(0)

def test_inference_engine():
    """Test the GPU inference client initialization and prediction."""
    print("Testing GPU inference client...")
    
    try:
        # Test initialization with timeout
        with timeout(30):
            engine = GPUInferenceClient(base_url="http://172.28.69.2:8081")
            health_check = engine.health_check()
            print(f"✓ GPU client initialized, status: {health_check.get('status')}")
            print(f"✓ Available models: {list(engine.models.keys())}")
            print(f"✓ Feature names: {engine.feature_names}")
        
        # Test prediction with timeout
        test_features = {
            'N': 90,
            'P': 42,
            'K': 43,
            'temperature': 20.87,
            'humidity': 82.00,
            'ph': 6.50,
            'rainfall': 202.93
        }
        
        with timeout(10):
            result = engine.predict(test_features)
            print(f"✓ Prediction successful: {result['predicted_crop']}")
            print(f"✓ Confidence: {result['confidence']:.4f}")
            return True
            
    except TimeoutError as e:
        print(f"✗ Test timed out: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_inference_engine()
    sys.exit(0 if success else 1)