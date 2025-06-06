# Working Curl Commands for Prediction History API

## User Credentials
```json
{
    "user_id": "d81586ff-5334-417f-be3b-5776685e809e",
    "username": "beborico",
    "email": "beborico16@gmail.com",
    "session_token": "ITRXufDQ_ez6dEV1g-gTz6RaZKFNcLkDHvBZ9KQN55k",
    "iat": 1749165957,
    "exp": 1749252357
}
```

## Working Curl Command

### Get Prediction Logs
```bash
curl -X GET \
  "http://172.28.69.96:8443/api/users/d81586ff-5334-417f-be3b-5776685e809e/prediction-logs" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZDgxNTg2ZmYtNTMzNC00MTdmLWJlM2ItNTc3NjY4NWU4MDllIiwidXNlcm5hbWUiOiJiZWJvcmljbyIsImVtYWlsIjoiYmVib3JpY28xNkBnbWFpbC5jb20iLCJzZXNzaW9uX3Rva2VuIjoiSVRSWHVmRFFfZXo2ZEVWMWctZ1R6NlJhWktGTmNMa0RIdkJaOUtRTjU1ayIsImlhdCI6MTc0OTE2NTk1NywiZXhwIjoxNzQ5MjUyMzU3fQ.RxuyQitabc30HioHfjNd29fyq2aPGFRB-AXHxnqsL9s" \
  -H "Content-Type: application/json"
```

### With Query Parameters
```bash
curl -X GET \
  "http://172.28.69.96:8443/api/users/d81586ff-5334-417f-be3b-5776685e809e/prediction-logs?limit=10&offset=0&orderBy=timestamp&orderDirection=desc" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZDgxNTg2ZmYtNTMzNC00MTdmLWJlM2ItNTc3NjY4NWU4MDllIiwidXNlcm5hbWUiOiJiZWJvcmljbyIsImVtYWlsIjoiYmVib3JpY28xNkBnbWFpbC5jb20iLCJzZXNzaW9uX3Rva2VuIjoiSVRSWHVmRFFfZXo2ZEVWMWctZ1R6NlJhWktGTmNMa0RIdkJaOUtRTjU1ayIsImlhdCI6MTc0OTE2NTk1NywiZXhwIjoxNzQ5MjUyMzU3fQ.RxuyQitabc30HioHfjNd29fyq2aPGFRB-AXHxnqsL9s" \
  -H "Content-Type: application/json"
```

### Get Prediction Statistics
```bash
curl -X GET \
  "http://172.28.69.96:8443/api/users/d81586ff-5334-417f-be3b-5776685e809e/prediction-statistics?period=30d&groupBy=day" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZDgxNTg2ZmYtNTMzNC00MTdmLWJlM2ItNTc3NjY4NWU4MDllIiwidXNlcm5hbWUiOiJiZWJvcmljbyIsImVtYWlsIjoiYmVib3JpY28xNkBnbWFpbC5jb20iLCJzZXNzaW9uX3Rva2VuIjoiSVRSWHVmRFFfZXo2ZEVWMWctZ1R6NlJhWktGTmNMa0RIdkJaOUtRTjU1ayIsImlhdCI6MTc0OTE2NTk1NywiZXhwIjoxNzQ5MjUyMzU3fQ.RxuyQitabc30HioHfjNd29fyq2aPGFRB-AXHxnqsL9s" \
  -H "Content-Type: application/json"
```

## Expected Response Format

### Prediction Logs Response
```json
{
  "logs": [
    {
      "id": "string",
      "userId": "string",
      "timestamp": "2025-06-05T23:52:33.263735",
      "inputFeatures": {
        "N": 5,
        "P": 5,
        "K": 5,
        "temperature": 10,
        "humidity": 15,
        "ph": 5,
        "rainfall": 25
      },
      "predictedCrop": "kidneybeans",
      "confidence": 0.9687,
      "topPredictions": [...],
      "status": "success",
      "processingTime": 458
    }
  ],
  "pagination": {
    "total": 4,
    "limit": 50,
    "offset": 0,
    "hasMore": false
  },
  "filters": {
    "order_by": "timestamp",
    "order_direction": "desc"
  },
  "timestamp": "2025-06-05T23:58:17.413230"
}
```

## Frontend Fix Applied

✅ **FIXED**: Updated `src/services/api.ts` to access the correct response properties:
- Changed `result.data.logs` to `result.logs` 
- Changed `result.data.pagination` to `result.pagination`

## Test Results
✅ API returns 4 prediction logs for user `beborico`  
✅ Backend prediction logging system is working correctly  
✅ Database contains the logs  
✅ Frontend now accessing the correct response properties  

## Solution Applied
The frontend `History.tsx` now correctly accesses:
- `response.logs` (instead of `response.data.logs`)
- `response.pagination` (instead of `response.data.pagination`)

The backend was working correctly all along - it was a frontend data access issue.