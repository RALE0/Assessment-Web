# Database Schema for Authentication System

## Overview
This document specifies the database schema requirements for the complete authentication system including user registration, login, session management, and activity logging.

## 🗄️ Database Tables

### 1. Users Table
**Purpose:** Store user account information and credentials

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP NULL,
    email_verified BOOLEAN DEFAULT false,
    email_verification_token VARCHAR(255) NULL,
    email_verification_expires_at TIMESTAMP NULL
);
```

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_email_verification_token ON users(email_verification_token);
```

**Field Descriptions:**
- `id`: Unique identifier for the user (UUID)
- `username`: Unique username (3-50 characters)
- `email`: Unique email address for account recovery and notifications
- `password_hash`: Bcrypt hashed password (minimum 6 characters before hashing)
- `created_at`: Account creation timestamp
- `updated_at`: Last account modification timestamp
- `last_login_at`: Timestamp of most recent successful login
- `is_active`: Account status (for soft deletion/deactivation)
- `failed_login_attempts`: Counter for failed login attempts (security)
- `locked_until`: Account lockout expiration (15 minutes after 5 failed attempts)
- `email_verified`: Whether email address has been verified
- `email_verification_token`: Token for email verification process
- `email_verification_expires_at`: Expiration time for verification token

### 2. User Sessions Table
**Purpose:** Track active user sessions and authentication tokens

```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    ended_at TIMESTAMP NULL,
    logout_reason VARCHAR(50) NULL -- 'user_logout', 'expired', 'admin_logout', 'security'
);
```

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_sessions_is_active ON user_sessions(is_active);
```

**Field Descriptions:**
- `session_token`: JWT token or session identifier
- `ip_address`: IP address where session was created
- `user_agent`: Browser/client information
- `expires_at`: When the session expires (24 hours from creation)
- `last_activity_at`: Last time session was used
- `logout_reason`: Reason session ended

### 3. Session Activities Table
**Purpose:** Log all user activities for security and analytics

```sql
CREATE TABLE session_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES user_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    activity_details JSONB,
    page_url VARCHAR(500),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER NULL -- For page view duration tracking
);
```

**Indexes:**
```sql
CREATE INDEX idx_activities_user_id ON session_activities(user_id);
CREATE INDEX idx_activities_session_id ON session_activities(session_id);
CREATE INDEX idx_activities_timestamp ON session_activities(timestamp);
CREATE INDEX idx_activities_type ON session_activities(activity_type);
CREATE INDEX idx_activities_details ON session_activities USING GIN(activity_details);
```

**Activity Types:**
- `signup`: User account creation
- `login`: Successful login
- `login_failed`: Failed login attempt
- `logout`: User logout
- `password_reset_request`: Password reset initiated
- `password_reset_complete`: Password successfully reset
- `page_view`: Page navigation
- `api_call`: API endpoint access
- `session_expired`: Automatic session expiration

**Field Descriptions:**
- `activity_details`: JSON object with additional context
- `page_url`: Frontend page URL (for page_view activities)
- `duration_ms`: Time spent on page (for page_view activities)

### 4. Password Reset Tokens Table
**Purpose:** Manage password reset requests and tokens

```sql
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);
```

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX idx_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX idx_reset_tokens_expires_at ON password_reset_tokens(expires_at);
```

**Field Descriptions:**
- `token`: Secure random token for password reset
- `expires_at`: Token expiration (1 hour from creation)
- `used_at`: When token was used (null if unused)
- `ip_address`: IP where reset was requested
- `user_agent`: Browser/client where reset was requested

## 🔐 Security Considerations

### Password Security
- **Hashing Algorithm:** bcrypt with minimum 12 rounds
- **Password Requirements:** Minimum 6 characters (enforced in frontend)
- **Password Storage:** Never store plaintext passwords

### Account Security
- **Account Lockout:** 5 failed attempts locks account for 15 minutes
- **Session Limits:** Maximum 5 concurrent sessions per user
- **Token Expiration:** 
  - Session tokens: 24 hours
  - Password reset tokens: 1 hour
  - Email verification tokens: 24 hours

### Data Protection
- **IP Tracking:** Store IP addresses for security monitoring
- **User Agent Tracking:** Track browser/device for session validation
- **Activity Logging:** Comprehensive audit trail for security analysis

