# Backend History Implementation Guide

This document provides a complete implementation guide for adding prediction history functionality to the AgriAI backend system.

## Overview

The history feature allows users to:
- View all their past crop predictions
- Filter and search through their prediction history
- Export their data as CSV
- View statistics about their prediction patterns

## Database Schema

### 1. Create the `prediction_logs` table

```sql
CREATE TABLE prediction_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    input_features JSON NOT NULL,
    predicted_crop VARCHAR(255) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    top_predictions JSON NOT NULL,
    status ENUM('success', 'error') DEFAULT 'success',
    processing_time INT NULL COMMENT 'Processing time in milliseconds',
    error_message TEXT NULL,
    session_id VARCHAR(255) NULL,
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_status (status),
    INDEX idx_predicted_crop (predicted_crop),
    INDEX idx_user_timestamp (user_id, timestamp DESC),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 2. Create the `prediction_statistics` table (optional for aggregated metrics)

```sql
CREATE TABLE prediction_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    date DATE NOT NULL,
    total_predictions INT DEFAULT 0,
    successful_predictions INT DEFAULT 0,
    failed_predictions INT DEFAULT 0,
    most_predicted_crop VARCHAR(255) NULL,
    avg_confidence DECIMAL(5,4) NULL,
    avg_processing_time INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_date (user_id, date),
    INDEX idx_user_id (user_id),
    INDEX idx_date (date),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

## Backend Implementation

### 1. Models (Python/SQLAlchemy Example)

```python
# models/prediction_log.py
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Numeric, Integer, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class PredictionLog(Base):
    __tablename__ = 'prediction_logs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    input_features = Column(JSON, nullable=False)
    predicted_crop = Column(String(255), nullable=False)
    confidence = Column(Numeric(5,4), nullable=False)
    top_predictions = Column(JSON, nullable=False)
    status = Column(Enum('success', 'error'), default='success')
    processing_time = Column(Integer)
    error_message = Column(Text)
    session_id = Column(String(255))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'inputFeatures': self.input_features,
            'predictedCrop': self.predicted_crop,
            'confidence': float(self.confidence) if self.confidence else 0,
            'topPredictions': self.top_predictions or [],
            'status': self.status,
            'processingTime': self.processing_time,
            'errorMessage': self.error_message
        }
```

### 2. API Endpoints

#### A. Save Prediction Log

```python
# routes/prediction_logs.py
from flask import Blueprint, request, jsonify
from models.prediction_log import PredictionLog
from utils.auth import require_auth
from database import db

prediction_logs_bp = Blueprint('prediction_logs', __name__)

@prediction_logs_bp.route('/api/prediction-logs', methods=['POST'])
@require_auth
def save_prediction_log():
    try:
        data = request.get_json()
        user_id = request.user['id']  # From auth middleware
        
        # Create new prediction log
        log = PredictionLog(
            user_id=user_id,
            input_features=data['inputFeatures'],
            predicted_crop=data['prediction']['predicted_crop'],
            confidence=data['prediction']['confidence'],
            top_predictions=data['prediction']['top_predictions'],
            status='success',
            processing_time=data.get('processingTime'),
            session_id=data.get('sessionId'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'logId': log.id,
            'message': 'Prediction log saved successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e),
            'message': 'Failed to save prediction log'
        }), 500
```

#### B. Get User Prediction Logs

