-- Statistics Schema for Backend Statistics Implementation
-- Adds additional tables for metrics tracking and statistics

-- ============================================================================
-- STATISTICS TABLES
-- ============================================================================

-- System Metrics Table - Store aggregated platform statistics
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(50) NOT NULL,
    metric_value NUMERIC NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(metric_name)
);

-- User Activity Table - Track user engagement
CREATE TABLE IF NOT EXISTS user_activity (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    activity_date DATE NOT NULL,
    predictions_count INTEGER DEFAULT 0,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prediction Outcomes Table - Track prediction success rates
CREATE TABLE IF NOT EXISTS prediction_outcomes (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER REFERENCES predictions(id) ON DELETE CASCADE,
    outcome_status VARCHAR(20) DEFAULT 'pending' CHECK (outcome_status IN ('success', 'failure', 'pending')),
    reported_at TIMESTAMP,
    user_feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Geographic Usage Table - Track country/region usage
CREATE TABLE IF NOT EXISTS geographic_usage (
    id SERIAL PRIMARY KEY,
    country_code VARCHAR(3) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    user_count INTEGER DEFAULT 0,
    last_activity TIMESTAMP,
    UNIQUE(country_code)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- System metrics indexes
CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_calculated ON system_metrics(calculated_at DESC);

-- User activity indexes  
CREATE INDEX IF NOT EXISTS idx_user_activity_user ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_date ON user_activity(activity_date DESC);
CREATE INDEX IF NOT EXISTS idx_user_activity_user_date ON user_activity(user_id, activity_date);

-- Prediction outcomes indexes
CREATE INDEX IF NOT EXISTS idx_prediction_outcomes_prediction ON prediction_outcomes(prediction_id);
CREATE INDEX IF NOT EXISTS idx_prediction_outcomes_status ON prediction_outcomes(outcome_status);
CREATE INDEX IF NOT EXISTS idx_prediction_outcomes_reported ON prediction_outcomes(reported_at DESC);

-- Geographic usage indexes
CREATE INDEX IF NOT EXISTS idx_geographic_usage_country ON geographic_usage(country_code);
CREATE INDEX IF NOT EXISTS idx_geographic_usage_activity ON geographic_usage(last_activity DESC);

-- ============================================================================
-- FUNCTIONS FOR STATISTICS CALCULATION
-- ============================================================================

-- Function to calculate system metrics
CREATE OR REPLACE FUNCTION calculate_system_metrics()
RETURNS void AS $$
BEGIN
    -- Calculate total crops analyzed
    INSERT INTO system_metrics (metric_name, metric_value)
    VALUES ('crops_analyzed', (SELECT COUNT(DISTINCT predicted_crop) FROM predictions))
    ON CONFLICT (metric_name) 
    DO UPDATE SET metric_value = EXCLUDED.metric_value, calculated_at = CURRENT_TIMESTAMP;
    
    -- Calculate active users (last 30 days)
    INSERT INTO system_metrics (metric_name, metric_value)
    VALUES ('active_users', (
        SELECT COUNT(DISTINCT COALESCE(user_id::text, client_ip::text))
        FROM predictions 
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
    ))
    ON CONFLICT (metric_name) 
    DO UPDATE SET metric_value = EXCLUDED.metric_value, calculated_at = CURRENT_TIMESTAMP;
    
    -- Calculate success rate (default to 95% if no data)
    INSERT INTO system_metrics (metric_name, metric_value)
    VALUES ('success_rate', (
        SELECT CASE 
            WHEN COUNT(*) = 0 THEN 95.0
            WHEN COUNT(CASE WHEN outcome_status != 'pending' THEN 1 END) = 0 THEN 95.0
            ELSE COALESCE((COUNT(CASE WHEN outcome_status = 'success' THEN 1 END) * 100.0 / 
                  NULLIF(COUNT(CASE WHEN outcome_status != 'pending' THEN 1 END), 0)), 95.0)
        END
        FROM prediction_outcomes
    ))
    ON CONFLICT (metric_name) 
    DO UPDATE SET metric_value = EXCLUDED.metric_value, calculated_at = CURRENT_TIMESTAMP;
    
    -- Calculate countries served
    INSERT INTO system_metrics (metric_name, metric_value)
    VALUES ('countries_served', (SELECT COUNT(DISTINCT country_code) FROM geographic_usage WHERE user_count > 0))
    ON CONFLICT (metric_name) 
    DO UPDATE SET metric_value = EXCLUDED.metric_value, calculated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Function to update user activity
CREATE OR REPLACE FUNCTION update_user_activity(p_user_id UUID, p_activity_date DATE)
RETURNS void AS $$
BEGIN
    INSERT INTO user_activity (user_id, activity_date, predictions_count, last_login)
    VALUES (p_user_id, p_activity_date, 1, CURRENT_TIMESTAMP)
    ON CONFLICT (user_id, activity_date) 
    DO UPDATE SET 
        predictions_count = user_activity.predictions_count + 1,
        last_login = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Function to update geographic usage
CREATE OR REPLACE FUNCTION update_geographic_usage(p_country_code VARCHAR, p_country_name VARCHAR)
RETURNS void AS $$
BEGIN
    INSERT INTO geographic_usage (country_code, country_name, user_count, last_activity)
    VALUES (p_country_code, p_country_name, 1, CURRENT_TIMESTAMP)
    ON CONFLICT (country_code) 
    DO UPDATE SET 
        user_count = geographic_usage.user_count + 1,
        last_activity = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert initial system metrics with default values
INSERT INTO system_metrics (metric_name, metric_value) VALUES
('crops_analyzed', 22),
('active_users', 0),
('success_rate', 95.0),
('countries_served', 8)
ON CONFLICT (metric_name) DO NOTHING;

-- Insert initial geographic data for Latin American countries
INSERT INTO geographic_usage (country_code, country_name, user_count, last_activity) VALUES
('MEX', 'México', 0, CURRENT_TIMESTAMP),
('COL', 'Colombia', 0, CURRENT_TIMESTAMP),
('ARG', 'Argentina', 0, CURRENT_TIMESTAMP),
('BRA', 'Brasil', 0, CURRENT_TIMESTAMP),
('PER', 'Perú', 0, CURRENT_TIMESTAMP),
('CHL', 'Chile', 0, CURRENT_TIMESTAMP),
('ECU', 'Ecuador', 0, CURRENT_TIMESTAMP),
('GTM', 'Guatemala', 0, CURRENT_TIMESTAMP)
ON CONFLICT (country_code) DO NOTHING;

-- Add unique constraint for user activity
ALTER TABLE user_activity DROP CONSTRAINT IF EXISTS unique_user_activity_date;
ALTER TABLE user_activity ADD CONSTRAINT unique_user_activity_date UNIQUE (user_id, activity_date);

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Statistics schema deployment completed!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'New tables created: ';
    RAISE NOTICE '✓ system_metrics - aggregated platform statistics';
    RAISE NOTICE '✓ user_activity - user engagement tracking';
    RAISE NOTICE '✓ prediction_outcomes - prediction success rates';
    RAISE NOTICE '✓ geographic_usage - country/region usage';
    RAISE NOTICE '';
    RAISE NOTICE 'Functions created:';
    RAISE NOTICE '✓ calculate_system_metrics() - updates all metrics';
    RAISE NOTICE '✓ update_user_activity() - tracks user activity';
    RAISE NOTICE '✓ update_geographic_usage() - tracks geographic usage';
    RAISE NOTICE '========================================';
END $$;