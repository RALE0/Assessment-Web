# Backend API Changes Required

This document details all the new endpoints and modifications needed in the backend to support the frontend data integration.

## Overview

The frontend has been modified to fetch all displayed data from the backend instead of using mocked/hardcoded data. The following components now require backend API support:

1. **Dashboard Component** - Main metrics and charts
2. **Analytics Component** - Performance metrics and analytics data
3. **Recommendations Component** - Already integrated (existing endpoints)
4. **ChatBot Component** - AI-powered chat interface

## New Endpoints Required

### 1. Dashboard Endpoints

#### GET `/api/dashboard/metrics`
Returns the main dashboard metrics.

**Response Format:**
```json
{
  "predictions_generated": 3456,
  "predictions_change": 12,
  "model_accuracy": 97.8,
  "accuracy_change": 2.1,
  "crops_analyzed": 24,
  "new_crops": 3,
  "active_users": 12847,
  "users_change": 8
}
```

**Fields Description:**
- `predictions_generated`: Total number of predictions made
- `predictions_change`: Percentage change compared to previous month
- `model_accuracy`: Current model accuracy percentage
- `accuracy_change`: Change in accuracy compared to previous quarter
- `crops_analyzed`: Total number of different crops supported
- `new_crops`: Number of new crops added recently
- `active_users`: Number of active users
- `users_change`: Percentage change in users compared to previous month

#### GET `/api/dashboard/monthly-predictions`
Returns monthly prediction counts for the line chart.

**Response Format:**
```json
{
  "data": [
    { "month": "Ene", "predictions": 234 },
    { "month": "Feb", "predictions": 289 },
    { "month": "Mar", "predictions": 356 },
    { "month": "Abr", "predictions": 423 },
    { "month": "May", "predictions": 467 },
    { "month": "Jun", "predictions": 543 }
  ],
  "timestamp": "2024-01-05T10:00:00Z"
}
```

#### GET `/api/dashboard/crop-distribution`
Returns crop distribution data for the bar chart.

**Response Format:**
```json
{
  "data": [
    { "crop": "Maíz", "count": 1234, "color": "#10b981" },
    { "crop": "Frijol", "count": 956, "color": "#059669" },
    { "crop": "Arroz", "count": 743, "color": "#047857" },
    { "crop": "Café", "count": 587, "color": "#065f46" },
    { "crop": "Tomate", "count": 432, "color": "#064e3b" }
  ],
  "timestamp": "2024-01-05T10:00:00Z"
}
```

### 2. Analytics Endpoints

#### GET `/api/analytics/accuracy-trend`
Returns model accuracy trend over time.

**Response Format:**
```json
{
  "data": [
    { "month": "Ene", "accuracy": 94.2 },
    { "month": "Feb", "accuracy": 95.1 },
    { "month": "Mar", "accuracy": 96.3 },
    { "month": "Abr", "accuracy": 97.1 },
    { "month": "May", "accuracy": 97.8 },
    { "month": "Jun", "accuracy": 97.8 }
  ],
  "timestamp": "2024-01-05T10:00:00Z"
}
```

#### GET `/api/analytics/regional-distribution`
Returns prediction distribution by region.

**Response Format:**
```json
{
  "data": [
    { "name": "Centro México", "value": 35, "color": "#10b981" },
    { "name": "Sur México", "value": 25, "color": "#059669" },
    { "name": "Norte México", "value": 20, "color": "#047857" },
    { "name": "Colombia", "value": 12, "color": "#065f46" },
    { "name": "Otros", "value": 8, "color": "#064e3b" }
  ],
  "timestamp": "2024-01-05T10:00:00Z"
}
```

#### GET `/api/analytics/model-metrics`
Returns detailed model performance metrics.

**Response Format:**
```json
{
  "metrics": [
    { "name": "Precisión General", "value": 97.8, "target": 95, "status": "excellent" },
    { "name": "Recall", "value": 94.2, "target": 90, "status": "good" },
    { "name": "F1-Score", "value": 95.9, "target": 92, "status": "excellent" },
    { "name": "Especificidad", "value": 96.4, "target": 93, "status": "excellent" }
  ],
  "timestamp": "2024-01-05T10:00:00Z"
}
```