## 📊 Database Constraints and Triggers

### Update Trigger for Users Table
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Session Cleanup Trigger
```sql
-- Automatically mark sessions as inactive when ended_at is set
CREATE OR REPLACE FUNCTION mark_session_inactive()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ended_at IS NOT NULL AND OLD.ended_at IS NULL THEN
        NEW.is_active = false;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER session_end_trigger BEFORE UPDATE ON user_sessions
    FOR EACH ROW EXECUTE FUNCTION mark_session_inactive();
```

### Cleanup Expired Tokens
```sql
-- Function to clean up expired tokens (run periodically)
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Clean up expired password reset tokens
    DELETE FROM password_reset_tokens 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up expired sessions
    UPDATE user_sessions 
    SET is_active = false, ended_at = CURRENT_TIMESTAMP, logout_reason = 'expired'
    WHERE expires_at < CURRENT_TIMESTAMP AND is_active = true;
    
    RETURN deleted_count;
END;
$$ language 'plpgsql';
```

## 🔍 Common Queries

### User Authentication
```sql
-- Verify user credentials
SELECT id, username, email, password_hash, failed_login_attempts, locked_until, is_active
FROM users 
WHERE username = $1 AND is_active = true;

-- Update last login
UPDATE users 
SET last_login_at = CURRENT_TIMESTAMP, failed_login_attempts = 0 
WHERE id = $1;

-- Increment failed attempts
UPDATE users 
SET failed_login_attempts = failed_login_attempts + 1,
    locked_until = CASE 
        WHEN failed_login_attempts + 1 >= 5 
        THEN CURRENT_TIMESTAMP + INTERVAL '15 minutes'
        ELSE locked_until 
    END
WHERE id = $1;
```

### Session Management
```sql
-- Create new session
INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, expires_at)
VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP + INTERVAL '24 hours');

-- Validate session
SELECT us.*, u.username, u.email 
FROM user_sessions us
JOIN users u ON u.id = us.user_id
WHERE us.session_token = $1 
  AND us.is_active = true 
  AND us.expires_at > CURRENT_TIMESTAMP;

-- End session
UPDATE user_sessions 
SET is_active = false, ended_at = CURRENT_TIMESTAMP, logout_reason = 'user_logout'
WHERE session_token = $1;
```

### Activity Logging
```sql
-- Log activity
INSERT INTO session_activities (session_id, user_id, activity_type, activity_details, page_url, ip_address, user_agent)
VALUES ($1, $2, $3, $4, $5, $6, $7);

-- Get user activity history
SELECT * FROM session_activities 
WHERE user_id = $1 
ORDER BY timestamp DESC 
LIMIT 100;
```

## 📋 Migration Scripts

### Initial Migration
```sql
-- Create all tables in order
-- 1. Users table (no dependencies)
-- 2. User sessions table (depends on users)
-- 3. Session activities table (depends on users and sessions)
-- 4. Password reset tokens table (depends on users)

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext"; -- For case-insensitive email

-- Modify users table to use citext for email
ALTER TABLE users ALTER COLUMN email TYPE citext;
```

### Performance Optimization
```sql
-- Additional indexes for performance
CREATE INDEX idx_users_active_created ON users(is_active, created_at);
CREATE INDEX idx_sessions_user_active ON user_sessions(user_id, is_active);
CREATE INDEX idx_activities_user_timestamp ON session_activities(user_id, timestamp DESC);
```

## 🚀 Deployment Checklist

- [ ] Create database with UUID extension
- [ ] Run table creation scripts in dependency order
- [ ] Create all indexes
- [ ] Set up triggers and functions
- [ ] Configure periodic cleanup job for expired tokens
- [ ] Set appropriate database permissions
- [ ] Configure connection pooling
- [ ] Set up database monitoring
- [ ] Create backup strategy
- [ ] Test all queries with sample data

## 📈 Monitoring and Maintenance

### Daily Maintenance
- Clean up expired tokens and sessions
- Monitor failed login attempts
- Check for unusual activity patterns

### Weekly Reports
- User registration trends
- Session duration analytics
- Security incident summary
- Database performance metrics

### Alerts
- Multiple failed login attempts from same IP
- Unusual number of password reset requests
- High number of concurrent sessions
- Database performance degradation