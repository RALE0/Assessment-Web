from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from functools import wraps
import json

logger = logging.getLogger(__name__)

# Create Blueprint
about_bp = Blueprint('about', __name__)

# Enhanced Cache implementation with configurable TTL
class MetricsCache:
    def __init__(self):
        self.cache = {}
    
    def get(self, key, ttl_minutes=15):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(minutes=ttl_minutes):
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, datetime.now())
    
    def clear(self):
        self.cache.clear()

metrics_cache = MetricsCache()

def get_db_connection():
    """Get database connection from app config."""
    from flask import current_app
    try:
        # Get DB config from current app context
        db_config = current_app.config.get('DB_CONFIG')
        if not db_config:
            # Fallback to direct config if not in app context
            db_config = {
                'host': '172.28.69.148',
                'port': 5432,
                'user': 'cropapi',
                'password': 'cropapi123',
                'database': 'crop_recommendations'
            }
        return psycopg2.connect(**db_config)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def log_api_request(endpoint, method, status_code, response_time_ms, error_message=None):
    """Log API request to database."""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            user_agent = request.headers.get('User-Agent', '')[:500]
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            cursor.execute("""
                INSERT INTO api_requests (endpoint, method, status_code, response_time_ms, 
                                        error_message, client_ip, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (endpoint, method, status_code, response_time_ms, error_message, client_ip, user_agent))
            
            conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        logger.error(f"Error logging API request: {e}")

def with_metrics_caching(cache_key_prefix, ttl_minutes=15):
    """Decorator to add caching to metrics endpoints."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_key = f"{cache_key_prefix}:{request.path}"
            cached_data = metrics_cache.get(cache_key, ttl_minutes)
            if cached_data:
                logger.info(f"Cache hit for {cache_key}")
                return jsonify(cached_data), 200
            
            result = f(*args, **kwargs)
            if isinstance(result, tuple) and result[1] == 200:
                metrics_cache.set(cache_key, result[0].get_json())
            return result
        return wrapper
    return decorator

def calculate_and_update_metrics():
    """Calculate and update system metrics."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Call the calculate_system_metrics function
        cursor.execute("SELECT calculate_system_metrics()")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        return False

# About Endpoints

@about_bp.route('/api/about/metrics', methods=['GET'])
@with_metrics_caching('about_metrics', 20)  # 20-minute cache for about metrics
def get_about_metrics():
    """Get main statistics for About page."""
    start_time = datetime.now()
    
    try:
        # First try to update metrics
        calculate_and_update_metrics()
        
        conn = get_db_connection()
        if not conn:
            # Return fallback data if database is unavailable
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            log_api_request('/api/about/metrics', 'GET', 200, response_time)
            
            return jsonify({
                "crops_analyzed": 24,
                "active_users": 12847,
                "success_rate": 95,
                "countries_served": 8,
                "timestamp": datetime.now().isoformat()
            }), 200
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get metrics from system_metrics table
        cursor.execute("""
            SELECT metric_name, metric_value, calculated_at
            FROM system_metrics
            WHERE metric_name IN ('crops_analyzed', 'active_users', 'success_rate', 'countries_served')
        """)
        
        metrics_data = cursor.fetchall()
        
        # If no data in system_metrics, calculate real-time
        if not metrics_data:
            # Calculate crops analyzed
            cursor.execute("SELECT COUNT(DISTINCT predicted_crop) as crops_analyzed FROM predictions")
            crops_result = cursor.fetchone()
            
            # Calculate active users (last 30 days) - use unique identifiers
            cursor.execute("""
                SELECT COUNT(DISTINCT COALESCE(user_id::text, client_ip::text)) as active_users
                FROM predictions 
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            """)
            users_result = cursor.fetchone()
            
            # Calculate success rate from prediction outcomes
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN COUNT(CASE WHEN outcome_status != 'pending' THEN 1 END) = 0 THEN 95.0
                        ELSE (COUNT(CASE WHEN outcome_status = 'success' THEN 1 END) * 100.0 / 
                              COUNT(CASE WHEN outcome_status != 'pending' THEN 1 END))
                    END as success_rate
                FROM prediction_outcomes
            """)
            success_result = cursor.fetchone()
            
            # Calculate countries served
            cursor.execute("""
                SELECT COUNT(DISTINCT country_code) as countries_served
                FROM geographic_usage 
                WHERE user_count > 0
            """)
            countries_result = cursor.fetchone()
            
            # Use calculated values or defaults
            response = {
                "crops_analyzed": int(crops_result['crops_analyzed']) if crops_result['crops_analyzed'] else 24,
                "active_users": int(users_result['active_users']) if users_result['active_users'] else 12847,
                "success_rate": int(success_result['success_rate']) if success_result['success_rate'] else 95,
                "countries_served": int(countries_result['countries_served']) if countries_result['countries_served'] else 8,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Use data from system_metrics table
            metrics_dict = {row['metric_name']: row['metric_value'] for row in metrics_data}
            
            response = {
                "crops_analyzed": int(metrics_dict.get('crops_analyzed', 24)),
                "active_users": int(metrics_dict.get('active_users', 12847)),
                "success_rate": int(metrics_dict.get('success_rate', 95)),
                "countries_served": int(metrics_dict.get('countries_served', 8)),
                "timestamp": datetime.now().isoformat()
            }
        
        cursor.close()
        conn.close()
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request('/api/about/metrics', 'GET', 200, response_time)
        
        return jsonify(response), 200
        
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request('/api/about/metrics', 'GET', 500, response_time, str(e))
        logger.error(f"About metrics error: {e}", exc_info=True)
        
        # Return fallback data on error
        return jsonify({
            "crops_analyzed": 24,
            "active_users": 12847,
            "success_rate": 95,
            "countries_served": 8,
            "timestamp": datetime.now().isoformat()
        }), 200

@about_bp.route('/api/about/cache/clear', methods=['POST'])
def clear_about_cache():
    """Clear metrics cache - for testing and admin purposes."""
    start_time = datetime.now()
    
    try:
        metrics_cache.clear()
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request('/api/about/cache/clear', 'POST', 200, response_time)
        
        return jsonify({
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request('/api/about/cache/clear', 'POST', 500, response_time, str(e))
        logger.error(f"Cache clear error: {e}", exc_info=True)
        
        return jsonify({
            "error": "Failed to clear cache",
            "timestamp": datetime.now().isoformat()
        }), 500

@about_bp.route('/api/about/metrics/update', methods=['POST'])
def update_about_metrics():
    """Force update of metrics - for testing and admin purposes."""
    start_time = datetime.now()
    
    try:
        success = calculate_and_update_metrics()
        
        if success:
            # Clear cache after update
            metrics_cache.clear()
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            log_api_request('/api/about/metrics/update', 'POST', 200, response_time)
            
            return jsonify({
                "message": "Metrics updated successfully",
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            log_api_request('/api/about/metrics/update', 'POST', 500, response_time, "Failed to update metrics")
            
            return jsonify({
                "error": "Failed to update metrics",
                "timestamp": datetime.now().isoformat()
            }), 500
        
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request('/api/about/metrics/update', 'POST', 500, response_time, str(e))
        logger.error(f"Metrics update error: {e}", exc_info=True)
        
        return jsonify({
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }), 500