-- Analytics schema modifications for backend analytics requirements
-- Run after prediction_logs_schema.sql

-- Add missing columns to prediction_logs table
ALTER TABLE prediction_logs ADD COLUMN IF NOT EXISTS user_region VARCHAR(100);
ALTER TABLE prediction_logs ADD COLUMN IF NOT EXISTS actual_crop VARCHAR(100);
ALTER TABLE prediction_logs ADD COLUMN IF NOT EXISTS feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5);

-- User Reviews Table
CREATE TABLE IF NOT EXISTS user_reviews (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    prediction_id UUID REFERENCES prediction_logs(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Metrics Table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calculation_period VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Regional Data Table
CREATE TABLE IF NOT EXISTS regional_data (
    id SERIAL PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL,
    country VARCHAR(100),
    user_count INTEGER DEFAULT 0,
    prediction_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Harvest Outcomes Table
CREATE TABLE IF NOT EXISTS harvest_outcomes (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    prediction_id UUID REFERENCES prediction_logs(id),
    predicted_crop VARCHAR(100),
    actual_crop VARCHAR(100),
    harvest_date DATE,
    yield_quantity DECIMAL(10,2),
    roi_percentage DECIMAL(5,2),
    success_rating INTEGER CHECK (success_rating >= 1 AND success_rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_prediction_logs_user_region ON prediction_logs(user_region);
CREATE INDEX IF NOT EXISTS idx_prediction_logs_actual_crop ON prediction_logs(actual_crop);
CREATE INDEX IF NOT EXISTS idx_prediction_logs_feedback_score ON prediction_logs(feedback_score);

CREATE INDEX IF NOT EXISTS idx_user_reviews_user_id ON user_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_user_reviews_created_at ON user_reviews(created_at);
CREATE INDEX IF NOT EXISTS idx_user_reviews_rating ON user_reviews(rating);
CREATE INDEX IF NOT EXISTS idx_user_reviews_prediction_id ON user_reviews(prediction_id);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_recorded_at ON performance_metrics(recorded_at);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_period ON performance_metrics(calculation_period);

CREATE INDEX IF NOT EXISTS idx_regional_data_region ON regional_data(region_name);
CREATE INDEX IF NOT EXISTS idx_regional_data_country ON regional_data(country);

CREATE INDEX IF NOT EXISTS idx_harvest_outcomes_user_id ON harvest_outcomes(user_id);
CREATE INDEX IF NOT EXISTS idx_harvest_outcomes_prediction_id ON harvest_outcomes(prediction_id);
CREATE INDEX IF NOT EXISTS idx_harvest_outcomes_harvest_date ON harvest_outcomes(harvest_date);
CREATE INDEX IF NOT EXISTS idx_harvest_outcomes_actual_crop ON harvest_outcomes(actual_crop);

-- Add triggers for updated_at timestamps
CREATE TRIGGER update_user_reviews_updated_at BEFORE UPDATE ON user_reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_harvest_outcomes_updated_at BEFORE UPDATE ON harvest_outcomes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default regional data
INSERT INTO regional_data (region_name, country, user_count, prediction_count) VALUES
('Centro México', 'México', 0, 0),
('Sur México', 'México', 0, 0),
('Norte México', 'México', 0, 0),
('Colombia', 'Colombia', 0, 0),
('Otros', 'Otros', 0, 0)
ON CONFLICT DO NOTHING;

-- Add comments
COMMENT ON TABLE user_reviews IS 'User reviews and ratings for predictions';
COMMENT ON TABLE performance_metrics IS 'System performance metrics and calculations';
COMMENT ON TABLE regional_data IS 'Regional distribution data for analytics';
COMMENT ON TABLE harvest_outcomes IS 'Actual harvest outcomes compared to predictions';

COMMENT ON COLUMN prediction_logs.user_region IS 'Geographic region of the user';
COMMENT ON COLUMN prediction_logs.actual_crop IS 'Actual crop grown (for accuracy calculation)';
COMMENT ON COLUMN prediction_logs.feedback_score IS 'User feedback score for the prediction';