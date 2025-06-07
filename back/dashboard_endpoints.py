from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from functools import wraps
import json
from auth_utils import get_client_info, require_auth

logger = logging.getLogger(__name__)

# Create Blueprint
dashboard_bp = Blueprint('dashboard', __name__)

# Cache implementation
class SimpleCache:
    def __init__(self):
        self.cache = {}
    
    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            # Use shorter cache time for user-specific data (30 seconds)
            # and longer for general data (5 minutes)
            cache_duration = timedelta(seconds=30) if 'user' in key.lower() else timedelta(minutes=5)
            if datetime.now() - timestamp < cache_duration:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, datetime.now())
    
    def clear(self):
        self.cache.clear()
    
    def invalidate_user_cache(self, user_id):
        """Invalidate cache entries for a specific user."""
        keys_to_remove = []
        for key in self.cache.keys():
            if user_id in key or 'user' in key.lower():
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        print(f"[DEBUG] Invalidated {len(keys_to_remove)} cache entries for user {user_id[:8]}...")

cache = SimpleCache()

def invalidate_user_dashboard_cache(user_id):
    """Function to invalidate user dashboard cache after predictions."""
    if user_id:
        cache.invalidate_user_cache(user_id)
        print(f"[DEBUG] User {user_id[:8]}... dashboard cache invalidated")

def get_db_connection():
    """Get database connection from app config."""
    from flask import current_app
    try:
        print("[DEBUG] Getting database configuration...")
        # Get DB config from current app context
        db_config = current_app.config.get('DB_CONFIG')
        if not db_config:
            print("[DEBUG] No DB_CONFIG found in app, using fallback config...")
            # Fallback to direct config if not in app context
            db_config = {
                'host': '172.28.69.148',
                'port': 5432,  # PostgreSQL port, not MySQL
                'user': 'cropapi',
                'password': 'cropapi123',
                'database': 'crop_recommendations'
            }
        print(f"[DEBUG] Using DB config: {db_config}")
        conn = psycopg2.connect(**db_config)
        print("[DEBUG] Database connection successful!")
        return conn
    except Exception as e:
        print(f"[ERROR] Database connection error: {e}")
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

