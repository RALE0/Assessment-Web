# Backend Analytics API Requirements - URGENT IMPLEMENTATION NEEDED

## Overview
The frontend Analytics page is currently showing fallback mock data because the backend API endpoints are not implemented. The frontend is already configured to call the real endpoints but falls back to sample data when they fail.

**CRITICAL**: These endpoints must be implemented to show real analytics data instead of mock data in the "Tiempo de Respuesta", "Satisfacción Usuario", and "ROI Promedio" cards.

## Required API Endpoints

### 1. Accuracy Trend Endpoint
**Endpoint**: `GET /api/analytics/accuracy-trend`
**Authentication**: Bearer token (optional)

**Response Structure**:
```json
{
  "data": [
    {
      "month": "Ene",
      "accuracy": 94.2
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Data Requirements**:
- Calculate monthly model accuracy from prediction logs
- Group predictions by month for the last 12 months
- Calculate accuracy as: `(correct_predictions / total_predictions) * 100`

### 2. Regional Distribution Endpoint
**Endpoint**: `GET /api/analytics/regional-distribution`
**Authentication**: Bearer token (optional)

**Response Structure**:
```json
{
  "data": [
    {
      "name": "Centro México",
      "value": 35,
      "color": "#10b981"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Data Requirements**:
- Group users/predictions by geographic region
- Calculate percentage distribution
- Assign consistent colors for regions
- Support regions: Centro México, Sur México, Norte México, Colombia, Otros

### 3. Model Performance Metrics Endpoint
**Endpoint**: `GET /api/analytics/model-metrics`
**Authentication**: Bearer token (optional)

**Response Structure**:
```json
{
  "metrics": [
    {
      "name": "Precisión General",
      "value": 97.8,
      "target": 95,
      "status": "excellent"
    },
    {
      "name": "Recall", 
      "value": 94.2,
      "target": 90,
      "status": "good"
    },
    {
      "name": "F1-Score",
      "value": 95.9,
      "target": 92, 
      "status": "excellent"
    },
    {
      "name": "Especificidad",
      "value": 96.4,
      "target": 93,
      "status": "excellent"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Data Requirements**:
- Calculate precision, recall, F1-score, and specificity from prediction logs
- Compare against predefined targets
- Assign status based on performance: 
  - excellent: >= target + 2%
  - good: >= target
  - warning: >= target - 5%
  - poor: < target - 5%

### 4. Performance Metrics Endpoint ⚠️ MOST CRITICAL - FIXES MOCK DATA ISSUE
**Endpoint**: `GET /api/analytics/performance-metrics`
**Authentication**: Bearer token (optional)
**Frontend Impact**: This endpoint directly feeds the "Tiempo de Respuesta", "Satisfacción Usuario", and "ROI Promedio" cards

**Response Structure**:
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
  "last_harvest_date": "2024-01-15"
}
```

**Data Requirements**:
- Track API response times for each prediction request
- Calculate percentiles (P95, P99) from response time logs
- Store user satisfaction scores and reviews
- Calculate ROI metrics from user feedback/surveys
- Track harvest dates and outcomes

## Database Schema Modifications

### 1. Prediction Logs Enhancement
```sql
ALTER TABLE prediction_logs ADD COLUMN IF NOT EXISTS processing_time_ms INTEGER;
ALTER TABLE prediction_logs ADD COLUMN IF NOT EXISTS user_region VARCHAR(100);
ALTER TABLE prediction_logs ADD COLUMN IF NOT EXISTS actual_crop VARCHAR(100);
ALTER TABLE prediction_logs ADD COLUMN IF NOT EXISTS feedback_score INTEGER;
```

### 2. New Tables Required

#### User Reviews Table
```sql
CREATE TABLE user_reviews (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    prediction_id VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### Performance Metrics Table
```sql
CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calculation_period VARCHAR(50),
    metadata JSONB
);
```

#### Regional Data Table
```sql
CREATE TABLE regional_data (
    id SERIAL PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL,
    country VARCHAR(100),
    user_count INTEGER DEFAULT 0,
    prediction_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Harvest Outcomes Table
```sql
CREATE TABLE harvest_outcomes (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    prediction_id VARCHAR(255),
    predicted_crop VARCHAR(100),
    actual_crop VARCHAR(100),
    harvest_date DATE,
    yield_quantity DECIMAL(10,2),
    roi_percentage DECIMAL(5,2),
    success_rating INTEGER CHECK (success_rating >= 1 AND success_rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## IMMEDIATE IMPLEMENTATION PRIORITY

### CRITICAL - Implement these endpoints to eliminate mock data:

1. **`GET /api/analytics/performance-metrics`** - HIGHEST PRIORITY
   - Eliminates mock data in "Tiempo de Respuesta", "Satisfacción Usuario", "ROI Promedio" cards
   - Frontend is calling this endpoint and falling back to mock data on failure

2. **`GET /api/analytics/model-metrics`** - HIGH PRIORITY  
   - Eliminates mock data in the 4 performance metric cards at the top

3. **`GET /api/analytics/accuracy-trend`** - MEDIUM PRIORITY
   - Eliminates mock data in the accuracy trend chart

4. **`GET /api/analytics/regional-distribution`** - LOWER PRIORITY
   - Eliminates mock data in the regional pie chart

## Implementation Tasks

### 1. Data Collection
- **Response Time Tracking**: Implement middleware to log API response times
- **User Region Detection**: Add IP geolocation or user profile region setting
- **Feedback Collection**: Create forms for users to rate predictions and report outcomes
- **Harvest Tracking**: Allow users to log actual harvest results

### 2. Calculation Services
- **Accuracy Calculator**: Service to compute model accuracy from prediction vs actual results
- **Performance Aggregator**: Service to calculate percentiles and averages from logs
- **Regional Analytics**: Service to group and calculate regional distributions
- **ROI Calculator**: Service to compute return on investment from harvest data

### 3. Caching Strategy
- Implement Redis caching for expensive calculations
- Cache results for 1 hour, recalculate on cache miss
- Background jobs to pre-calculate metrics during off-peak hours

### 4. Authentication & Authorization
- Secure endpoints with JWT token validation
- Allow public access with limited data for demo purposes
- Rate limiting to prevent abuse

### 5. Data Migration
- Backfill existing prediction logs with estimated regions
- Import historical data if available
- Set up default targets for model metrics

## API Error Handling

All endpoints should return consistent error responses:

```json
{
  "error": "Error message",
  "details": "Detailed error description",
  "timestamp": "2024-01-15T10:30:00Z",
  "endpoint": "/api/analytics/accuracy-trend"
}
```

## Performance Considerations

1. **Database Indexing**:
   - Index on prediction_logs.timestamp for time-based queries
   - Index on prediction_logs.user_region for regional queries
   - Index on user_reviews.created_at for review aggregations

2. **Query Optimization**:
   - Use database aggregation functions instead of application-level calculations
   - Implement pagination for large datasets
   - Use database views for complex calculations

3. **Monitoring**:
   - Log slow queries (>100ms)
   - Monitor endpoint response times
   - Set up alerts for unusual metric values

## Testing Requirements

1. **Unit Tests**: Test calculation logic for each metric
2. **Integration Tests**: Test API endpoints with sample data
3. **Performance Tests**: Ensure endpoints respond within 2 seconds
4. **Data Accuracy Tests**: Validate metric calculations against known datasets

This implementation will transform the Analytics page from displaying dummy data to showing real, actionable insights about the crop recommendation system's performance.