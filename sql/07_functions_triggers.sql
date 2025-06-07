-- Database functions and triggers
-- Run after indexes.sql

-- Update trigger function for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_crops_updated_at ON crops;
CREATE TRIGGER update_crops_updated_at BEFORE UPDATE ON crops
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_chat_conversations_updated_at ON chat_conversations;
CREATE TRIGGER update_chat_conversations_updated_at 
    BEFORE UPDATE ON chat_conversations
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Session cleanup trigger
CREATE OR REPLACE FUNCTION mark_session_inactive()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ended_at IS NOT NULL AND OLD.ended_at IS NULL THEN
        NEW.is_active = false;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS session_end_trigger ON user_sessions;
CREATE TRIGGER session_end_trigger BEFORE UPDATE ON user_sessions
    FOR EACH ROW EXECUTE FUNCTION mark_session_inactive();

-- Cleanup expired tokens function
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Clean up expired password reset tokens
    DELETE FROM password_reset_tokens 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up expired sessions
    UPDATE user_sessions 
    SET is_active = false, ended_at = CURRENT_TIMESTAMP, logout_reason = 'expired'
    WHERE expires_at < CURRENT_TIMESTAMP AND is_active = true;
    
    RETURN deleted_count;
END;
$$ language 'plpgsql';

-- Function to calculate dashboard metrics
CREATE OR REPLACE FUNCTION calculate_dashboard_metrics()
RETURNS void AS $$
BEGIN
    -- Calculate predictions generated (last 30 days)
    INSERT INTO dashboard_metrics (metric_type, metric_name, value, change_percentage, period)
    VALUES (
        'dashboard',
        'predictions_generated',
        (SELECT COUNT(*) FROM predictions WHERE created_at > NOW() - INTERVAL '30 days'),
        (
            SELECT CASE 
                WHEN COUNT(*) FILTER (WHERE created_at BETWEEN NOW() - INTERVAL '60 days' AND NOW() - INTERVAL '30 days') = 0 THEN 0
                ELSE ((COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') - 
                      COUNT(*) FILTER (WHERE created_at BETWEEN NOW() - INTERVAL '60 days' AND NOW() - INTERVAL '30 days'))::numeric / 
                      COUNT(*) FILTER (WHERE created_at BETWEEN NOW() - INTERVAL '60 days' AND NOW() - INTERVAL '30 days') * 100)
            END
            FROM predictions
        ),
        'monthly'
    )
    ON CONFLICT (metric_type, metric_name, period, calculated_at) 
    DO UPDATE SET value = EXCLUDED.value, change_percentage = EXCLUDED.change_percentage;
    
    -- Calculate active users (only if user_sessions table has data)
    IF EXISTS (SELECT 1 FROM user_sessions LIMIT 1) THEN
        INSERT INTO dashboard_metrics (metric_type, metric_name, value, change_percentage, period)
        VALUES (
            'dashboard',
            'active_users',
            (SELECT COUNT(DISTINCT user_id) FROM user_sessions WHERE last_activity_at > NOW() - INTERVAL '30 days'),
            (
                SELECT CASE 
                    WHEN COUNT(DISTINCT user_id) FILTER (WHERE last_activity_at BETWEEN NOW() - INTERVAL '60 days' AND NOW() - INTERVAL '30 days') = 0 THEN 0
                    ELSE ((COUNT(DISTINCT user_id) FILTER (WHERE last_activity_at > NOW() - INTERVAL '30 days') - 
                          COUNT(DISTINCT user_id) FILTER (WHERE last_activity_at BETWEEN NOW() - INTERVAL '60 days' AND NOW() - INTERVAL '30 days'))::numeric / 
                          COUNT(DISTINCT user_id) FILTER (WHERE last_activity_at BETWEEN NOW() - INTERVAL '60 days' AND NOW() - INTERVAL '30 days') * 100)
                END
                FROM user_sessions
            ),
            'monthly'
        )
        ON CONFLICT (metric_type, metric_name, period, calculated_at) 
        DO UPDATE SET value = EXCLUDED.value, change_percentage = EXCLUDED.change_percentage;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to update monthly predictions summary
CREATE OR REPLACE FUNCTION update_monthly_predictions_summary()
RETURNS void AS $$
BEGIN
    INSERT INTO monthly_predictions_summary (
        month, 
        month_name, 
        predictions_count, 
        unique_users_count, 
        avg_confidence, 
        top_crop
    )
    SELECT 
        DATE_TRUNC('month', created_at)::date as month,
        TO_CHAR(created_at, 'Mon') as month_name,
        COUNT(*) as predictions_count,
        COUNT(DISTINCT user_id) as unique_users_count,
        AVG(confidence) as avg_confidence,
        (SELECT predicted_crop FROM predictions p2 
         WHERE DATE_TRUNC('month', p2.created_at) = DATE_TRUNC('month', p1.created_at)
         GROUP BY predicted_crop 
         ORDER BY COUNT(*) DESC 
         LIMIT 1) as top_crop
    FROM predictions p1
    WHERE created_at >= DATE_TRUNC('month', NOW() - INTERVAL '6 months')
    GROUP BY DATE_TRUNC('month', created_at), TO_CHAR(created_at, 'Mon')
    ON CONFLICT (month) 
    DO UPDATE SET 
        predictions_count = EXCLUDED.predictions_count,
        unique_users_count = EXCLUDED.unique_users_count,
        avg_confidence = EXCLUDED.avg_confidence,
        top_crop = EXCLUDED.top_crop;
END;
$$ LANGUAGE plpgsql;