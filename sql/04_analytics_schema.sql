-- Analytics and dashboard tables
-- Run after core_schema.sql

-- Dashboard Metrics Table
-- Stores aggregated metrics for fast dashboard loading
CREATE TABLE IF NOT EXISTS dashboard_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    value NUMERIC NOT NULL,
    change_percentage NUMERIC,
    period VARCHAR(20) NOT NULL, -- 'daily', 'monthly', 'quarterly', 'yearly'
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT unique_metric_period UNIQUE(metric_type, metric_name, period, calculated_at)
);

-- Prediction Analytics Table
-- Enhanced prediction tracking with regional and performance data
CREATE TABLE IF NOT EXISTS prediction_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id INTEGER REFERENCES predictions(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    region VARCHAR(100),
    country VARCHAR(100) DEFAULT 'México',
    state VARCHAR(100),
    city VARCHAR(100),
    model_version VARCHAR(50),
    model_type VARCHAR(50), -- 'DropClassifier', 'DeepDropoutClassifier', etc.
    response_time_ms INTEGER,
    confidence_score NUMERIC(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Model Performance Table
-- Tracks model performance metrics over time
CREATE TABLE IF NOT EXISTS model_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(50) NOT NULL, -- 'accuracy', 'precision', 'recall', 'f1_score', 'specificity'
    value NUMERIC(5,4) NOT NULL,
    target_value NUMERIC(5,4),
    status VARCHAR(20), -- 'excellent', 'good', 'warning', 'poor'
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    test_size INTEGER,
    metadata JSONB DEFAULT '{}'
);

-- Monthly Predictions Summary
-- Pre-aggregated monthly data for charts
CREATE TABLE IF NOT EXISTS monthly_predictions_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    month DATE NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    predictions_count INTEGER NOT NULL,
    unique_users_count INTEGER,
    avg_confidence NUMERIC(5,4),
    top_crop VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_month UNIQUE(month)
);

-- Crop Distribution Summary
-- Tracks crop recommendation distribution
CREATE TABLE IF NOT EXISTS crop_distribution_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_name VARCHAR(100) NOT NULL,
    count INTEGER NOT NULL,
    percentage NUMERIC(5,2),
    color VARCHAR(7), -- Hex color for charts
    period VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_crop_period UNIQUE(crop_name, period, calculated_at)
);

-- System Performance Metrics
-- Tracks API performance and user satisfaction
CREATE TABLE IF NOT EXISTS system_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(50) NOT NULL, -- 'response_time', 'satisfaction', 'roi'
    avg_value NUMERIC,
    p50_value NUMERIC,
    p95_value NUMERIC,
    p99_value NUMERIC,
    sample_count INTEGER,
    period VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Satisfaction Table
-- Stores user feedback and ratings
CREATE TABLE IF NOT EXISTS user_satisfaction (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    prediction_id INTEGER REFERENCES predictions(id) ON DELETE SET NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);