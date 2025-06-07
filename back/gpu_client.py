#!/usr/bin/env python3
"""
GPU Client - HTTP client to communicate with the GPU inference API
"""
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class GPUInferenceClient:
    """Client for communicating with the GPU inference API."""
    
    def __init__(self, base_url: str = "http://172.28.69.2:8081", timeout: int = 30):
        """
        Initialize the GPU inference client.
        
        Args:
            base_url: Base URL of the GPU inference API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CropRecommendation-Backend/1.0'
        })
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the GPU inference API is healthy."""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GPU API health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Make crop prediction using the GPU inference API.
        
        Args:
            features: Dictionary containing the 7 required features
            
        Returns:
            Dictionary containing prediction results
        """
        try:
            response = self.session.post(
                f"{self.base_url}/predict",
                json=features,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            # Transform response to match original inference engine format
            return {
                'success': True,
                'predicted_crop': result['predicted_crop'],
                'confidence': result['confidence'],
                'top_predictions': result['top_predictions'],
                'input_features': result['input_features'],
                'warnings': result.get('warnings')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GPU API prediction failed: {e}")
            return {
                'success': False,
                'error': f'GPU inference service unavailable: {str(e)}',
                'predicted_crop': None,
                'confidence': 0.0
            }
        except Exception as e:
            logger.error(f"Unexpected error in GPU prediction: {e}")
            return {
                'success': False,
                'error': f'Prediction processing error: {str(e)}',
                'predicted_crop': None,
                'confidence': 0.0
            }
    
    def get_crops(self) -> Dict[str, Any]:
        """Get list of supported crops from the GPU API."""
        try:
            response = self.session.get(
                f"{self.base_url}/crops",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GPU API get crops failed: {e}")
            return {
                'crops': [],
                'count': 0,
                'error': str(e)
            }
    
    def get_features(self) -> Dict[str, Any]:
        """Get feature information from the GPU API."""
        try:
            response = self.session.get(
                f"{self.base_url}/features",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GPU API get features failed: {e}")
            return {
                'features': [],
                'count': 0,
                'error': str(e)
            }
    
    @property
    def label_mapping(self) -> Dict[str, int]:
        """Get label mapping (for compatibility with original inference engine)."""
        try:
            crops_response = self.get_crops()
            if 'crops' in crops_response:
                # Create a simple mapping (this is a fallback)
                crops = crops_response['crops']
                return {crop: idx for idx, crop in enumerate(crops)}
            return {}
        except Exception as e:
            logger.error(f"Failed to get label mapping: {e}")
            return {}
    
    @property
    def feature_names(self) -> list:
        """Get feature names (for compatibility with original inference engine)."""
        return ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
    
    @property
    def feature_ranges(self) -> Dict[str, tuple]:
        """Get feature ranges (for compatibility with original inference engine)."""
        return {
            "N": (0, 200),
            "P": (0, 150),
            "K": (0, 250),
            "temperature": (8, 45),
            "humidity": (10, 100),
            "ph": (3.5, 10.0),
            "rainfall": (20, 3000)
        }
    
    @property
    def models(self) -> Dict[str, Any]:
        """Get models info (for compatibility with original inference engine)."""
        try:
            health = self.health_check()
            if health.get('status') == 'healthy':
                return {'RemoteGPUModel': True}  # Dummy entry for compatibility
            return {}
        except Exception:
            return {}