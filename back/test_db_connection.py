#!/usr/bin/env python3
import psycopg2
import sys
from psycopg2.extras import RealDictCursor

def test_db_connection():
    """Test database connection with timeout"""
    try:
        # Connection parameters from working_command.sh
        conn = psycopg2.connect(
            host="172.28.69.148",
            database="crop_recommendations", 
            user="cropapi",
            password="cropapi123",
            connect_timeout=10  # 10 second timeout
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test query from working_command.sh
        cursor.execute("SELECT 'OK' as test;")
        result = cursor.fetchone()
        
        print(f"Database connection successful!")
        print(f"Test result: {result['test']}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_db_connection()
    sys.exit(0 if success else 1)