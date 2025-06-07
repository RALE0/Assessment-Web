#!/usr/bin/env python3
"""
Diagnostic script to check for duplicate prediction entries.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import os

def get_db_connection():
    """Get database connection."""
    db_config = {
        'host': os.getenv('DB_HOST', '172.28.69.148'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'crop_recommendations'),
        'user': os.getenv('DB_USER', 'cropapi'),
        'password': os.getenv('DB_PASSWORD', 'cropapi123')
    }
    return psycopg2.connect(**db_config)

def diagnose_duplicates(user_id):
    """Diagnose duplicate prediction entries for a user."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\nDiagnosing predictions for user: {user_id}")
    print("=" * 60)
    
    # Check prediction_logs table
    print("\n1. Checking prediction_logs table:")
    cursor.execute("""
        SELECT 
            id,
            user_id,
            predicted_crop,
            confidence,
            timestamp,
            status,
            session_id,
            processing_time
        FROM prediction_logs
        WHERE user_id = %s
        ORDER BY timestamp DESC
        LIMIT 10
    """, (user_id,))
    
    prediction_logs = cursor.fetchall()
    print(f"Found {len(prediction_logs)} recent entries in prediction_logs")
    
    for log in prediction_logs:
        print(f"  ID: {log['id']}, Crop: {log['predicted_crop']}, "
              f"Time: {log['timestamp']}, Session: {log['session_id']}")
    
    # Check for potential duplicates (same crop within 1 second)
    print("\n2. Checking for duplicates (same crop within 5 seconds):")
    cursor.execute("""
        SELECT 
            p1.id as id1,
            p2.id as id2,
            p1.predicted_crop,
            p1.timestamp as time1,
            p2.timestamp as time2,
            ABS(EXTRACT(EPOCH FROM (p2.timestamp - p1.timestamp))) as seconds_diff
        FROM prediction_logs p1
        JOIN prediction_logs p2 ON p1.user_id = p2.user_id 
            AND p1.predicted_crop = p2.predicted_crop
            AND p1.id < p2.id
        WHERE p1.user_id = %s
            AND ABS(EXTRACT(EPOCH FROM (p2.timestamp - p1.timestamp))) < 5
        ORDER BY p1.timestamp DESC
        LIMIT 10
    """, (user_id,))
    
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"Found {len(duplicates)} potential duplicate pairs:")
        for dup in duplicates:
            print(f"  IDs: {dup['id1']} & {dup['id2']}, Crop: {dup['predicted_crop']}, "
                  f"Diff: {dup['seconds_diff']:.2f}s")
    else:
        print("No duplicates found")
    
    # Check predictions table (if exists)
    print("\n3. Checking predictions table (if exists):")
    try:
        cursor.execute("""
            SELECT 
                id,
                user_id,
                predicted_crop,
                confidence,
                created_at
            FROM predictions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id,))
        
        predictions = cursor.fetchall()
        print(f"Found {len(predictions)} recent entries in predictions table")
        
        for pred in predictions:
            print(f"  ID: {pred['id']}, Crop: {pred['predicted_crop']}, "
                  f"Time: {pred['created_at']}")
    except psycopg2.errors.UndefinedColumn:
        print("predictions table doesn't have user_id column")
    except psycopg2.errors.UndefinedTable:
        print("predictions table doesn't exist")
    
    # Count predictions by status
    print("\n4. Predictions by status:")
    cursor.execute("""
        SELECT 
            status,
            COUNT(*) as count
        FROM prediction_logs
        WHERE user_id = %s
        GROUP BY status
    """, (user_id,))
    
    status_counts = cursor.fetchall()
    for status in status_counts:
        print(f"  {status['status']}: {status['count']}")
    
    # Check monthly prediction count
    print("\n5. Monthly prediction count:")
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM prediction_logs
        WHERE user_id = %s
          AND timestamp >= DATE_TRUNC('month', CURRENT_DATE)
          AND status = 'success'
    """, (user_id,))
    
    monthly_count = cursor.fetchone()
    print(f"  This month: {monthly_count['count']} successful predictions")
    
    # Check crop distribution
    print("\n6. Crop distribution (last 30 days):")
    cursor.execute("""
        SELECT 
            predicted_crop,
            COUNT(*) as count
        FROM prediction_logs
        WHERE user_id = %s
          AND timestamp >= CURRENT_DATE - INTERVAL '30 days'
          AND status = 'success'
          AND predicted_crop IS NOT NULL
        GROUP BY predicted_crop
        ORDER BY count DESC
        LIMIT 5
    """, (user_id,))
    
    crop_dist = cursor.fetchall()
    for crop in crop_dist:
        print(f"  {crop['predicted_crop']}: {crop['count']}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        # Default test user
        user_id = "567ab65a-486e-486d-89de-c06aa6fee544"  # ian's user ID
    
    diagnose_duplicates(user_id)