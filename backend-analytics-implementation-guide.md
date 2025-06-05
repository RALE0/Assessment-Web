# Backend Analytics Implementation Guide

Based on the frontend Analytics component and API service, this document outlines the required backend endpoints that need to be implemented to support the analytics functionality.

## Missing Endpoints (404 Errors)

The following endpoints are currently returning 404 errors and need to be implemented:

### 1. `/api/analytics/user-predictions`
**Method:** GET  
**Authentication:** Bearer token (optional)  
**Description:** Returns recent user predictions for analytics display

**Expected Response:**
```json
{
  "predictions": [
    {
      "date": "2025-06-05",
      "user": "user123",
      "recommendedCrop": "Rice",
      "confidence": 89
    }
  ],
  "timestamp": "2025-06-05T11:58:12.000Z"
}
```

**Implementation Notes:**
- Query the prediction logs table/collection
- Return the most recent 50-100 predictions
- Include user identifier, predicted crop, confidence score, and date
- Support pagination if needed

### 2. `/api/analytics/response-time-data`
**Method:** GET  
**Authentication:** Bearer token (optional)  
**Description:** Returns response time metrics over time for chart visualization

**Expected Response:**
```json
{
  "data": [
    {
      "timestamp": "2025-06-05T11:00:00Z",
      "responseTime": 1.23
    },
    {
      "timestamp": "2025-06-05T11:30:00Z", 
      "responseTime": 0.98
    }
  ],
  "timestamp": "2025-06-05T11:58:12.000Z"
}
```

**Implementation Notes:**
- Track API response times for prediction endpoints
- Aggregate data by time intervals (15-30 minutes)
- Store in a time-series format for efficient querying
- Return last 24-48 hours of data

## Existing Endpoints (Working)

### 3. `/api/analytics/model-metrics` ✅
**Status:** Working (200 OK)  
**Expected Response:**
```json
{
  "metrics": [
    {
      "name": "Accuracy",
      "value": 94.5,
      "target": 90,
      "status": "excellent"
    },
    {
      "name": "Precision",
      "value": 92.1,
      "target": 85,
      "status": "excellent" 
    },
    {
      "name": "Recall",
      "value": 88.7,
      "target": 80,
      "status": "good"
    },
    {
      "name": "F1-Score",
      "value": 90.3,
      "target": 82,
      "status": "excellent"
    }
  ],
  "timestamp": "2025-06-05T11:58:12.000Z"
}
```

### 4. `/api/analytics/performance-metrics` ✅
**Status:** Working (200 OK)  
**Expected Response:**
```json
{
  "average_response_time": 1.24,
  "p95_response_time": 2.10,
  "p99_response_time": 3.45,
  "timestamp": "2025-06-05T11:58:12.000Z"
}
```

## Implementation Requirements

### Database Schema Requirements

1. **Response Time Tracking Table:**
```sql
CREATE TABLE response_time_logs (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    response_time DECIMAL(10,3) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_code INTEGER,
    user_id VARCHAR(255)
);
```

2. **Enhanced Prediction Logs:**
```sql
-- Ensure prediction_logs table includes necessary fields
ALTER TABLE prediction_logs ADD COLUMN IF NOT EXISTS confidence DECIMAL(5,2);
ALTER TABLE prediction_logs ADD COLUMN IF NOT EXISTS processing_time DECIMAL(10,3);
```

### Backend Implementation Steps

1. **Create Analytics Blueprint/Router:**
   - Create `/api/analytics/` route handler
   - Implement authentication middleware
   - Add error handling and logging

2. **Implement Missing Endpoints:**

   **User Predictions Endpoint:**
   ```python
   @analytics_bp.route('/user-predictions', methods=['GET'])
   def get_user_predictions():
       try:
           # Query recent predictions from database
           predictions = db.query("""
               SELECT date, user_id, predicted_crop, confidence 
               FROM prediction_logs 
               ORDER BY timestamp DESC 
               LIMIT 50
           """)
           
           return jsonify({
               "predictions": [
                   {
                       "date": p.date.strftime("%Y-%m-%d"),
                       "user": p.user_id,
                       "recommendedCrop": p.predicted_crop,
                       "confidence": float(p.confidence)
                   } for p in predictions
               ],
               "timestamp": datetime.utcnow().isoformat()
           })
       except Exception as e:
           return jsonify({"error": str(e)}), 500
   ```

   **Response Time Data Endpoint:**
   ```python
   @analytics_bp.route('/response-time-data', methods=['GET'])
   def get_response_time_data():
       try:
           # Query aggregated response times
           data = db.query("""
               SELECT 
                   DATE_TRUNC('hour', timestamp) as hour,
                   AVG(response_time) as avg_time
               FROM response_time_logs 
               WHERE timestamp >= NOW() - INTERVAL '24 hours'
               GROUP BY hour
               ORDER BY hour
           """)
           
           return jsonify({
               "data": [
                   {
                       "timestamp": d.hour.isoformat(),
                       "responseTime": round(float(d.avg_time), 2)
                   } for d in data
               ],
               "timestamp": datetime.utcnow().isoformat()
           })
       except Exception as e:
           return jsonify({"error": str(e)}), 500
   ```

3. **Add Response Time Tracking Middleware:**
   ```python
   @app.before_request
   def start_timer():
       g.start_time = time.time()

   @app.after_request
   def log_response_time(response):
       if hasattr(g, 'start_time'):
           response_time = time.time() - g.start_time
           
           # Log to database for analytics
           if request.endpoint in ['predict', 'predict_batch']:
               log_response_time_to_db(
                   endpoint=request.endpoint,
                   response_time=response_time,
                   status_code=response.status_code,
                   user_id=getattr(g, 'user_id', None)
               )
       
       return response
   ```

4. **Update Existing Prediction Endpoints:**
   - Ensure prediction logs include confidence scores
   - Track processing times for performance metrics
   - Store user associations for analytics

### Frontend Integration Notes

The frontend expects:
- All endpoints to handle optional Bearer token authentication
- Consistent error responses with proper HTTP status codes
- Data formatted exactly as shown in the response examples
- Timestamps in ISO format
- Response time values in seconds (decimal format)

### Testing Requirements

1. **Endpoint Testing:**
   - Test all analytics endpoints with/without authentication
   - Verify response format matches frontend expectations
   - Test error handling for database failures

2. **Performance Testing:**
   - Ensure analytics queries don't impact prediction performance
   - Test with large datasets to verify query efficiency
   - Monitor memory usage for time-series data

3. **Integration Testing:**
   - Test full analytics workflow from prediction to display
   - Verify real-time updates work correctly
   - Test auto-refresh functionality (30-second intervals)

## Priority Implementation Order

1. **High Priority:** `/api/analytics/user-predictions` (required for main analytics table)
2. **High Priority:** `/api/analytics/response-time-data` (required for main chart)
3. **Medium Priority:** Response time tracking middleware
4. **Low Priority:** Performance optimizations and caching

## Error Handling

Ensure all endpoints return appropriate error responses:
```json
{
  "error": "Database connection failed",
  "details": "Connection timeout after 30 seconds",
  "timestamp": "2025-06-05T11:58:12.000Z"
}
```

Frontend will display "Datos no disponibles" and "No se pudieron cargar los datos del servidor" for any failed requests.