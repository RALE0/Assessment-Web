#!/usr/bin/env python3
"""
Database initialization script for AgriAI Analytics API
This script creates all necessary tables and inserts sample data for the new endpoints.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, timedelta
import random
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': '172.28.69.148',
    'port': 5432,
    'user': 'cropapi',
    'password': 'cropapi123',
    'database': 'crop_recommendations'
}

def get_db_connection():
    """Get database connection."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def run_sql_file(conn, file_path):
    """Run SQL commands from a file."""
    try:
        with open(file_path, 'r') as file:
            sql_content = file.read()
        
        cursor = conn.cursor()
        cursor.execute(sql_content)
        conn.commit()
        cursor.close()
        logger.info(f"Successfully executed SQL file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error running SQL file {file_path}: {e}")
        return False

def create_sample_model_performance_data(conn):
    """Create sample model performance data."""
    cursor = conn.cursor()
    
    # Sample model performance metrics
    metrics = ['accuracy', 'recall', 'f1_score', 'specificity']
    model_types = ['DropClassifier', 'DeepDropoutClassifier', 'Conv1DClassifier']
    
    for i in range(6):  # Last 6 months
        date = datetime.now() - timedelta(days=30 * i)
        
        for model_type in model_types:
            for metric in metrics:
                base_values = {
                    'accuracy': 0.94 + random.uniform(0, 0.05),
                    'recall': 0.90 + random.uniform(0, 0.06),
                    'f1_score': 0.92 + random.uniform(0, 0.05),
                    'specificity': 0.93 + random.uniform(0, 0.04)
                }
                
                value = base_values[metric] + (i * 0.005)  # Slight improvement over time
                target_value = base_values[metric]
                
                if value >= target_value * 1.02:
                    status = 'excellent'
                elif value >= target_value * 0.98:
                    status = 'good'
                elif value >= target_value * 0.95:
                    status = 'warning'
                else:
                    status = 'poor'
                
                cursor.execute("""
                    INSERT INTO model_performance 
                    (model_version, model_type, metric_name, value, target_value, status, evaluated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    f"v2.{i}", model_type, metric, value, target_value, status, date
                ))
    
    conn.commit()
    cursor.close()
    logger.info("Created sample model performance data")

def create_sample_user_satisfaction_data(conn):
    """Create sample user satisfaction data."""
    cursor = conn.cursor()
    
    # Create sample satisfaction ratings
    for i in range(100):  # 100 sample ratings
        date = datetime.now() - timedelta(days=random.randint(1, 30))
        rating = random.choices([4, 5, 3, 2, 1], weights=[40, 50, 8, 1, 1])[0]
        
        feedbacks = {
            5: ["Excelente predicción, muy precisa", "Muy útil para mi cultivo", "Perfecto resultado"],
            4: ["Buena recomendación", "Útil para la toma de decisiones", "Satisfecho con el resultado"],
            3: ["Funciona bien", "Resultado aceptable", "Regular"],
            2: ["Podría mejorar", "No muy preciso", "Esperaba mejor resultado"],
            1: ["No funcionó bien", "Resultado incorrecto", "Decepcionante"]
        }
        
        feedback = random.choice(feedbacks[rating])
        
        cursor.execute("""
            INSERT INTO user_satisfaction (rating, feedback, created_at)
            VALUES (%s, %s, %s)
        """, (rating, feedback, date))
    
    conn.commit()
    cursor.close()
    logger.info("Created sample user satisfaction data")

def create_sample_prediction_analytics_data(conn):
    """Create sample prediction analytics data."""
    cursor = conn.cursor()
    
    regions = ['Centro México', 'Sur México', 'Norte México', 'Colombia', 'Otros']
    states = ['Jalisco', 'Michoacán', 'Sinaloa', 'Veracruz', 'Chiapas']
    cities = ['Guadalajara', 'Morelia', 'Culiacán', 'Xalapa', 'Tuxtla Gutiérrez']
    
    # Get existing prediction IDs
    cursor.execute("SELECT id FROM predictions ORDER BY created_at DESC LIMIT 50")
    prediction_ids = [row[0] for row in cursor.fetchall()]
    
    for pred_id in prediction_ids:
        region = random.choice(regions)
        state = random.choice(states)
        city = random.choice(cities)
        model_type = random.choice(['DropClassifier', 'DeepDropoutClassifier', 'Conv1DClassifier'])
        response_time = random.randint(800, 3000)  # ms
        confidence = random.uniform(0.7, 0.99)
        
        cursor.execute("""
            INSERT INTO prediction_analytics 
            (prediction_id, region, state, city, model_type, response_time_ms, confidence_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (pred_id, region, state, city, model_type, response_time, confidence))
    
    conn.commit()
    cursor.close()
    logger.info("Created sample prediction analytics data")

def main():
    """Main initialization function."""
    logger.info("Starting database initialization...")
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        # 1. Run the analytics schema SQL file
        logger.info("Creating analytics schema...")
        if not run_sql_file(conn, 'analytics_schema.sql'):
            logger.error("Failed to create analytics schema")
            return False
        
        # 2. Create sample data
        logger.info("Creating sample data...")
        create_sample_model_performance_data(conn)
        create_sample_user_satisfaction_data(conn)
        create_sample_prediction_analytics_data(conn)
        
        # 3. Update existing tables
        cursor = conn.cursor()
        
        # Add user_id column to predictions if it doesn't exist
        try:
            cursor.execute("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name = 'predictions' AND column_name = 'user_id') THEN
                        ALTER TABLE predictions ADD COLUMN user_id UUID REFERENCES users(id) ON DELETE SET NULL;
                        CREATE INDEX idx_predictions_user ON predictions(user_id);
                    END IF;
                END $$;
            """)
            conn.commit()
            logger.info("Updated predictions table with user_id column")
        except Exception as e:
            logger.warning(f"Could not update predictions table: {e}")
        
        cursor.close()
        
        logger.info("Database initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    if success:
        print("✅ Database initialization completed successfully!")
    else:
        print("❌ Database initialization failed!")
        exit(1)