```python
@prediction_logs_bp.route('/api/users/<user_id>/prediction-logs', methods=['GET'])
@require_auth
def get_user_prediction_logs(user_id):
    try:
        # Security check: ensure user can only access their own logs
        if request.user['id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Parse query parameters
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        crop = request.args.get('crop')
        status = request.args.get('status')
        order_by = request.args.get('orderBy', 'timestamp')
        order_direction = request.args.get('orderDirection', 'desc')
        
        # Build query
        query = db.session.query(PredictionLog).filter(
            PredictionLog.user_id == user_id
        )
        
        # Apply filters
        if date_from:
            query = query.filter(PredictionLog.timestamp >= date_from)
        if date_to:
            query = query.filter(PredictionLog.timestamp <= date_to)
        if crop and crop != 'all':
            query = query.filter(PredictionLog.predicted_crop.ilike(f'%{crop}%'))
        if status and status != 'all':
            query = query.filter(PredictionLog.status == status)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply ordering
        if order_direction == 'desc':
            query = query.order_by(getattr(PredictionLog, order_by).desc())
        else:
            query = query.order_by(getattr(PredictionLog, order_by).asc())
        
        # Apply pagination
        logs = query.limit(limit).offset(offset).all()
        
        return jsonify({
            'logs': [log.to_dict() for log in logs],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'hasMore': (offset + limit) < total
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to fetch prediction logs'
        }), 500
```

#### C. Get User Statistics

```python
@prediction_logs_bp.route('/api/users/<user_id>/prediction-statistics', methods=['GET'])
@require_auth
def get_user_statistics(user_id):
    try:
        # Security check
        if request.user['id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        period = request.args.get('period', '30d')
        
        # Calculate date range based on period
        from datetime import datetime, timedelta
        end_date = datetime.utcnow()
        if period == '7d':
            start_date = end_date - timedelta(days=7)
        elif period == '30d':
            start_date = end_date - timedelta(days=30)
        elif period == '90d':
            start_date = end_date - timedelta(days=90)
        elif period == '1y':
            start_date = end_date - timedelta(days=365)
        else:  # 'all'
            start_date = datetime(2000, 1, 1)
        
        # Get statistics
        from sqlalchemy import func
        
        # Total predictions
        total_predictions = db.session.query(func.count(PredictionLog.id)).filter(
            PredictionLog.user_id == user_id,
            PredictionLog.timestamp >= start_date
        ).scalar()
        
        # Successful predictions
        successful_predictions = db.session.query(func.count(PredictionLog.id)).filter(
            PredictionLog.user_id == user_id,
            PredictionLog.timestamp >= start_date,
            PredictionLog.status == 'success'
        ).scalar()
        
        # Average confidence
        avg_confidence = db.session.query(func.avg(PredictionLog.confidence)).filter(
            PredictionLog.user_id == user_id,
            PredictionLog.timestamp >= start_date,
            PredictionLog.status == 'success'
        ).scalar()
        
        # Most predicted crop
        most_predicted = db.session.query(
            PredictionLog.predicted_crop,
            func.count(PredictionLog.id).label('count')
        ).filter(
            PredictionLog.user_id == user_id,
            PredictionLog.timestamp >= start_date
        ).group_by(PredictionLog.predicted_crop).order_by(
            func.count(PredictionLog.id).desc()
        ).first()
        
        # Crop distribution
        crop_distribution = db.session.query(
            PredictionLog.predicted_crop,
            func.count(PredictionLog.id).label('count')
        ).filter(
            PredictionLog.user_id == user_id,
            PredictionLog.timestamp >= start_date
        ).group_by(PredictionLog.predicted_crop).all()
        
        crop_dist_data = []
        for crop, count in crop_distribution:
            percentage = (count / total_predictions * 100) if total_predictions > 0 else 0
            crop_dist_data.append({
                'crop': crop,
                'count': count,
                'percentage': round(percentage, 1)
            })
        
        return jsonify({
            'statistics': {
                'totalPredictions': total_predictions or 0,
                'successfulPredictions': successful_predictions or 0,
                'failedPredictions': (total_predictions or 0) - (successful_predictions or 0),
                'successRate': round((successful_predictions / total_predictions * 100) if total_predictions > 0 else 0, 1),
                'avgConfidence': round(float(avg_confidence or 0), 3),
                'mostPredictedCrop': most_predicted[0] if most_predicted else None,
                'mostPredictedCropCount': most_predicted[1] if most_predicted else 0
            },
            'cropDistribution': crop_dist_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to fetch statistics'
        }), 500
```

### 3. Modify the Existing Prediction Endpoint

