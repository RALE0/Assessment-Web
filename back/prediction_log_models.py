"""
Prediction log models and database operations for the crop recommendation API.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
import json
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Any, Union
import logging
import csv
import io

logger = logging.getLogger(__name__)

class PredictionLogDatabase:
    """Database operations for prediction logging system."""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
    
    def get_connection(self):
        """Get database connection with timeout."""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.OperationalError as e:
            logger.error(f"Database connection timeout/error: {e}")
            return None
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected database connection error: {e}")
            return None
    
    def _safe_fetchone(self, cursor, field_name: str = None):
        """Safely fetch one result from cursor, handling both regular and RealDictCursor."""
        try:
            result = cursor.fetchone()
            if result is None:
                return None
            
            # If field_name is provided and result is dict-like, return the field
            if field_name and hasattr(result, '__getitem__') and hasattr(result, 'keys'):
                return result.get(field_name)
            
            # If no field_name and result is dict-like, return the whole dict
            if hasattr(result, '__getitem__') and hasattr(result, 'keys'):
                return result
            
            # For regular cursor results (tuples), return as-is
            return result
        except Exception as e:
            logger.error(f"Error fetching cursor result: {e}")
            return None
    
    def _safe_fetchall(self, cursor):
        """Safely fetch all results from cursor."""
        try:
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching cursor results: {e}")
            return []
    
    def save_prediction_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """Save prediction log to database with duplicate prevention."""
        try:
            # Validate required fields
            required_fields = ['user_id', 'input_features']
            for field in required_fields:
                if field not in log_data:
                    logger.error(f"Missing required field in log_data: {field}")
                    return None
            
            # Validate user_id format (should be UUID)
            user_id = log_data['user_id']
            if not isinstance(user_id, str) or len(user_id) != 36:
                logger.error(f"Invalid user_id format: {user_id}")
                return None
            
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            # Check for recent duplicate (same user, same crop within 3 seconds)
            predicted_crop = log_data.get('predicted_crop')
            if predicted_crop:
                cursor.execute("""
                    SELECT id FROM prediction_logs 
                    WHERE user_id = %s 
                      AND predicted_crop = %s 
                      AND timestamp > NOW() - INTERVAL '3 seconds'
                    LIMIT 1
                """, (user_id, predicted_crop))
                
                existing = cursor.fetchone()
                if existing:
                    logger.warning(f"Duplicate prediction detected for user {user_id[:8]}... crop {predicted_crop}, skipping")
                    cursor.close()
                    conn.close()
                    return existing[0]  # Return existing ID
            
            cursor = conn.cursor()
            
            log_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO prediction_logs (
                    id, user_id, input_features, predicted_crop, confidence, 
                    top_predictions, status, processing_time, error_message, 
                    session_id, ip_address, user_agent
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                log_id,
                log_data['user_id'],
                psycopg2.extras.Json(log_data['input_features']),
                log_data.get('predicted_crop'),
                log_data.get('confidence'),
                psycopg2.extras.Json(log_data.get('top_predictions', [])),
                log_data.get('status', 'success'),
                log_data.get('processing_time'),
                log_data.get('error_message'),
                log_data.get('session_id'),
                log_data.get('ip_address'),
                log_data.get('user_agent')
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Update daily statistics asynchronously
            try:
                self.update_daily_statistics(log_data['user_id'], datetime.now().date())
            except Exception as e:
                logger.warning(f"Failed to update daily statistics: {e}")
            
            logger.info(f"Prediction log saved with ID: {log_id}")
            return log_id
            
        except Exception as e:
            logger.error(f"Error saving prediction log: {e}")
            return None
    
    def get_user_prediction_logs(self, user_id: str, filters: Optional[Dict[str, Any]] = None, 
                               pagination: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get prediction logs for a user with filtering and pagination."""
        try:
            conn = self.get_connection()
            if not conn:
                return {'logs': [], 'pagination': {}, 'filters': {}}
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build WHERE clause
            where_conditions = ["user_id = %s"]
            params = [user_id]
            
            if filters:
                if filters.get('date_from'):
                    where_conditions.append("timestamp >= %s")
                    params.append(filters['date_from'])
                
                if filters.get('date_to'):
                    where_conditions.append("timestamp <= %s")
                    params.append(filters['date_to'])
                
                if filters.get('crop'):
                    where_conditions.append("predicted_crop ILIKE %s")
                    params.append(f"%{filters['crop']}%")
                
                if filters.get('status'):
                    where_conditions.append("status = %s")
                    params.append(filters['status'])
            
            where_clause = " AND ".join(where_conditions)
            
            # Build ORDER BY clause
            order_by = filters.get('order_by', 'timestamp') if filters else 'timestamp'
            order_direction = filters.get('order_direction', 'desc') if filters else 'desc'
            
            # Validate order_by to prevent SQL injection
            valid_order_fields = ['timestamp', 'confidence', 'predicted_crop', 'processing_time']
            if order_by not in valid_order_fields:
                order_by = 'timestamp'
            
            order_clause = f"ORDER BY {order_by} {order_direction.upper()}"
            
            # Count total records
            count_query = f"SELECT COUNT(*) as count FROM prediction_logs WHERE {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()['count']
            
            # If no records found, return early without error
            if total_count == 0:
                cursor.close()
                conn.close()
                return {
                    'logs': [],
                    'pagination': {'total': 0, 'limit': 50, 'offset': 0, 'hasMore': False},
                    'filters': filters or {}
                }
            
            # Apply pagination
            limit = 50  # default
            offset = 0  # default
            
            if pagination:
                limit = min(pagination.get('limit', 50), 100)  # max 100
                offset = pagination.get('offset', 0)
            
            # Main query
            query = f"""
                SELECT id, user_id, timestamp, input_features, predicted_crop, 
                       confidence, top_predictions, status, processing_time
                FROM prediction_logs 
                WHERE {where_clause}
                {order_clause}
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, params + [limit, offset])
            logs = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Format logs for response
            formatted_logs = []
            for log in logs:
                formatted_log = {
                    'id': str(log['id']),
                    'userId': str(log['user_id']),
                    'timestamp': log['timestamp'].isoformat() if log['timestamp'] else None,
                    'inputFeatures': log['input_features'],
                    'predictedCrop': log['predicted_crop'],
                    'confidence': float(log['confidence']) if log['confidence'] else None,
                    'topPredictions': log['top_predictions'],
                    'status': log['status'],
                    'processingTime': log['processing_time']
                }
                formatted_logs.append(formatted_log)
            
            # Build pagination info
            has_more = (offset + limit) < total_count
            pagination_info = {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'hasMore': has_more
            }
            
            return {
                'logs': formatted_logs,
                'pagination': pagination_info,
                'filters': filters or {}
            }
            
        except Exception as e:
            logger.error(f"Error getting user prediction logs for user {user_id}: {e}")
            return {'logs': [], 'pagination': {}, 'filters': {}}
    
    def get_user_prediction_statistics(self, user_id: str, period: str = '30d', 
                                     group_by: str = 'day') -> Dict[str, Any]:
        """Get prediction statistics for a user."""
        try:
            conn = self.get_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Calculate date range based on period
            end_date = datetime.now()
            if period == '7d':
                start_date = end_date - timedelta(days=7)
            elif period == '30d':
                start_date = end_date - timedelta(days=30)
            elif period == '90d':
                start_date = end_date - timedelta(days=90)
            elif period == '1y':
                start_date = end_date - timedelta(days=365)
            else:  # 'all'
                start_date = datetime(2020, 1, 1)  # Far past date
            
            # Overall statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_predictions,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_predictions,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed_predictions,
                    AVG(CASE WHEN status = 'success' THEN confidence END) as avg_confidence,
                    AVG(CASE WHEN processing_time IS NOT NULL THEN processing_time END) as avg_processing_time,
                    MIN(timestamp) as first_prediction,
                    MAX(timestamp) as last_prediction
                FROM prediction_logs 
                WHERE user_id = %s AND timestamp >= %s
            """, (user_id, start_date))
            
            stats = cursor.fetchone()
            
            if not stats or stats['total_predictions'] == 0:
                cursor.close()
                conn.close()
                return {
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
            
            # Most predicted crop
            cursor.execute("""
                SELECT predicted_crop, COUNT(*) as count
                FROM prediction_logs 
                WHERE user_id = %s AND timestamp >= %s AND status = 'success'
                GROUP BY predicted_crop
                ORDER BY count DESC
                LIMIT 1
            """, (user_id, start_date))
            
            most_predicted = cursor.fetchone()
            
            # Timeline data (grouped by day/week/month)
            if group_by == 'day':
                timeline_query = """
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as predictions,
                        AVG(CASE WHEN status = 'success' THEN confidence END) as avg_confidence
                    FROM prediction_logs 
                    WHERE user_id = %s AND timestamp >= %s
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                    LIMIT 30
                """
            elif group_by == 'week':
                timeline_query = """
                    SELECT 
                        DATE_TRUNC('week', timestamp) as date,
                        COUNT(*) as predictions,
                        AVG(CASE WHEN status = 'success' THEN confidence END) as avg_confidence
                    FROM prediction_logs 
                    WHERE user_id = %s AND timestamp >= %s
                    GROUP BY DATE_TRUNC('week', timestamp)
                    ORDER BY date DESC
                    LIMIT 12
                """
            else:  # month
                timeline_query = """
                    SELECT 
                        DATE_TRUNC('month', timestamp) as date,
                        COUNT(*) as predictions,
                        AVG(CASE WHEN status = 'success' THEN confidence END) as avg_confidence
                    FROM prediction_logs 
                    WHERE user_id = %s AND timestamp >= %s
                    GROUP BY DATE_TRUNC('month', timestamp)
                    ORDER BY date DESC
                    LIMIT 12
                """
            
            cursor.execute(timeline_query, (user_id, start_date))
            timeline = cursor.fetchall()
            
            # Crop distribution
            if stats['successful_predictions'] > 0:
                cursor.execute("""
                    SELECT 
                        predicted_crop as crop,
                        COUNT(*) as count,
                        ROUND(COUNT(*) * 100.0 / %s, 1) as percentage
                    FROM prediction_logs 
                    WHERE user_id = %s AND timestamp >= %s AND status = 'success'
                    GROUP BY predicted_crop
                    ORDER BY count DESC
                    LIMIT 10
                """, (stats['successful_predictions'], user_id, start_date))
                crop_distribution = cursor.fetchall()
            else:
                crop_distribution = []
            
            cursor.close()
            conn.close()
            
            # Format response
            success_rate = (stats['successful_predictions'] / stats['total_predictions'] * 100 
                          if stats['total_predictions'] > 0 else 0)
            
            response = {
                'statistics': {
                    'totalPredictions': stats['total_predictions'],
                    'successfulPredictions': stats['successful_predictions'],
                    'failedPredictions': stats['failed_predictions'],
                    'successRate': round(success_rate, 1),
                    'avgConfidence': round(float(stats['avg_confidence']), 3) if stats['avg_confidence'] else 0,
                    'avgProcessingTime': int(stats['avg_processing_time']) if stats['avg_processing_time'] else 0,
                    'mostPredictedCrop': most_predicted['predicted_crop'] if most_predicted else None,
                    'mostPredictedCropCount': most_predicted['count'] if most_predicted else 0,
                    'firstPrediction': stats['first_prediction'].isoformat() if stats['first_prediction'] else None,
                    'lastPrediction': stats['last_prediction'].isoformat() if stats['last_prediction'] else None
                },
                'timeline': [
                    {
                        'date': item['date'].strftime('%Y-%m-%d'),
                        'predictions': item['predictions'],
                        'avgConfidence': round(float(item['avg_confidence']), 3) if item['avg_confidence'] else 0
                    }
                    for item in timeline
                ],
                'cropDistribution': [
                    {
                        'crop': item['crop'],
                        'count': item['count'],
                        'percentage': float(item['percentage'])
                    }
                    for item in crop_distribution
                ]
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting user prediction statistics: {e}")
            return {}
    
    def export_user_prediction_logs_csv(self, user_id: str, filters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Export user prediction logs to CSV format."""
        try:
            # Get logs with no pagination limit for export
            export_filters = filters.copy() if filters else {}
            logs_data = self.get_user_prediction_logs(
                user_id, 
                filters=export_filters, 
                pagination={'limit': 5000, 'offset': 0}  # Max export limit
            )
            
            if not logs_data['logs']:
                return None
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'ID', 'Timestamp', 'Predicted Crop', 'Confidence', 'Status', 
                'Processing Time (ms)', 'Nitrogen', 'Phosphorus', 'Potassium', 
                'Temperature', 'Humidity', 'pH', 'Rainfall', 'Top Predictions'
            ])
            
            # Write data rows
            for log in logs_data['logs']:
                input_features = log.get('inputFeatures', {})
                top_predictions_str = json.dumps(log.get('topPredictions', []))
                
                writer.writerow([
                    log['id'],
                    log['timestamp'],
                    log['predictedCrop'],
                    log['confidence'],
                    log['status'],
                    log['processingTime'],
                    input_features.get('N'),
                    input_features.get('P'),
                    input_features.get('K'),
                    input_features.get('temperature'),
                    input_features.get('humidity'),
                    input_features.get('ph'),
                    input_features.get('rainfall'),
                    top_predictions_str
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            return csv_content
            
        except Exception as e:
            logger.error(f"Error exporting prediction logs to CSV: {e}")
            return None
    
    def update_daily_statistics(self, user_id: str, date_obj: date) -> bool:
        """Update daily statistics for a user."""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Calculate statistics for the day
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_predictions,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_predictions,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed_predictions,
                    AVG(CASE WHEN status = 'success' THEN confidence END) as avg_confidence,
                    AVG(processing_time) as avg_processing_time,
                    (SELECT predicted_crop 
                     FROM prediction_logs 
                     WHERE user_id = %s AND DATE(timestamp) = %s AND status = 'success'
                     GROUP BY predicted_crop 
                     ORDER BY COUNT(*) DESC 
                     LIMIT 1) as most_predicted_crop
                FROM prediction_logs 
                WHERE user_id = %s AND DATE(timestamp) = %s
            """, (user_id, date_obj, user_id, date_obj))
            
            stats = cursor.fetchone()
            
            if stats and stats['total_predictions'] > 0:  # total_predictions > 0
                # Upsert statistics
                cursor.execute("""
                    INSERT INTO prediction_statistics 
                    (user_id, date, total_predictions, successful_predictions, 
                     failed_predictions, most_predicted_crop, avg_confidence, avg_processing_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, date) 
                    DO UPDATE SET
                        total_predictions = EXCLUDED.total_predictions,
                        successful_predictions = EXCLUDED.successful_predictions,
                        failed_predictions = EXCLUDED.failed_predictions,
                        most_predicted_crop = EXCLUDED.most_predicted_crop,
                        avg_confidence = EXCLUDED.avg_confidence,
                        avg_processing_time = EXCLUDED.avg_processing_time,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    user_id, date_obj, stats['total_predictions'], stats['successful_predictions'], stats['failed_predictions'], 
                    stats['most_predicted_crop'], stats['avg_confidence'], int(stats['avg_processing_time']) if stats['avg_processing_time'] else None
                ))
                
                conn.commit()
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating daily statistics: {e}")
            return False