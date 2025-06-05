# Dashboard Backend Changes - User-Specific Data

## Overview
The dashboard has been modified in the frontend to show only user-generated data instead of all platform data. This document outlines the required backend changes to support user-specific dashboard functionality.

## Required Backend Endpoints

### 1. User-Specific Dashboard Metrics
**Endpoint:** `GET /api/dashboard/user/{userId}/metrics`

**Description:** Returns dashboard metrics filtered for a specific user

**Authentication:** Required (Bearer token)

**Response Format:**
```json
{
  "predictions_generated": number,     // User's total predictions
  "predictions_change": number,        // % change vs previous month
  "model_accuracy": number,           // Model accuracy for user's predictions
  "accuracy_change": number,          // % change vs previous period
  "crops_analyzed": number,           // Unique crops analyzed by user
  "new_crops": number,               // New crops this period
  "active_users": 1,                 // Always 1 for user-specific view
  "users_change": 0                  // Not applicable for user view
}
```

### 2. User-Specific Monthly Predictions
**Endpoint:** `GET /api/dashboard/user/{userId}/monthly-predictions`

**Description:** Returns monthly prediction data for a specific user

**Authentication:** Required (Bearer token)

**Response Format:**
```json
{
  "data": [
    {
      "month": "Ene",
      "predictions": number    // User's predictions for this month
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 3. User-Specific Crop Distribution
**Endpoint:** `GET /api/dashboard/user/{userId}/crop-distribution`

**Description:** Returns crop distribution data for a specific user's predictions

**Authentication:** Required (Bearer token)

**Response Format:**
```json
{
  "data": [
    {
      "crop": "Maíz",
      "count": number,         // Number of times user got this crop prediction
      "color": "#10b981"      // Chart color
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Implementation Requirements

### Database Queries
1. **Filter by User ID:** All dashboard queries must filter data by the authenticated user's ID
2. **Prediction Logs:** Use the existing prediction logs table to aggregate user-specific data
3. **Date Filtering:** Implement proper date range filtering for monthly/periodic comparisons

### Security
1. **Authentication:** All endpoints require valid Bearer token
2. **Authorization:** Users can only access their own data (verify userId matches token)
3. **Input Validation:** Validate userId parameter format

### Data Aggregation
1. **Monthly Predictions:** Group user's predictions by month
2. **Crop Distribution:** Count frequency of each crop in user's predictions
3. **Accuracy Calculation:** Calculate model accuracy based on user's prediction feedback (if available)
4. **Change Percentages:** Compare current period with previous period for the same user

### Fallback Behavior
1. **New Users:** Handle users with no prediction history gracefully
2. **Empty Data:** Return zero values for metrics when user has no data
3. **Error Handling:** Provide meaningful error messages for invalid user IDs

## Database Schema Considerations

### Prediction Logs Table
Ensure the prediction logs table includes:
- `user_id` (foreign key to users table)
- `timestamp` (for monthly grouping)
- `predicted_crop` (for distribution analysis)
- `confidence` (for accuracy calculations)
- `created_at` (for tracking trends)

### Indexes
Consider adding indexes for:
- `user_id, timestamp` (for monthly queries)
- `user_id, predicted_crop` (for distribution queries)
- `user_id, created_at` (for general filtering)

## Migration Notes
1. **Backward Compatibility:** Keep existing global dashboard endpoints for admin/analytics purposes
2. **Data Migration:** No data migration required - only new endpoints needed
3. **Testing:** Test with users who have varying amounts of prediction history

## Performance Considerations
1. **Caching:** Consider caching user dashboard data for frequently accessed metrics
2. **Pagination:** For users with large prediction histories, consider pagination
3. **Query Optimization:** Optimize database queries for user-specific aggregations