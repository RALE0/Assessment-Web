# Authentication API Endpoints

This document describes the authentication-related API endpoints for the AgriAI Platform.

## Base URL
```
Default: 172.28.69.96:8443
Environment variable: VITE_API_BASE_URL
```

## Authentication Endpoints

### 1. User Login
**POST** `/auth/login`

Authenticates a user and returns a JWT token.

#### Request Body
```json
{
  "username": "string",
  "password": "string"
}
```

#### Response (200 OK)
```json
{
  "token": "string",
  "user": {
    "id": "string",
    "username": "string",
    "email": "string",
    "lastLoginAt": "string",
    "sessionStartedAt": "string"
  }
}
```

#### Error Response (400/401)
```json
{
  "error": "string",
  "details": "string",
  "timestamp": "string"
}
```

### 2. User Registration
**POST** `/auth/signup`

Creates a new user account and returns authentication token.

#### Request Body
```json
{
  "username": "string",
  "email": "string", 
  "password": "string"
}
```

#### Response (201 Created)
```json
{
  "token": "string",
  "user": {
    "id": "string",
    "username": "string",
    "email": "string",
    "lastLoginAt": "string",
    "sessionStartedAt": "string"
  }
}
```

#### Error Response (400)
```json
{
  "error": "string",
  "details": "string",
  "timestamp": "string"
}
```

### 3. User Logout
**POST** `/auth/logout`

Logs out the current user and invalidates the session.

#### Headers
```
Authorization: Bearer <token>
```

#### Response (200 OK)
```json
{
  "message": "Logout successful"
}
```

#### Error Response (401)
```json
{
  "error": "string",
  "details": "string",
  "timestamp": "string"
}
```

### 4. Token Verification
**GET** `/auth/verify`

Verifies the validity of a JWT token and returns user information.

#### Headers
```
Authorization: Bearer <token>
```

#### Response (200 OK)
```json
{
  "token": "string",
  "user": {
    "id": "string",
    "username": "string",
    "email": "string",
    "lastLoginAt": "string",
    "sessionStartedAt": "string"
  }
}
```

#### Error Response (401)
```json
{
  "error": "string",
  "details": "string",
  "timestamp": "string"
}
```

### 5. Password Reset Request
**POST** `/auth/reset-password`

Initiates a password reset process by sending a reset email.

#### Request Body
```json
{
  "email": "string"
}
```

#### Response (200 OK)
```json
{
  "message": "Password reset email sent"
}
```

#### Error Response (400/404)
```json
{
  "error": "string",
  "details": "string", 
  "timestamp": "string"
}
```

### 6. Log Session Activity
**POST** `/auth/log-activity`

Records user session activities for analytics and security.

#### Headers
```
Authorization: Bearer <token> (optional)
```

#### Request Body
```json
{
  "userId": "string",
  "activity": "login | logout | page_view | action",
  "timestamp": "string",
  "userAgent": "string",
  "ipAddress": "string",
  "details": {}
}
```

#### Response (200 OK)
```json
{
  "message": "Activity logged successfully"
}
```

#### Error Response (400)
```json
{
  "error": "string",
  "details": "string",
  "timestamp": "string"
}
```

### 7. Get Session Logs
**GET** `/auth/sessions/{userId}`

Retrieves session logs for a specific user.

#### Headers
```
Authorization: Bearer <token>
```

#### Path Parameters
- `userId` (string): The ID of the user

#### Response (200 OK)
```json
{
  "sessions": [
    {
      "id": "string",
      "userId": "string", 
      "sessionId": "string",
      "startTime": "string",
      "endTime": "string",
      "duration": 0,
      "activities": [
        {
          "userId": "string",
          "activity": "string",
          "timestamp": "string",
          "userAgent": "string",
          "ipAddress": "string",
          "details": {}
        }
      ],
      "ipAddress": "string",
      "userAgent": "string"
    }
  ]
}
```

#### Error Response (401/403)
```json
{
  "error": "string",
  "details": "string",
  "timestamp": "string"
}
```

## Data Types

### User Object
```typescript
interface User {
  id: string;
  username: string;
  email?: string;
  lastLoginAt: string;
  sessionStartedAt: string;
}
```

### Session Activity Object
```typescript
interface SessionActivity {
  userId: string;
  activity: 'login' | 'logout' | 'page_view' | 'action';
  timestamp: string;
  userAgent?: string;
  ipAddress?: string;
  details?: Record<string, any>;
}
```

### Session Log Object
```typescript
interface SessionLog {
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
```

## Error Handling

All endpoints return structured error responses with the following format:

```json
{
  "error": "string",
  "details": "string",
  "timestamp": "string"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

## Authentication Flow

1. **Registration**: User registers with username, email, and password
2. **Login**: User logs in with username and password to receive JWT token
3. **Token Storage**: Frontend stores JWT token in localStorage
4. **Authenticated Requests**: Include `Authorization: Bearer <token>` header
5. **Token Verification**: Periodic verification of token validity
6. **Logout**: Explicit logout to invalidate session
7. **Session Tracking**: Activities logged for analytics and security

## Security Considerations

- All authentication endpoints use HTTPS
- JWT tokens have expiration times
- Session activities are logged for security monitoring
- Password reset requires email verification
- Tokens are validated on protected routes