-- Prediction logs and statistics tables
-- Run after statistics_schema.sql

-- Prediction Logs Table
CREATE TABLE IF NOT EXISTS prediction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    input_features JSONB NOT NULL,
    predicted_crop VARCHAR(255) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    top_predictions JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'success' CHECK (status IN ('success', 'error')),
    processing_time INTEGER NULL, -- Processing time in milliseconds
    error_message TEXT NULL,
    session_id VARCHAR(255) NULL,
    ip_address INET NULL,
    user_agent TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for prediction_logs
CREATE INDEX IF NOT EXISTS idx_prediction_logs_user_id ON prediction_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_prediction_logs_timestamp ON prediction_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_prediction_logs_status ON prediction_logs(status);
CREATE INDEX IF NOT EXISTS idx_prediction_logs_predicted_crop ON prediction_logs(predicted_crop);
CREATE INDEX IF NOT EXISTS idx_prediction_logs_user_timestamp ON prediction_logs(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_prediction_logs_crop_confidence ON prediction_logs(predicted_crop, confidence DESC);
CREATE INDEX IF NOT EXISTS idx_prediction_logs_status_timestamp ON prediction_logs(status, timestamp DESC);

-- Prediction Statistics Table (for aggregated metrics)
CREATE TABLE IF NOT EXISTS prediction_statistics (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_predictions INTEGER DEFAULT 0,
    successful_predictions INTEGER DEFAULT 0,
    failed_predictions INTEGER DEFAULT 0,
    most_predicted_crop VARCHAR(255) NULL,
    avg_confidence DECIMAL(5,4) NULL,
    avg_processing_time INTEGER NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_user_date UNIQUE (user_id, date)
);

-- Create indexes for prediction_statistics
CREATE INDEX IF NOT EXISTS idx_prediction_statistics_user_id ON prediction_statistics(user_id);
CREATE INDEX IF NOT EXISTS idx_prediction_statistics_date ON prediction_statistics(date);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_prediction_logs_updated_at BEFORE UPDATE ON prediction_logs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prediction_statistics_updated_at BEFORE UPDATE ON prediction_statistics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments
COMMENT ON TABLE prediction_logs IS 'Detailed logs of individual prediction requests';
COMMENT ON TABLE prediction_statistics IS 'Daily aggregated prediction statistics per user';
COMMENT ON COLUMN prediction_logs.input_features IS 'JSON object containing N, P, K, temperature, humidity, ph, rainfall';
COMMENT ON COLUMN prediction_logs.top_predictions IS 'JSON array of top predictions with crop and probability';
COMMENT ON COLUMN prediction_logs.processing_time IS 'Processing time in milliseconds';
COMMENT ON COLUMN prediction_logs.status IS 'success or error status of prediction';