def with_caching(cache_key_prefix):
    """Decorator to add caching to endpoints."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_key = f"{cache_key_prefix}:{request.path}"
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for {cache_key}")
                return jsonify(cached_data), 200
            
            result = f(*args, **kwargs)
            if isinstance(result, tuple) and result[1] == 200:
                cache.set(cache_key, result[0].get_json())
            return result
        return wrapper
    return decorator

# Dashboard Endpoints

@dashboard_bp.route('/api/dashboard/user/<user_id>/metrics', methods=['GET'])
@with_caching('user_dashboard_metrics')
def get_user_dashboard_metrics(user_id):
    """Get user-specific dashboard metrics."""
    start_time = datetime.now()
    print(f"[DEBUG] User dashboard metrics endpoint called for user {user_id} at {start_time}")
    
    try:
        print("[DEBUG] Attempting to get database connection...")
        conn = get_db_connection()
        if not conn:
            print("[ERROR] Database connection failed!")
            return jsonify({'error': 'Database connection failed'}), 500
        
        print("[DEBUG] Database connection successful, creating cursor...")
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get user's predictions count and change from prediction_logs
        print(f"[DEBUG] Executing user predictions count query for user {user_id}...")
        cursor.execute("""
            WITH current_month AS (
                SELECT COUNT(*) as count 
                FROM prediction_logs 
                WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE)
                  AND user_id = %s
                  AND status = 'success'
            ),
            previous_month AS (
                SELECT COUNT(*) as count 
                FROM prediction_logs 
                WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                  AND timestamp < DATE_TRUNC('month', CURRENT_DATE)
                  AND user_id = %s
                  AND status = 'success'
            )
            SELECT 
                current_month.count as current_count,
                CASE 
                    WHEN previous_month.count = 0 THEN 100
                    ELSE ROUND(((current_month.count - previous_month.count)::numeric / previous_month.count * 100), 1)
                END as change_percentage
            FROM current_month, previous_month
        """, (user_id, user_id))
        predictions_data = cursor.fetchone()
        print(f"[DEBUG] User predictions data: {predictions_data}")
        
        # Get user's average accuracy (confidence) from their predictions
        print(f"[DEBUG] Executing user accuracy query for user {user_id}...")
        cursor.execute("""
            WITH current_month AS (
                SELECT AVG(confidence) as avg_confidence 
                FROM prediction_logs 
                WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE)
                  AND user_id = %s
                  AND status = 'success'
            ),
            previous_month AS (
                SELECT AVG(confidence) as avg_confidence 
                FROM prediction_logs 
                WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                  AND timestamp < DATE_TRUNC('month', CURRENT_DATE)
                  AND user_id = %s
                  AND status = 'success'
            )
            SELECT 
                COALESCE(current_month.avg_confidence * 100, 0) as accuracy,
                COALESCE((current_month.avg_confidence - previous_month.avg_confidence) * 100, 0) as change
            FROM current_month, previous_month
        """, (user_id, user_id))
        accuracy_data = cursor.fetchone()
        print(f"[DEBUG] User accuracy data: {accuracy_data}")
        
        # Get user's crops analyzed count from prediction_logs
        print(f"[DEBUG] Executing user crops query for user {user_id}...")
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT predicted_crop) as total_crops,
                COUNT(DISTINCT predicted_crop) FILTER (WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days') as new_crops
            FROM prediction_logs
            WHERE user_id = %s
              AND status = 'success'
              AND predicted_crop IS NOT NULL
        """, (user_id,))
        crops_data = cursor.fetchone()
        
        # Get user's weekly predictions count and change
        print(f"[DEBUG] Executing user weekly predictions query for user {user_id}...")
        cursor.execute("""
            WITH current_week AS (
                SELECT COUNT(*) as count
                FROM prediction_logs p
                WHERE p.timestamp >= DATE_TRUNC('week', CURRENT_DATE)
                  AND p.user_id = %s
                  AND p.status = 'success'
            ),
            previous_week AS (
                SELECT COUNT(*) as count
                FROM prediction_logs p
                WHERE p.timestamp >= DATE_TRUNC('week', CURRENT_DATE - INTERVAL '1 week')
                  AND p.timestamp < DATE_TRUNC('week', CURRENT_DATE)
                  AND p.user_id = %s
                  AND p.status = 'success'
            )
            SELECT 
                current_week.count as current_count,
                CASE 
                    WHEN previous_week.count = 0 THEN 100
                    ELSE ROUND(((current_week.count - previous_week.count)::numeric / previous_week.count * 100), 1)
                END as change_percentage
            FROM current_week, previous_week
        """, (user_id, user_id))
        users_data = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print("[DEBUG] Building user-specific response...")
        response = {
            "predictions_generated": predictions_data['current_count'] if predictions_data else 0,
            "predictions_change": float(predictions_data['change_percentage']) if predictions_data else 0,
            "model_accuracy": round(float(accuracy_data['accuracy']), 2) if accuracy_data and accuracy_data['accuracy'] else 0,
            "accuracy_change": round(float(accuracy_data['change']), 2) if accuracy_data and accuracy_data['change'] else 0,
            "crops_analyzed": crops_data['total_crops'] if crops_data else 0,
            "new_crops": crops_data['new_crops'] if crops_data else 0,
            "weekly_predictions": users_data['current_count'] if users_data else 0,
            "weekly_change": float(users_data['change_percentage']) if users_data else 0
        }
        print(f"[DEBUG] Final user response: {response}")
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request(f'/api/dashboard/user/{user_id}/metrics', 'GET', 200, response_time)
        
        return jsonify(response), 200
        
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request(f'/api/dashboard/user/{user_id}/metrics', 'GET', 500, response_time, str(e))
        print(f"[ERROR] User dashboard metrics error: {e}")
        logger.error(f"User dashboard metrics error: {e}", exc_info=True)
        
        # Return empty user data as fallback
        print("[DEBUG] Returning empty user data due to error")
        return jsonify({
            "predictions_generated": 0,
            "predictions_change": 0,
            "model_accuracy": 0,
            "accuracy_change": 0,
            "crops_analyzed": 0,
            "new_crops": 0,
            "weekly_predictions": 0,
            "weekly_change": 0
        }), 200

