"""
Prediction log endpoints for the crop recommendation API.
"""

from flask import Blueprint, request, jsonify, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, date
import time
import logging
from auth_utils import require_auth, require_auth_optional, get_client_info, create_error_response, create_success_response
from prediction_log_models import PredictionLogDatabase

logger = logging.getLogger(__name__)

prediction_logs_bp = Blueprint('prediction_logs', __name__)

def get_prediction_log_db():
    """Get prediction log database instance from app config."""
    from flask import current_app
    db_config = current_app.config.get('DB_CONFIG')
    return PredictionLogDatabase(db_config)

@prediction_logs_bp.route('/api/prediction-logs', methods=['POST'])
@require_auth
def create_prediction_log():
    """Save prediction log endpoint."""
    start_time = time.time()
    
    try:
        if not request.is_json:
            return create_error_response("Request must be JSON", status_code=400)
        
        data = request.get_json()
        if not data:
            return create_error_response("No JSON data provided", status_code=400)
        
        # Validate required fields
        required_fields = ['userId', 'inputFeatures', 'prediction']
        for field in required_fields:
            if field not in data:
                return create_error_response(f"Missing required field: {field}", status_code=400)
        
        # Validate user authorization - users can only create logs for themselves
        current_user = request.current_user
        if current_user['id'] != data['userId']:
            return create_error_response("Unauthorized to create logs for other users", status_code=403)
        
        # Validate input features
        input_features = data['inputFeatures']
        required_features = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
        for feature in required_features:
            if feature not in input_features:
                return create_error_response(f"Missing input feature: {feature}", status_code=400)
            try:
                float(input_features[feature])
            except (ValueError, TypeError):
                return create_error_response(f"Invalid value for feature: {feature}", status_code=400)
        
        # Validate prediction data
        prediction = data['prediction']
        if 'predicted_crop' not in prediction:
            return create_error_response("Missing predicted_crop in prediction", status_code=400)
        
        if 'confidence' not in prediction:
            return create_error_response("Missing confidence in prediction", status_code=400)
        
        try:
            confidence = float(prediction['confidence'])
            if not (0 <= confidence <= 1):
                return create_error_response("Confidence must be between 0 and 1", status_code=400)
        except (ValueError, TypeError):
            return create_error_response("Invalid confidence value", status_code=400)
        
        # Get client info
        ip_address, user_agent = get_client_info(request)
        
        # Prepare log data
        log_data = {
            'user_id': data['userId'],
            'input_features': input_features,
            'predicted_crop': prediction['predicted_crop'],
            'confidence': confidence,
            'top_predictions': prediction.get('top_predictions', []),
            'status': 'success',  # Assume success if we're manually logging
            'processing_time': data.get('processingTime'),
            'session_id': data.get('sessionId'),
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        # Save to database
        prediction_log_db = get_prediction_log_db()
        log_id = prediction_log_db.save_prediction_log(log_data)
        
        if not log_id:
            return create_error_response("Failed to save prediction log", status_code=500)
        
        response_data = {
            'logId': log_id,
            'message': 'Prediction log saved successfully'
        }
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Prediction log created successfully: {log_id} (processing time: {processing_time}ms)")
        
        return create_success_response(response_data, status_code=201)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"Error creating prediction log: {e}", exc_info=True)
        return create_error_response("Internal server error", status_code=500)

@prediction_logs_bp.route('/api/users/<user_id>/prediction-logs', methods=['GET'])
@require_auth
def get_user_prediction_logs(user_id):
    """Get prediction logs for a user."""
    start_time = time.time()
    
    try:
        # Validate user authorization - users can only access their own logs
        current_user = request.current_user
        if current_user['id'] != user_id:
            return create_error_response("Unauthorized to access other users' logs", status_code=403)
        
        # Parse query parameters
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
        offset = int(request.args.get('offset', 0))
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        crop = request.args.get('crop')
        status = request.args.get('status')
        order_by = request.args.get('orderBy', 'timestamp')
        order_direction = request.args.get('orderDirection', 'desc')
        
        # Validate date parameters
        filters = {}
        if date_from:
            try:
                filters['date_from'] = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except ValueError:
                return create_error_response("Invalid dateFrom format. Use YYYY-MM-DD", status_code=400)
        
        if date_to:
            try:
                filters['date_to'] = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except ValueError:
                return create_error_response("Invalid dateTo format. Use YYYY-MM-DD", status_code=400)
        
        if crop:
            filters['crop'] = crop
        
        if status and status in ['success', 'error']:
            filters['status'] = status
        
        # Validate order parameters
        valid_order_fields = ['timestamp', 'confidence', 'predicted_crop', 'processing_time']
        if order_by not in valid_order_fields:
            order_by = 'timestamp'
        
        if order_direction.lower() not in ['asc', 'desc']:
            order_direction = 'desc'
        
        filters['order_by'] = order_by
        filters['order_direction'] = order_direction
        
        pagination = {
            'limit': limit,
            'offset': offset
        }
        
        # Get logs from database
        prediction_log_db = get_prediction_log_db()
        result = prediction_log_db.get_user_prediction_logs(user_id, filters, pagination)
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Retrieved {len(result['logs'])} prediction logs for user {user_id} (processing time: {processing_time}ms)")
        
        return create_success_response(result)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"Error getting user prediction logs: {e}", exc_info=True)
        return create_error_response("Internal server error", status_code=500)

