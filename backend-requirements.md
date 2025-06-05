# Backend Authentication Requirements

## Overview
This document specifies all backend requirements needed to support the complete authentication system implemented in the frontend. The backend must provide secure user authentication, session management, and comprehensive logging capabilities.

## 🗄️ Database Schema Requirements

### 1. Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP NULL
);
```

### 2. User Sessions Table
```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    ended_at TIMESTAMP NULL
);
```

### 3. Session Activities Table
```sql
CREATE TABLE session_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES user_sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL, -- 'login', 'logout', 'page_view', 'action'
    activity_details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. Password Reset Tokens Table
```sql
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔌 Required API Endpoints

### 1. Authentication Endpoints

#### POST `/auth/login`
**Purpose:** Authenticate user and create session
**Request Body:**
```json
{
    "username": "string",
    "password": "string"
}
```
**Response (200):**
```json
{
    "token": "jwt_token_string",
    "user": {
        "id": "uuid",
        "username": "string",
        "email": "string",
        "lastLoginAt": "2024-01-01T00:00:00Z",
        "sessionStartedAt": "2024-01-01T00:00:00Z"
    }
}
```
**Functionality:**
- Validate username/password
- Check account lockout status
- Create new session record
- Generate JWT token
- Log login activity
- Update last_login_at
- Reset failed_login_attempts on success

#### GET `/auth/verify`
**Purpose:** Validate JWT token and return user data
**Headers:** `Authorization: Bearer <token>`
**Response (200):**
```json
{
    "user": {
        "id": "uuid",
        "username": "string",
        "email": "string",
        "lastLoginAt": "2024-01-01T00:00:00Z",
        "sessionStartedAt": "2024-01-01T00:00:00Z"
    }
}
```

#### POST `/auth/logout`
**Purpose:** End user session
**Headers:** `Authorization: Bearer <token>`
**Response (200):**
```json
{
    "message": "Logged out successfully"
}
```
**Functionality:**
- Invalidate session token
- Mark session as ended
- Log logout activity

#### POST `/auth/reset-password`
**Purpose:** Initiate password reset process
**Request Body:**
```json
{
    "email": "string"
}
```
**Response (200):**
```json
{
    "message": "Reset email sent if account exists"
}
```
**Functionality:**
- Validate email exists
- Generate reset token
- Send reset email
- Log reset request

### 2. Session Management Endpoints

#### POST `/auth/log-activity`
**Purpose:** Log user session activity
**Headers:** `Authorization: Bearer <token>` (optional for anonymous activities)
**Request Body:**
```json
{
    "userId": "uuid",
    "activity": "login|logout|page_view|action",
    "timestamp": "2024-01-01T00:00:00Z",
    "userAgent": "string",
    "ipAddress": "string",
    "details": {}
}
```
**Response (200):**
```json
{
    "message": "Activity logged successfully"
}
```

#### GET `/auth/sessions/:userId`
**Purpose:** Retrieve user session history
**Headers:** `Authorization: Bearer <token>`
**Response (200):**
```json
{
    "sessions": [
        {
            "id": "uuid",
            "userId": "uuid",
            "sessionId": "uuid",
            "startTime": "2024-01-01T00:00:00Z",
            "endTime": "2024-01-01T01:00:00Z",
            "duration": 3600,
            "activities": [
                {
                    "userId": "uuid",
                    "activity": "login",
                    "timestamp": "2024-01-01T00:00:00Z",
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

## 🔐 Security Requirements

### 1. Password Security
- **Hashing:** Use bcrypt with minimum 12 rounds
- **Validation:** Minimum 6 characters (frontend enforces this)
- **Reset Tokens:** Secure random tokens with 1-hour expiration

### 2. JWT Configuration
- **Algorithm:** RS256 or HS256
- **Expiration:** 24 hours for access tokens
- **Claims:** Include user ID, username, issued at, expiration
- **Secret Management:** Use environment variables

### 3. Account Security
- **Lockout:** Lock account after 5 failed attempts for 15 minutes
- **Session Management:** Maximum 5 concurrent sessions per user
- **Token Blacklisting:** Maintain invalidated token list

### 4. Rate Limiting
- **Login Attempts:** 5 attempts per IP per 15 minutes
- **Password Reset:** 3 requests per email per hour
- **API Calls:** 1000 requests per user per hour

## 🌐 CORS Configuration
Configure CORS to allow frontend domain:
```
Origin: http://localhost:5173 (development)
Origin: https://your-frontend-domain.com (production)
Methods: GET, POST, PUT, DELETE, OPTIONS
Headers: Content-Type, Authorization
```

## 📧 Email Service Requirements

### Password Reset Email Template
```html
Subject: Restablecer contraseña - AgriAI Platform

Hola [username],

Has solicitado restablecer tu contraseña para AgriAI Platform.

Haz clic en el siguiente enlace para restablecer tu contraseña:
[reset_url]

Este enlace expira en 1 hora.

Si no solicitaste este cambio, puedes ignorar este email.

Saludos,
Equipo AgriAI Platform
```

## 📊 Logging and Monitoring

### 1. Required Logs
- All authentication attempts (success/failure)
- Session creation and termination
- Password reset requests
- API endpoint access with user context
- Security events (lockouts, suspicious activity)

### 2. Log Format
```json
{
    "timestamp": "2024-01-01T00:00:00Z",
    "level": "INFO|WARN|ERROR",
    "event": "auth_login|auth_logout|password_reset|etc",
    "userId": "uuid",
    "sessionId": "uuid",
    "ipAddress": "string",
    "userAgent": "string",
    "details": {}
}
```

## 🔧 Environment Variables
```env
# Database
DATABASE_URL=postgresql://...
DATABASE_POOL_SIZE=10

# JWT
JWT_SECRET=your-super-secure-secret
JWT_EXPIRATION=24h

# Email Service
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASS=your-password
FROM_EMAIL=noreply@agriaiplatform.com

# Security
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
SESSION_DURATION_HOURS=24

# Rate Limiting
RATE_LIMIT_WINDOW_MINUTES=15
RATE_LIMIT_MAX_ATTEMPTS=5
```

## 🧪 Testing Requirements

### 1. Unit Tests
- User authentication logic
- Password hashing/validation
- JWT token generation/validation
- Session management
- Rate limiting

### 2. Integration Tests
- Full authentication flow
- Password reset flow
- Session activity logging
- API endpoint security

### 3. Security Tests
- SQL injection attempts
- JWT manipulation
- Rate limiting effectiveness
- Account lockout behavior

## 🚀 Deployment Considerations

### 1. Database Migrations
- Create migration scripts for all tables
- Include proper indexes for performance
- Set up foreign key constraints

### 2. Performance Optimization
- Index on users.username and users.email
- Index on user_sessions.session_token
- Index on session_activities.user_id and timestamp
- Connection pooling for database

### 3. Monitoring
- Set up alerts for failed login patterns
- Monitor session creation rates
- Track API response times
- Database performance monitoring

## 📋 Integration Checklist

- [ ] Database schema implemented
- [ ] All authentication endpoints created
- [ ] JWT configuration complete
- [ ] Email service configured
- [ ] Security measures implemented
- [ ] CORS properly configured
- [ ] Logging system in place
- [ ] Rate limiting active
- [ ] Tests passing
- [ ] Environment variables set
- [ ] Monitoring configured

## 🔄 Frontend Integration
Once backend is implemented, the frontend will automatically connect using the existing API configuration in `src/services/api.ts`. The base URL is configured via environment variable `VITE_API_BASE_URL` or defaults to `172.28.69.96:8443`.