@dashboard_bp.route('/api/dashboard/user/<user_id>/monthly-predictions', methods=['GET'])
@with_caching('user_monthly_predictions')
def get_user_monthly_predictions(user_id):
    """Get user's monthly prediction counts."""
    start_time = datetime.now()
    print(f"[DEBUG] User monthly predictions endpoint called for user {user_id}")
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get last 6 months of user's predictions from prediction_logs
        print(f"[DEBUG] Executing user monthly predictions query for user {user_id}...")
        cursor.execute("""
            SELECT 
                TO_CHAR(DATE_TRUNC('month', timestamp), 'Mon') as month,
                COUNT(*) as predictions
            FROM prediction_logs
            WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '5 months')
              AND user_id = %s
              AND status = 'success'
            GROUP BY DATE_TRUNC('month', timestamp)
            ORDER BY DATE_TRUNC('month', timestamp)
        """, (user_id,))
        
        monthly_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Ensure we have 6 months of data
        months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        current_month = datetime.now().month
        result_data = []
        
        for i in range(6):
            month_idx = (current_month - 6 + i) % 12
            month_name = months[month_idx]
            
            # Find data for this month
            month_data = next((m for m in monthly_data if m['month'] == month_name), None)
            
            result_data.append({
                "month": month_name,
                "predictions": month_data['predictions'] if month_data else 0
            })
        
        response = {
            "data": result_data,
            "timestamp": datetime.now().isoformat()
        }
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request(f'/api/dashboard/user/{user_id}/monthly-predictions', 'GET', 200, response_time)
        
        print(f"[DEBUG] Returning user monthly data: {response}")
        return jsonify(response), 200
        
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request(f'/api/dashboard/user/{user_id}/monthly-predictions', 'GET', 500, response_time, str(e))
        print(f"[ERROR] User monthly predictions error: {e}")
        logger.error(f"User monthly predictions error: {e}", exc_info=True)
        
        # Return empty data for user
        return jsonify({
            "data": [
                {"month": "Ene", "predictions": 0},
                {"month": "Feb", "predictions": 0},
                {"month": "Mar", "predictions": 0},
                {"month": "Abr", "predictions": 0},
                {"month": "May", "predictions": 0},
                {"month": "Jun", "predictions": 0}
            ],
            "timestamp": datetime.now().isoformat()
        }), 200

@dashboard_bp.route('/api/dashboard/user/<user_id>/crop-distribution', methods=['GET'])
@with_caching('user_crop_distribution')
def get_user_crop_distribution(user_id):
    """Get user's crop distribution data."""
    start_time = datetime.now()
    print(f"[DEBUG] User crop distribution endpoint called for user {user_id}")
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get user's crop distribution from prediction_logs
        print(f"[DEBUG] Executing user crop distribution query for user {user_id}...")
        cursor.execute("""
            SELECT 
                predicted_crop as crop,
                COUNT(*) as count
            FROM prediction_logs
            WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
              AND user_id = %s
              AND status = 'success'
              AND predicted_crop IS NOT NULL
            GROUP BY predicted_crop
            ORDER BY count DESC
            LIMIT 5
        """, (user_id,))
        
        crop_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Define colors for crops
        colors = ["#10b981", "#059669", "#047857", "#065f46", "#064e3b"]
        
        result_data = []
        for i, crop in enumerate(crop_data):
            result_data.append({
                "crop": crop['crop'],
                "count": crop['count'],
                "color": colors[i % len(colors)]
            })
        
        response = {
            "data": result_data,
            "timestamp": datetime.now().isoformat()
        }
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request(f'/api/dashboard/user/{user_id}/crop-distribution', 'GET', 200, response_time)
        
        print(f"[DEBUG] Returning user crop distribution: {response}")
        return jsonify(response), 200
        
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request(f'/api/dashboard/user/{user_id}/crop-distribution', 'GET', 500, response_time, str(e))
        print(f"[ERROR] User crop distribution error: {e}")
        logger.error(f"User crop distribution error: {e}", exc_info=True)
        
        # Return empty data for user
        return jsonify({
            "data": [],
            "timestamp": datetime.now().isoformat()
        }), 200

# Test endpoint to verify blueprints are working
@dashboard_bp.route('/api/dashboard/test', methods=['GET'])
def test_dashboard():
    """Test endpoint to verify dashboard blueprint is working."""
    print("[DEBUG] Test dashboard endpoint called")
    return jsonify({"status": "ok", "message": "Dashboard blueprint is working!"}), 200

