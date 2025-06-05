# Frontend History View Debugging Guide

## Issue Summary

The frontend history view (Historial) is displaying zeros for all metrics despite the backend having 403+ prediction logs. This is caused by a **user authentication/session mismatch** between frontend and backend.

## Backend Status ✅

- **Database Connection**: Working correctly
- **Prediction Logs**: 403 entries exist in `prediction_logs` table
- **Basic Predictions**: 13 entries in `predictions` table  
- **API Endpoints**: All history endpoints are implemented and functional
- **Authentication**: JWT-based auth is working

## Root Cause 🔍

The frontend is making API calls with a **different user_id** than the one that has actual prediction data in the database.

### Known User with Data:
```
User ID: 567ab65a-486e-486d-89de-c06aa6fee544
- Has 403+ prediction logs
- Recent predictions include: wheat, test_crop, test_crop_2, final_test_crop
- Last activity: June 5, 2025
```

## Frontend Debugging Steps

### 1. Check Current User Session

In browser developer tools, verify what user_id the frontend is using:

```javascript
// Check localStorage/sessionStorage for user data
console.log('User from localStorage:', localStorage.getItem('user'));
console.log('User from sessionStorage:', sessionStorage.getItem('user'));

// Check if there's a user context/state
console.log('Current user context:', window.currentUser);
```

### 2. Monitor API Calls

Open Network tab in DevTools and look for these API calls:

```
GET /api/users/{user_id}/prediction-statistics
GET /api/users/{user_id}/prediction-logs
```

**Check:**
- What `user_id` is being sent in the URL
- If JWT token is included in Authorization header
- Response status codes and content

### 3. Verify Authentication Headers

Ensure API calls include proper authentication:

```javascript
// Example of correct API call
const response = await fetch(`/api/users/${userId}/prediction-statistics`, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json'
  }
});
```

## API Endpoints Documentation

### Get User Prediction Statistics
```
GET /api/users/{user_id}/prediction-statistics
Authorization: Bearer {jwt_token}

Query Parameters:
- period: '7d' | '30d' | '90d' | '1y' | 'all' (default: '30d')
- groupBy: 'day' | 'week' | 'month' (default: 'day')

Response:
{
  "success": true,
  "data": {
    "statistics": {
      "totalPredictions": number,
      "successfulPredictions": number,
      "failedPredictions": number,
      "successRate": number,
      "avgConfidence": number,
      "avgProcessingTime": number,
      "mostPredictedCrop": string,
      "firstPrediction": string,
      "lastPrediction": string
    },
    "timeline": [
      {
        "date": "YYYY-MM-DD",
        "predictions": number,
        "avgConfidence": number
      }
    ],
    "cropDistribution": [
      {
        "crop": string,
        "count": number,
        "percentage": number
      }
    ]
  }
}
```

### Get User Prediction Logs
```
GET /api/users/{user_id}/prediction-logs
Authorization: Bearer {jwt_token}

Query Parameters:
- limit: number (max 100, default 50)
- offset: number (default 0)
- dateFrom: ISO date string
- dateTo: ISO date string
- crop: string (filter by crop name)
- status: 'success' | 'error'
- orderBy: 'timestamp' | 'confidence' | 'predicted_crop' | 'processing_time'
- orderDirection: 'asc' | 'desc'

Response:
{
  "success": true,
  "data": {
    "logs": [
      {
        "id": string,
        "userId": string,
        "timestamp": string,
        "inputFeatures": {
          "N": number,
          "P": number,
          "K": number,
          "temperature": number,
          "humidity": number,
          "ph": number,
          "rainfall": number
        },
        "predictedCrop": string,
        "confidence": number,
        "topPredictions": array,
        "status": string,
        "processingTime": number
      }
    ],
    "pagination": {
      "total": number,
      "limit": number,
      "offset": number,
      "hasMore": boolean
    }
  }
}
```

### Export User Prediction Logs
```
GET /api/users/{user_id}/prediction-logs/export
Authorization: Bearer {jwt_token}

Query Parameters: (same as prediction logs)
Response: CSV file download
```

## Testing Scenarios

### 1. Test with Known User (Immediate Fix)

For quick verification, temporarily hardcode the known user ID:

```javascript
const TEST_USER_ID = '567ab65a-486e-486d-89de-c06aa6fee544';

// Test API call
const testResponse = await fetch(`/api/users/${TEST_USER_ID}/prediction-statistics`, {
  headers: {
    'Authorization': `Bearer ${yourJwtToken}`,
    'Content-Type': 'application/json'
  }
});

const data = await testResponse.json();
console.log('Test response:', data);
```

If this returns data, then the issue is user session management.

### 2. Check User Authentication Flow

Verify the complete authentication flow:

```javascript
// 1. User login/registration
// 2. JWT token storage
// 3. User ID extraction from token
// 4. API calls with correct user_id

// Example JWT token decode
function parseJwt(token) {
  const base64Url = token.split('.')[1];
  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function(c) {
    return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
  }).join(''));
  return JSON.parse(jsonPayload);
}

const tokenData = parseJwt(yourJwtToken);
console.log('User ID from token:', tokenData.user_id || tokenData.sub);
```

## Common Issues & Solutions

### Issue 1: User ID Mismatch
**Problem**: Frontend user_id ≠ Database user_id  
**Solution**: Ensure user registration/login creates consistent UUIDs

### Issue 2: Missing Authentication
**Problem**: API calls without JWT token  
**Solution**: Include `Authorization: Bearer {token}` header

### Issue 3: Wrong User Context
**Problem**: Using anonymous/guest user_id  
**Solution**: Implement proper user session management

### Issue 4: Prediction Logging Not Working
**Problem**: New predictions not being logged  
**Solution**: Ensure `/predict` endpoint includes user authentication

## Implementation Checklist

- [ ] Verify current user_id in frontend state/storage
- [ ] Check JWT token presence and validity
- [ ] Monitor API calls in Network tab
- [ ] Test with known user_id (`567ab65a-486e-486d-89de-c06aa6fee544`)
- [ ] Implement proper error handling for empty states
- [ ] Add loading states while fetching data
- [ ] Ensure user registration creates proper UUIDs
- [ ] Verify prediction submission includes authentication

## Backend Base URL

```
Production: http://172.28.69.148:5000
Local Development: http://localhost:5000
```

## Error Responses

### 401 Unauthorized
```json
{
  "success": false,
  "error": "Missing or invalid authentication token"
}
```

### 403 Forbidden
```json
{
  "success": false,
  "error": "Unauthorized to access other users' data"
}
```

### 404 Not Found (Empty Data)
```json
{
  "success": true,
  "data": {
    "statistics": {
      "totalPredictions": 0,
      "successfulPredictions": 0,
      "failedPredictions": 0,
      "successRate": 0,
      "avgConfidence": 0,
      "avgProcessingTime": 0,
      "firstPrediction": null,
      "lastPrediction": null
    },
    "timeline": [],
    "cropDistribution": []
  }
}
```

## Next Steps

1. **Immediate**: Test with known user_id to confirm API works
2. **Short-term**: Fix user session management to use consistent user_ids
3. **Long-term**: Implement proper user onboarding with prediction history

## Contact

If you need backend API changes or have questions about the database schema, please coordinate with the backend team.

---

**Note**: The backend prediction logging system is working correctly. This is purely a frontend user session/authentication issue.