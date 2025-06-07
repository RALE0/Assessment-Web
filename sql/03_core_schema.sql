-- Core application tables
-- Run after auth_schema.sql

-- Crops Table (updated to include description column)
CREATE TABLE IF NOT EXISTS crops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    scientific_name VARCHAR(200),
    description TEXT,
    optimal_n_min DECIMAL(5,2),
    optimal_n_max DECIMAL(5,2),
    optimal_p_min DECIMAL(5,2),
    optimal_p_max DECIMAL(5,2),
    optimal_k_min DECIMAL(5,2),
    optimal_k_max DECIMAL(5,2),
    optimal_temp_min DECIMAL(5,2),
    optimal_temp_max DECIMAL(5,2),
    optimal_humidity_min DECIMAL(5,2),
    optimal_humidity_max DECIMAL(5,2),
    optimal_ph_min DECIMAL(3,2),
    optimal_ph_max DECIMAL(3,2),
    optimal_rainfall_min DECIMAL(7,2),
    optimal_rainfall_max DECIMAL(7,2),
    growing_season VARCHAR(100),
    harvest_time VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add description column if it doesn't exist (for existing tables)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'crops' AND column_name = 'description'
    ) THEN
        ALTER TABLE crops ADD COLUMN description TEXT;
    END IF;
END $$;

-- Predictions Table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    nitrogen DECIMAL(6,2) NOT NULL,
    phosphorus DECIMAL(6,2) NOT NULL,
    potassium DECIMAL(6,2) NOT NULL,
    temperature DECIMAL(5,2) NOT NULL,
    humidity DECIMAL(5,2) NOT NULL,
    ph DECIMAL(4,2) NOT NULL,
    rainfall DECIMAL(7,2) NOT NULL,
    predicted_crop VARCHAR(100) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    alternatives TEXT,
    client_ip INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50) DEFAULT '1.0'
);

-- API Requests Table (for logging and analytics)
CREATE TABLE IF NOT EXISTS api_requests (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    client_ip INET,
    user_agent TEXT,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);