# Compatibility endpoints for frontend that expects original URLs
@dashboard_bp.route('/api/dashboard/metrics', methods=['GET'])
@with_caching('dashboard_metrics_compat')
def get_dashboard_metrics_compatibility():
    """Get dashboard metrics - compatibility endpoint that gets user from auth context."""
    from auth_utils import verify_jwt_token
    
    print("[DEBUG] Compatibility dashboard metrics endpoint called")
    
    # Get user from auth token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        print("[DEBUG] No auth header found, returning guaranteed safe data")
        # Return GUARANTEED safe data if no auth
        return jsonify({
            "predictions_generated": 0,
            "predictions_change": 0.0,
            "model_accuracy": 0.0,
            "accuracy_change": 0.0,
            "crops_analyzed": 0,
            "new_crops": 0,
            "active_users": 0,
            "users_change": 0.0
        }), 200
    
    token = auth_header.split(' ')[1]
    user_data = verify_jwt_token(token)
    
    if not user_data:
        print("[DEBUG] Invalid token, returning guaranteed safe data")
        # Return GUARANTEED safe data if invalid token
        return jsonify({
            "predictions_generated": 0,
            "predictions_change": 0.0,
            "model_accuracy": 0.0,
            "accuracy_change": 0.0,
            "crops_analyzed": 0,
            "new_crops": 0,
            "active_users": 0,
            "users_change": 0.0
        }), 200
    
    user_id = user_data.get('user_id')
    if not user_id:
        print("[DEBUG] No user ID in token")
        return jsonify({'error': 'User ID not found in token'}), 400
    
    print(f"[DEBUG] Calling user-specific endpoint for user {user_id}")
    
    try:
        # Call the user-specific endpoint directly without Flask response wrapper
        start_time = datetime.now()
        conn = get_db_connection()
        if not conn:
            print("[ERROR] Database connection failed in compatibility endpoint")
            return jsonify({
                "predictions_generated": 0,
                "predictions_change": 0,
                "model_accuracy": 0,
                "accuracy_change": 0,
                "crops_analyzed": 0,
                "new_crops": 0,
                "active_users": 0,
                "users_change": 0
            }), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get user's predictions count and change from prediction_logs
        print(f"[DEBUG] Executing user predictions count query for compatibility endpoint user {user_id}...")
        cursor.execute("""
            WITH current_month AS (
                SELECT COUNT(*) as count 
                FROM prediction_logs 
                WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE)
                  AND user_id = %s
                  AND status = 'success'
            ),
            previous_month AS (
                SELECT COUNT(*) as count 
                FROM prediction_logs 
                WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                  AND timestamp < DATE_TRUNC('month', CURRENT_DATE)
                  AND user_id = %s
                  AND status = 'success'
            )
            SELECT 
                current_month.count as current_count,
                CASE 
                    WHEN previous_month.count = 0 THEN 100
                    ELSE ROUND(((current_month.count - previous_month.count)::numeric / previous_month.count * 100), 1)
                END as change_percentage
            FROM current_month, previous_month
        """, (user_id, user_id))
        predictions_data = cursor.fetchone()
        print(f"[DEBUG] Compatibility predictions data: {predictions_data}")
        
        # Get user's average accuracy (confidence) from their predictions
        cursor.execute("""
            WITH current_month AS (
                SELECT AVG(confidence) as avg_confidence 
                FROM prediction_logs 
                WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE)
                  AND user_id = %s
                  AND status = 'success'
            ),
            previous_month AS (
                SELECT AVG(confidence) as avg_confidence 
                FROM prediction_logs 
                WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                  AND timestamp < DATE_TRUNC('month', CURRENT_DATE)
                  AND user_id = %s
                  AND status = 'success'
            )
            SELECT 
                COALESCE(current_month.avg_confidence * 100, 0) as accuracy,
                COALESCE((current_month.avg_confidence - previous_month.avg_confidence) * 100, 0) as change
            FROM current_month, previous_month
        """, (user_id, user_id))
        accuracy_data = cursor.fetchone()
        print(f"[DEBUG] Compatibility accuracy data: {accuracy_data}")
        
        # Get user's crops analyzed count
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT predicted_crop) as total_crops,
                COUNT(DISTINCT predicted_crop) FILTER (WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days') as new_crops
            FROM prediction_logs
            WHERE user_id = %s
              AND status = 'success'
              AND predicted_crop IS NOT NULL
        """, (user_id,))
        crops_data = cursor.fetchone()
        print(f"[DEBUG] Compatibility crops data: {crops_data}")
        
        # Get user's weekly predictions count
        cursor.execute("""
            WITH current_week AS (
                SELECT COUNT(*) as count
                FROM prediction_logs p
                WHERE p.timestamp >= DATE_TRUNC('week', CURRENT_DATE)
                  AND p.user_id = %s
                  AND p.status = 'success'
            ),
            previous_week AS (
                SELECT COUNT(*) as count
                FROM prediction_logs p
                WHERE p.timestamp >= DATE_TRUNC('week', CURRENT_DATE - INTERVAL '1 week')
                  AND p.timestamp < DATE_TRUNC('week', CURRENT_DATE)
                  AND p.user_id = %s
                  AND p.status = 'success'
            )
            SELECT 
                current_week.count as current_count,
                CASE 
                    WHEN previous_week.count = 0 THEN 100
                    ELSE ROUND(((current_week.count - previous_week.count)::numeric / previous_week.count * 100), 1)
                END as change_percentage
            FROM current_week, previous_week
        """, (user_id, user_id))
        weekly_data = cursor.fetchone()
        print(f"[DEBUG] Compatibility weekly data: {weekly_data}")
        
        cursor.close()
        conn.close()
        
        # Build GUARANTEED safe response - all values are guaranteed to be valid numbers
        def safe_int(value, default=0):
            """Ensure value is a valid integer."""
            if value is None:
                return default
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return default
        
        def safe_float(value, default=0.0):
            """Ensure value is a valid float."""
            if value is None:
                return default
            try:
                return float(value)
            except (TypeError, ValueError):
                return default
        
        frontend_response = {
            "predictions_generated": safe_int(predictions_data['current_count'] if predictions_data else 0),
            "predictions_change": safe_float(predictions_data['change_percentage'] if predictions_data else 0.0),
            "model_accuracy": round(safe_float(accuracy_data['accuracy'] if accuracy_data else 0.0), 2),
            "accuracy_change": round(safe_float(accuracy_data['change'] if accuracy_data else 0.0), 2),
            "crops_analyzed": safe_int(crops_data['total_crops'] if crops_data else 0),
            "new_crops": safe_int(crops_data['new_crops'] if crops_data else 0),
            "active_users": safe_int(weekly_data['current_count'] if weekly_data else 0),
            "users_change": safe_float(weekly_data['change_percentage'] if weekly_data else 0.0)
        }
        
        print(f"[DEBUG] Final compatibility response: {frontend_response}")
        return jsonify(frontend_response), 200
        
    except Exception as e:
        print(f"[ERROR] Error in compatibility endpoint: {e}")
        # Return GUARANTEED safe fallback values
        return jsonify({
            "predictions_generated": 0,
            "predictions_change": 0.0,
            "model_accuracy": 0.0,
            "accuracy_change": 0.0,
            "crops_analyzed": 0,
            "new_crops": 0,
            "active_users": 0,
            "users_change": 0.0
        }), 200

@dashboard_bp.route('/api/dashboard/monthly-predictions', methods=['GET'])
@with_caching('monthly_predictions_compat')
def get_monthly_predictions_compatibility():
    """Get monthly predictions - compatibility endpoint."""
    from auth_utils import verify_jwt_token
    
    print("[DEBUG] Compatibility monthly predictions endpoint called")
    
    # Get user from auth token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        # Return GUARANTEED safe empty data
        return jsonify({
            "data": [{"month": month, "predictions": 0} for month in ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]],
            "timestamp": datetime.now().isoformat()
        }), 200
    
    token = auth_header.split(' ')[1]
    user_data = verify_jwt_token(token)
    
    if not user_data:
        # Return GUARANTEED safe data for invalid tokens
        return jsonify({
            "data": [{"month": month, "predictions": 0} for month in ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]],
            "timestamp": datetime.now().isoformat()
        }), 200
    
    user_id = user_data.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID not found in token'}), 400
    
    print(f"[DEBUG] Calling user monthly predictions for user {user_id}")
    # Call the user-specific endpoint internally
    return get_user_monthly_predictions(user_id)

@dashboard_bp.route('/api/dashboard/cache/clear', methods=['POST'])
@require_auth
def clear_user_cache():
    """Clear cache for the authenticated user."""
    try:
        user_id = request.current_user['id']
        cache.invalidate_user_cache(user_id)
        return jsonify({
            "message": "Cache cleared successfully",
            "user_id": user_id[:8] + "...",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "error": "Failed to clear cache",
            "details": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@dashboard_bp.route('/api/dashboard/crop-distribution', methods=['GET'])
@with_caching('crop_distribution_compat')
def get_crop_distribution_compatibility():
    """Get crop distribution - compatibility endpoint."""
    from auth_utils import verify_jwt_token
    
    print("[DEBUG] Compatibility crop distribution endpoint called")
    
    # Get user from auth token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"data": [], "timestamp": datetime.now().isoformat()}), 200
    
    token = auth_header.split(' ')[1]
    user_data = verify_jwt_token(token)
    
    if not user_data:
        return jsonify({"data": [], "timestamp": datetime.now().isoformat()}), 200
    
    user_id = user_data.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID not found in token'}), 400
    
    print(f"[DEBUG] Calling user crop distribution for user {user_id}")
    # Call the user-specific endpoint internally
    return get_user_crop_distribution(user_id)