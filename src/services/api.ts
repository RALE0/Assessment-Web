const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://172.28.69.96:8443';

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

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: {
    id: string;
    username: string;
    email?: string;
    lastLoginAt: string;
    sessionStartedAt: string;
  };
}

export interface ResetPasswordRequest {
  email: string;
}

export interface SignupRequest {
  username: string;
  email: string;
  password: string;
}

export interface SessionActivity {
  userId: string;
  activity: 'login' | 'logout' | 'page_view' | 'action';
  timestamp: string;
  userAgent?: string;
  ipAddress?: string;
  details?: Record<string, any>;
}

export interface SessionLog {
  id: string;
  userId: string;
  sessionId: string;
  startTime: string;
  endTime?: string;
  duration?: number;
  activities: SessionActivity[];
  ipAddress: string;
  userAgent: string;
}

export interface PredictionLog {
  id: string;
  userId: string;
  timestamp: string;
  inputFeatures: {
    N: number;
    P: number;
    K: number;
    temperature: number;
    humidity: number;
    ph: number;
    rainfall: number;
  };
  predictedCrop: string;
  confidence: number;
  topPredictions: {
    crop: string;
    probability: number;
  }[];
  status: 'success' | 'error';
  processingTime?: number;
  errorMessage?: string;
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

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    const result = await response.json();

    if (!response.ok) {
      const error: ApiError = result;
      throw new Error(error.error || 'Login failed');
    }

    return result;
  }

  async logout(token: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/auth/logout`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Logout failed');
    }
  }

  async verifyToken(token: string): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/auth/verify`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    const result = await response.json();

    if (!response.ok) {
      const error: ApiError = result;
      throw new Error(error.error || 'Token verification failed');
    }

    return result;
  }

  async resetPassword(request: ResetPasswordRequest): Promise<void> {
    const response = await fetch(`${this.baseUrl}/auth/reset-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Password reset failed');
    }
  }

  async signup(credentials: SignupRequest): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    const result = await response.json();

    if (!response.ok) {
      const error: ApiError = result;
      throw new Error(error.error || 'Sign up failed');
    }

    return result;
  }

  async logActivity(activity: SessionActivity, token?: string): Promise<void> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}/auth/log-activity`, {
      method: 'POST',
      headers,
      body: JSON.stringify(activity),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Activity logging failed');
    }
  }

  async getSessionLogs(userId: string, token: string): Promise<SessionLog[]> {
    const response = await fetch(`${this.baseUrl}/auth/sessions/${userId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    const result = await response.json();

    if (!response.ok) {
      const error: ApiError = result;
      throw new Error(error.error || 'Failed to get session logs');
    }

    return result.sessions;
  }

  // Dashboard endpoints
  async getDashboardMetrics(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/dashboard/metrics`);
    
    if (!response.ok) {
      throw new Error(`Failed to get dashboard metrics: ${response.status}`);
    }
    
    return response.json();
  }

  async getMonthlyPredictions(): Promise<{ data: any[], timestamp: string }> {
    const response = await fetch(`${this.baseUrl}/api/dashboard/monthly-predictions`);
    
    if (!response.ok) {
      throw new Error(`Failed to get monthly predictions: ${response.status}`);
    }
    
    return response.json();
  }

  async getCropDistribution(): Promise<{ data: any[], timestamp: string }> {
    const response = await fetch(`${this.baseUrl}/api/dashboard/crop-distribution`);
    
    if (!response.ok) {
      throw new Error(`Failed to get crop distribution: ${response.status}`);
    }
    
    return response.json();
  }

  // Analytics endpoints
  async getResponseTimeData(token?: string): Promise<{ data: { timestamp: string; responseTime: number }[], timestamp: string }> {
    const headers: Record<string, string> = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}/api/analytics/response-time-data`, {
      headers,
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get response time data: ${response.status}`);
    }
    
    return response.json();
  }

  async getUserPredictions(token?: string): Promise<{ predictions: { date: string; user: string; recommendedCrop: string; confidence: number }[], timestamp: string }> {
    const headers: Record<string, string> = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}/api/analytics/user-predictions`, {
      headers,
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get user predictions: ${response.status}`);
    }
    
    return response.json();
  }

  async getModelMetrics(token?: string): Promise<{ metrics: any[], timestamp: string }> {
    const headers: Record<string, string> = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}/api/analytics/model-metrics`, {
      headers,
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get model metrics: ${response.status}`);
    }
    
    return response.json();
  }

  async getPerformanceMetrics(token?: string): Promise<any> {
    const headers: Record<string, string> = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}/api/analytics/performance-metrics`, {
      headers,
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get performance metrics: ${response.status}`);
    }
    
    return response.json();
  }

  // About page metrics endpoint
  async getAboutMetrics(): Promise<{
    crops_analyzed: number;
    active_users: number;
    success_rate: number;
    countries_served: number;
  }> {
    const response = await fetch(`${this.baseUrl}/api/about/metrics`);
    
    if (!response.ok) {
      throw new Error(`Failed to get about metrics: ${response.status}`);
    }
    
    return response.json();
  }

  // Chatbot endpoint
  async sendChatMessage(message: string, conversationId?: string): Promise<{
    response: string;
    conversationId: string;
    suggestions?: string[];
    context?: any;
  }> {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        conversationId,
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      const error: ApiError = result;
      throw new Error(error.error || 'Chat request failed');
    }

    return result;
  }

  // User prediction logs endpoints
  async getUserPredictionLogs(userId: string, token?: string): Promise<PredictionLog[]> {
    const headers: Record<string, string> = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}/api/users/${userId}/prediction-logs`, {
      headers,
    });

    const result = await response.json();

    if (!response.ok) {
      const error: ApiError = result;
      throw new Error(error.error || 'Failed to get user prediction logs');
    }

    return result.logs;
  }

  async savePredictionLog(predictionData: {
    userId: string;
    inputFeatures: PredictionRequest;
    prediction: PredictionResponse;
    processingTime?: number;
  }, token?: string): Promise<void> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}/api/prediction-logs`, {
      method: 'POST',
      headers,
      body: JSON.stringify(predictionData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to save prediction log');
    }
  }
}

export const api = new CropRecommendationAPI();
export default api;