```python
# In your existing predict endpoint
import time

@app.route('/predict', methods=['POST'])
def predict():
    start_time = time.time()
    user_id = None
    
    # Check if user is authenticated
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            user_data = verify_jwt_token(token)  # Your JWT verification function
            user_id = user_data.get('id')
        except:
            pass  # Continue without user context
    
    try:
        # Your existing prediction logic
        input_data = request.get_json()
        prediction_result = make_prediction(input_data)  # Your ML prediction function
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Save log if user is authenticated
        if user_id:
            try:
                log = PredictionLog(
                    user_id=user_id,
                    input_features=input_data,
                    predicted_crop=prediction_result['predicted_crop'],
                    confidence=prediction_result['confidence'],
                    top_predictions=prediction_result['top_predictions'],
                    status='success',
                    processing_time=processing_time,
                    session_id=request.headers.get('X-Session-ID'),
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(log)
                db.session.commit()
            except Exception as log_error:
                # Log error but don't fail the prediction
                print(f"Failed to save prediction log: {log_error}")
        
        return jsonify(prediction_result), 200
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        
        # Save error log if user is authenticated
        if user_id:
            try:
                log = PredictionLog(
                    user_id=user_id,
                    input_features=request.get_json(),
                    predicted_crop='',
                    confidence=0,
                    top_predictions=[],
                    status='error',
                    processing_time=processing_time,
                    error_message=str(e),
                    session_id=request.headers.get('X-Session-ID'),
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(log)
                db.session.commit()
            except:
                pass
        
        return jsonify({'error': str(e)}), 500
```

### 4. Export to CSV Endpoint

```python
import csv
import io
from flask import Response

@prediction_logs_bp.route('/api/users/<user_id>/prediction-logs/export', methods=['GET'])
@require_auth
def export_prediction_logs(user_id):
    try:
        # Security check
        if request.user['id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get logs (reuse the same filtering logic)
        # ... (same filtering code as get_user_prediction_logs)
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Date', 'Predicted Crop', 'Confidence', 
            'N', 'P', 'K', 'Temperature', 'Humidity', 'pH', 'Rainfall',
            'Status', 'Processing Time (ms)'
        ])
        
        # Write data
        for log in logs:
            writer.writerow([
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.predicted_crop,
                f"{float(log.confidence) * 100:.1f}%",
                log.input_features.get('N'),
                log.input_features.get('P'),
                log.input_features.get('K'),
                log.input_features.get('temperature'),
                log.input_features.get('humidity'),
                log.input_features.get('ph'),
                log.input_features.get('rainfall'),
                log.status,
                log.processing_time or 'N/A'
            ])
        
        # Create response
        output.seek(0)
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=predictions_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
        
        return response
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to export logs'
        }), 500
```

## Security Considerations

### 1. Authentication Middleware

```python
# utils/auth.py
from functools import wraps
from flask import request, jsonify
import jwt

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No valid authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.user = payload
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
    
    return decorated_function
```

### 2. Rate Limiting

```python
# utils/rate_limit.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to endpoints
@limiter.limit("5 per minute")
@prediction_logs_bp.route('/api/users/<user_id>/prediction-logs/export', methods=['GET'])
def export_prediction_logs(user_id):
    # ... implementation
```

## Environment Configuration

```env
# .env file
ENABLE_PREDICTION_LOGGING=true
MAX_LOGS_PER_USER=10000
LOG_RETENTION_DAYS=365
MAX_EXPORT_RECORDS=5000
EXPORT_RATE_LIMIT=5
```

## Database Maintenance

### 1. Cleanup Old Logs (Cron Job)

```python
# scripts/cleanup_old_logs.py
from datetime import datetime, timedelta
from models.prediction_log import PredictionLog
from database import db
import os

def cleanup_old_logs():
    retention_days = int(os.getenv('LOG_RETENTION_DAYS', 365))
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    # Delete logs older than retention period
    deleted = db.session.query(PredictionLog).filter(
        PredictionLog.timestamp < cutoff_date
    ).delete()
    
    db.session.commit()
    print(f"Deleted {deleted} old prediction logs")

if __name__ == "__main__":
    cleanup_old_logs()
```

