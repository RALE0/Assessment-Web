-- Database views for real-time data access
-- Run after functions_triggers.sql

-- Create a view for real-time dashboard metrics
CREATE OR REPLACE VIEW dashboard_metrics_view AS
SELECT 
    (SELECT COUNT(*) FROM predictions WHERE created_at > NOW() - INTERVAL '30 days') as predictions_generated,
    (SELECT COUNT(*) FROM predictions WHERE created_at > NOW() - INTERVAL '1 day') as predictions_today,
    (SELECT AVG(confidence) FROM predictions WHERE created_at > NOW() - INTERVAL '30 days') as avg_confidence,
    (SELECT CASE WHEN EXISTS (SELECT 1 FROM user_sessions LIMIT 1) 
             THEN (SELECT COUNT(DISTINCT user_id) FROM user_sessions WHERE last_activity_at > NOW() - INTERVAL '30 days')
             ELSE 0 END) as active_users,
    (SELECT COUNT(DISTINCT predicted_crop) FROM predictions) as crops_analyzed,
    (SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '30 days') as new_users_month;