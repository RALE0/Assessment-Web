const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '172.28.69.96:8443';

export interface PredictionRequest {
  N: number;
  P: number;
  K: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
}

export interface PredictionResponse {
  predicted_crop: string;
  confidence: number;
  top_predictions: {
    crop: string;
    probability: number;
  }[];
  input_features: {
    N: number;
    P: number;
    K: number;
    temperature: number;
    humidity: number;
    ph: number;
    rainfall: number;
  };
  warnings?: string;
  timestamp: string;
}

export interface ApiError {
  error: string;
  details?: string;
  timestamp: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  database: string;
  models_loaded: number;
  available_models: string[];
}

export interface Crop {
  name: string;
}

export interface Feature {
  name: string;
  min_value: number;
  max_value: number;
  unit: string;
  description: string;
}

class CropRecommendationAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async checkHealth(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`);
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    
    return response.json();
  }

  async predictCrop(data: PredictionRequest): Promise<PredictionResponse> {
    const response = await fetch(`${this.baseUrl}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (!response.ok) {
      const error: ApiError = result;
      throw new Error(error.error || 'Prediction failed');
    }

    return result;
  }

  async getCrops(): Promise<{ crops: string[]; count: number; timestamp: string }> {
    const response = await fetch(`${this.baseUrl}/crops`);
    
    if (!response.ok) {
      throw new Error(`Failed to get crops: ${response.status}`);
    }
    
    return response.json();
  }

  async getFeatures(): Promise<{ features: Feature[]; count: number; timestamp: string }> {
    const response = await fetch(`${this.baseUrl}/features`);
    
    if (!response.ok) {
      throw new Error(`Failed to get features: ${response.status}`);
    }
    
    return response.json();
  }

  async predictBatch(predictions: PredictionRequest[]): Promise<PredictionResponse[]> {
    const results = await Promise.all(
      predictions.map(prediction => this.predictCrop(prediction))
    );
    
    return results;
  }
}

export const api = new CropRecommendationAPI();
export default api;
