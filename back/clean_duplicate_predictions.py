#!/usr/bin/env python3
"""
Script to clean duplicate prediction entries from the database.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
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

def clean_duplicates():
    """Remove duplicate prediction entries."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("Cleaning duplicate predictions...")
    print("=" * 40)
    
    # Find duplicates (same user, crop, and within 5 seconds)
    print("\n1. Finding duplicates...")
    cursor.execute("""
        WITH duplicates AS (
            SELECT 
                p1.id as keep_id,
                p2.id as delete_id,
                p1.user_id,
                p1.predicted_crop,
                p1.timestamp as time1,
                p2.timestamp as time2
            FROM prediction_logs p1
            JOIN prediction_logs p2 ON p1.user_id = p2.user_id 
                AND p1.predicted_crop = p2.predicted_crop
                AND p1.id < p2.id
            WHERE ABS(EXTRACT(EPOCH FROM (p2.timestamp - p1.timestamp))) < 5
        )
        SELECT 
            COUNT(*) as duplicate_count,
            COUNT(DISTINCT user_id) as affected_users
        FROM duplicates
    """)
    
    result = cursor.fetchone()
    print(f"Found {result['duplicate_count']} duplicates affecting {result['affected_users']} users")
    
    if result['duplicate_count'] == 0:
        print("No duplicates found!")
        cursor.close()
        conn.close()
        return
    
    # Show examples of duplicates
    print("\n2. Examples of duplicates to be removed:")
    cursor.execute("""
        WITH duplicates AS (
            SELECT 
                p1.id as keep_id,
                p2.id as delete_id,
                p1.user_id,
                p1.predicted_crop,
                p1.timestamp as time1,
                p2.timestamp as time2,
                ABS(EXTRACT(EPOCH FROM (p2.timestamp - p1.timestamp))) as seconds_diff
            FROM prediction_logs p1
            JOIN prediction_logs p2 ON p1.user_id = p2.user_id 
                AND p1.predicted_crop = p2.predicted_crop
                AND p1.id < p2.id
            WHERE ABS(EXTRACT(EPOCH FROM (p2.timestamp - p1.timestamp))) < 5
        )
        SELECT * FROM duplicates
        ORDER BY time1 DESC
        LIMIT 10
    """)
    
    examples = cursor.fetchall()
    for ex in examples:
        print(f"  User: {ex['user_id'][:8]}..., Crop: {ex['predicted_crop']}, "
              f"IDs: {ex['keep_id']} (keep) / {ex['delete_id']} (delete), "
              f"Diff: {ex['seconds_diff']:.2f}s")
    
    # Ask for confirmation
    response = input("\nDo you want to remove these duplicates? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        cursor.close()
        conn.close()
        return
    
    # Remove duplicates
    print("\n3. Removing duplicates...")
    cursor.execute("""
        WITH duplicates AS (
            SELECT 
                p2.id as delete_id
            FROM prediction_logs p1
            JOIN prediction_logs p2 ON p1.user_id = p2.user_id 
                AND p1.predicted_crop = p2.predicted_crop
                AND p1.id < p2.id
            WHERE ABS(EXTRACT(EPOCH FROM (p2.timestamp - p1.timestamp))) < 5
        )
        DELETE FROM prediction_logs
        WHERE id IN (SELECT delete_id FROM duplicates)
    """)
    
    deleted_count = cursor.rowcount
    print(f"Deleted {deleted_count} duplicate entries")
    
    # Commit changes
    conn.commit()
    print("Changes committed successfully!")
    
    # Verify cleanup
    print("\n4. Verifying cleanup...")
    cursor.execute("""
        WITH duplicates AS (
            SELECT 
                p1.id as id1,
                p2.id as id2
            FROM prediction_logs p1
            JOIN prediction_logs p2 ON p1.user_id = p2.user_id 
                AND p1.predicted_crop = p2.predicted_crop
                AND p1.id < p2.id
            WHERE ABS(EXTRACT(EPOCH FROM (p2.timestamp - p1.timestamp))) < 5
        )
        SELECT COUNT(*) as remaining_duplicates
        FROM duplicates
    """)
    
    remaining = cursor.fetchone()
    print(f"Remaining duplicates: {remaining['remaining_duplicates']}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    clean_duplicates()