### 2. Daily Statistics Aggregation

```python
# scripts/aggregate_statistics.py
from datetime import datetime, timedelta
from sqlalchemy import func
from models.prediction_log import PredictionLog
from models.prediction_statistics import PredictionStatistics
from database import db

def aggregate_daily_statistics():
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    
    # Get all users who made predictions yesterday
    users = db.session.query(PredictionLog.user_id).filter(
        func.date(PredictionLog.timestamp) == yesterday
    ).distinct().all()
    
    for (user_id,) in users:
        # Calculate statistics for this user
        stats = calculate_user_stats(user_id, yesterday)
        
        # Save or update statistics
        existing = db.session.query(PredictionStatistics).filter(
            PredictionStatistics.user_id == user_id,
            PredictionStatistics.date == yesterday
        ).first()
        
        if existing:
            update_statistics(existing, stats)
        else:
            create_statistics(user_id, yesterday, stats)
    
    db.session.commit()
```

## Testing

### 1. Unit Tests

```python
# tests/test_prediction_logs.py
import pytest
from models.prediction_log import PredictionLog
from datetime import datetime

def test_create_prediction_log():
    log = PredictionLog(
        user_id='test-user-123',
        input_features={'N': 90, 'P': 42, 'K': 43},
        predicted_crop='rice',
        confidence=0.95,
        top_predictions=[{'crop': 'rice', 'probability': 0.95}],
        status='success',
        processing_time=150
    )
    
    assert log.user_id == 'test-user-123'
    assert log.predicted_crop == 'rice'
    assert float(log.confidence) == 0.95

def test_prediction_log_to_dict():
    log = PredictionLog(
        user_id='test-user-123',
        predicted_crop='rice',
        confidence=0.95
    )
    
    dict_repr = log.to_dict()
    assert dict_repr['userId'] == 'test-user-123'
    assert dict_repr['predictedCrop'] == 'rice'
```

### 2. Integration Tests

```python
# tests/test_api_endpoints.py
import pytest
from app import app
from database import db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_user_logs_unauthorized(client):
    response = client.get('/api/users/test-user/prediction-logs')
    assert response.status_code == 401

def test_get_user_logs_with_auth(client, auth_token):
    response = client.get(
        '/api/users/test-user/prediction-logs',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    assert 'logs' in response.json
```

## Deployment Checklist

1. **Database Migration**
   - [ ] Run CREATE TABLE scripts
   - [ ] Create indexes
   - [ ] Verify foreign key constraints

2. **Backend Deployment**
   - [ ] Add new routes to main app
   - [ ] Configure environment variables
   - [ ] Test authentication middleware
   - [ ] Set up rate limiting

3. **Monitoring**
   - [ ] Set up logging for new endpoints
   - [ ] Configure alerts for high error rates
   - [ ] Monitor database growth

4. **Maintenance**
   - [ ] Schedule cleanup cron job
   - [ ] Set up statistics aggregation
   - [ ] Configure backups

## Performance Optimizations

1. **Database Indexes**
   - Composite index on (user_id, timestamp) for efficient user queries
   - Index on predicted_crop for filtering
   - Consider partitioning for very large tables

2. **Caching**
   - Cache user statistics for 5 minutes
   - Cache crop list for 1 hour

3. **Query Optimization**
   - Use pagination for all list endpoints
   - Limit maximum records per request
   - Use database aggregation functions instead of application-level calculations

## Error Handling

All endpoints should return consistent error responses:

```json
{
  "error": "Error message",
  "details": "Additional context if available",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Common HTTP status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

## Conclusion

This implementation guide provides a complete solution for adding prediction history functionality to the AgriAI backend. The implementation includes:

1. Database schema for storing prediction logs
2. RESTful API endpoints for CRUD operations
3. Security measures including authentication and rate limiting
4. Performance optimizations
5. Maintenance scripts
6. Testing strategies

Follow this guide step by step to implement the history feature successfully.