@prediction_logs_bp.route('/api/users/<user_id>/prediction-statistics', methods=['GET'])
@require_auth
def get_user_prediction_statistics(user_id):
    """Get prediction statistics for a user."""
    start_time = time.time()
    
    try:
        # Validate user authorization - users can only access their own statistics
        current_user = request.current_user
        if current_user['id'] != user_id:
            return create_error_response("Unauthorized to access other users' statistics", status_code=403)
        
        # Parse query parameters
        period = request.args.get('period', '30d')  # 7d, 30d, 90d, 1y, all
        group_by = request.args.get('groupBy', 'day')  # day, week, month
        
        # Validate parameters
        valid_periods = ['7d', '30d', '90d', '1y', 'all']
        if period not in valid_periods:
            period = '30d'
        
        valid_group_by = ['day', 'week', 'month']
        if group_by not in valid_group_by:
            group_by = 'day'
        
        # Get statistics from database
        prediction_log_db = get_prediction_log_db()
        result = prediction_log_db.get_user_prediction_statistics(user_id, period, group_by)
        
        if not result:
            result = {
                'statistics': {
                    'totalPredictions': 0,
                    'successfulPredictions': 0,
                    'failedPredictions': 0,
                    'successRate': 0,
                    'avgConfidence': 0,
                    'avgProcessingTime': 0,
                    'firstPrediction': None,
                    'lastPrediction': None
                },
                'timeline': [],
                'cropDistribution': []
            }
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Retrieved prediction statistics for user {user_id} (processing time: {processing_time}ms)")
        
        return create_success_response(result)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"Error getting user prediction statistics: {e}", exc_info=True)
        return create_error_response("Internal server error", status_code=500)

@prediction_logs_bp.route('/api/users/<user_id>/prediction-logs/export', methods=['GET'])
@require_auth
def export_user_prediction_logs(user_id):
    """Export prediction logs to CSV."""
    start_time = time.time()
    
    try:
        # Validate user authorization - users can only export their own logs
        current_user = request.current_user
        if current_user['id'] != user_id:
            return create_error_response("Unauthorized to export other users' logs", status_code=403)
        
        # Parse query parameters (same as get_user_prediction_logs)
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        crop = request.args.get('crop')
        status = request.args.get('status')
        order_by = request.args.get('orderBy', 'timestamp')
        order_direction = request.args.get('orderDirection', 'desc')
        
        # Validate and build filters
        filters = {}
        if date_from:
            try:
                filters['date_from'] = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except ValueError:
                return create_error_response("Invalid dateFrom format. Use YYYY-MM-DD", status_code=400)
        
        if date_to:
            try:
                filters['date_to'] = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except ValueError:
                return create_error_response("Invalid dateTo format. Use YYYY-MM-DD", status_code=400)
        
        if crop:
            filters['crop'] = crop
        
        if status and status in ['success', 'error']:
            filters['status'] = status
        
        # Validate order parameters
        valid_order_fields = ['timestamp', 'confidence', 'predicted_crop', 'processing_time']
        if order_by not in valid_order_fields:
            order_by = 'timestamp'
        
        if order_direction.lower() not in ['asc', 'desc']:
            order_direction = 'desc'
        
        filters['order_by'] = order_by
        filters['order_direction'] = order_direction
        
        # Export to CSV
        prediction_log_db = get_prediction_log_db()
        csv_content = prediction_log_db.export_user_prediction_logs_csv(user_id, filters)
        
        if not csv_content:
            return create_error_response("No data to export", status_code=404)
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"prediction_logs_{user_id}_{timestamp}.csv"
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Exported prediction logs for user {user_id} (processing time: {processing_time}ms)")
        
        # Return CSV file
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"Error exporting user prediction logs: {e}", exc_info=True)
        return create_error_response("Internal server error", status_code=500)