**Status Values:** "excellent", "good", "warning", "poor"

#### GET `/api/analytics/performance-metrics`
Returns system performance and user satisfaction metrics.

**Response Format:**
```json
{
  "average_response_time": 1.2,
  "p95_response_time": 2.1,
  "p99_response_time": 3.4,
  "user_satisfaction_score": 4.8,
  "total_reviews": 2847,
  "positive_percentage": 96,
  "average_roi_increase": 23,
  "vs_traditional_farming": "vs cultivos tradicionales",
  "last_harvest_date": "Última cosecha"
}
```

### 3. Chat Endpoint

#### POST `/api/chat`
Handles AI-powered chat conversations.

**Request Body:**
```json
{
  "message": "¿Qué cultivo me recomiendas?",
  "conversationId": "optional-conversation-id"
}
```

**Response Format:**
```json
{
  "response": "Para darte la mejor recomendación, necesito conocer algunos datos de tu terreno...",
  "conversationId": "unique-conversation-id",
  "suggestions": [
    "Tengo suelo arcilloso en México",
    "Suelo arenoso, temporada seca",
    "Necesito más información sobre tipos de suelo"
  ],
  "context": {
    "topic": "crop_recommendation",
    "confidence": 0.95
  }
}
```

## Implementation Notes

### 1. Data Aggregation
- Dashboard metrics should be calculated from actual database records
- Consider implementing caching for frequently accessed metrics (e.g., 5-minute cache)
- Monthly data should cover the last 6 months by default

### 2. Performance Considerations
- Implement pagination for large datasets
- Use database indexes for frequently queried fields
- Consider implementing real-time updates using WebSockets for dashboard metrics

### 3. Error Handling
- All endpoints should return consistent error responses:
```json
{
  "error": "Error message",
  "details": "Detailed error description",
  "timestamp": "2024-01-05T10:00:00Z"
}
```

### 4. Authentication
- Dashboard and Analytics endpoints should be publicly accessible or require basic authentication
- Chat endpoint should support both authenticated and anonymous users
- Consider implementing rate limiting for the chat endpoint

### 5. Chat Integration
- The chat endpoint should integrate with an AI model (e.g., OpenAI GPT, Claude, or a custom model)
- Implement conversation history storage for authenticated users
- Consider implementing context-aware responses based on user's previous predictions

### 6. Data Sources
The backend should aggregate data from:
- Prediction logs table
- User activity logs
- Model performance metrics
- Regional usage statistics
- System performance monitoring

### 7. Fallback Data
The frontend implements fallback data when API calls fail. However, the backend should ensure high availability to minimize the use of fallback data.

## Database Schema Suggestions

### New Tables Needed:

1. **dashboard_metrics**
   - id
   - metric_type
   - value
   - change_percentage
   - calculated_at
   - period (daily/monthly/quarterly)

2. **prediction_analytics**
   - id
   - prediction_id
   - region
   - created_at
   - response_time
   - model_version

3. **chat_conversations**
   - id
   - user_id (nullable for anonymous)
   - conversation_id
   - message
   - response
   - created_at

4. **model_performance**
   - id
   - model_version
   - metric_name
   - value
   - target_value
   - evaluated_at

## Testing Requirements

1. Unit tests for all new endpoints
2. Integration tests for data aggregation logic
3. Performance tests for endpoints returning large datasets
4. Load tests for the chat endpoint
5. End-to-end tests for the complete data flow

## Deployment Considerations

1. Ensure CORS is properly configured for the frontend domain
2. Set up monitoring for all new endpoints
3. Configure alerts for performance degradation
4. Implement graceful degradation for non-critical endpoints
5. Document all endpoints in API documentation (Swagger/OpenAPI)

## Timeline Recommendations

1. **Phase 1** (Week 1): Implement Dashboard endpoints
2. **Phase 2** (Week 2): Implement Analytics endpoints
3. **Phase 3** (Week 3): Implement Chat endpoint with AI integration
4. **Phase 4** (Week 4): Testing, optimization, and deployment

This implementation will transform the AgriAI platform from a static demo to a fully dynamic, data-driven application with real-time insights and AI-powered assistance.