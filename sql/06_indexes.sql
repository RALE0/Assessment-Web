-- Database indexes for performance optimization
-- Run after all table schemas are created

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_email_verification_token ON users(email_verification_token);
CREATE INDEX IF NOT EXISTS idx_users_active_created ON users(is_active, created_at);

-- User sessions table indexes
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_is_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_user_active ON user_sessions(user_id, is_active);

-- Session activities table indexes
CREATE INDEX IF NOT EXISTS idx_activities_user_id ON session_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_activities_session_id ON session_activities(session_id);
CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON session_activities(timestamp);
CREATE INDEX IF NOT EXISTS idx_activities_type ON session_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_activities_details ON session_activities USING GIN(activity_details);
CREATE INDEX IF NOT EXISTS idx_activities_user_timestamp ON session_activities(user_id, timestamp DESC);

-- Password reset tokens table indexes
CREATE INDEX IF NOT EXISTS idx_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_reset_tokens_expires_at ON password_reset_tokens(expires_at);

-- Crops table indexes
CREATE INDEX IF NOT EXISTS idx_crops_name ON crops(name);
CREATE INDEX IF NOT EXISTS idx_crops_created_at ON crops(created_at);

-- Predictions table indexes
CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_crop ON predictions(predicted_crop);
CREATE INDEX IF NOT EXISTS idx_predictions_client_ip ON predictions(client_ip);
CREATE INDEX IF NOT EXISTS idx_predictions_user_created ON predictions(user_id, created_at DESC);

-- API Requests table indexes
CREATE INDEX IF NOT EXISTS idx_api_requests_endpoint ON api_requests(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_requests_created_at ON api_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_api_requests_status_code ON api_requests(status_code);
CREATE INDEX IF NOT EXISTS idx_api_requests_user_id ON api_requests(user_id);

-- Analytics table indexes
CREATE INDEX IF NOT EXISTS idx_dashboard_metrics_type ON dashboard_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_dashboard_metrics_calculated ON dashboard_metrics(calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_dashboard_metrics_period ON dashboard_metrics(period);

CREATE INDEX IF NOT EXISTS idx_prediction_analytics_prediction ON prediction_analytics(prediction_id);
CREATE INDEX IF NOT EXISTS idx_prediction_analytics_region ON prediction_analytics(region);
CREATE INDEX IF NOT EXISTS idx_prediction_analytics_created ON prediction_analytics(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_prediction_analytics_user ON prediction_analytics(user_id);

CREATE INDEX IF NOT EXISTS idx_model_performance_version ON model_performance(model_version);
CREATE INDEX IF NOT EXISTS idx_model_performance_metric ON model_performance(metric_name);
CREATE INDEX IF NOT EXISTS idx_model_performance_evaluated ON model_performance(evaluated_at DESC);

CREATE INDEX IF NOT EXISTS idx_monthly_predictions_month ON monthly_predictions_summary(month DESC);

CREATE INDEX IF NOT EXISTS idx_crop_distribution_crop ON crop_distribution_summary(crop_name);
CREATE INDEX IF NOT EXISTS idx_crop_distribution_period ON crop_distribution_summary(period);

CREATE INDEX IF NOT EXISTS idx_chat_conversations_conversation ON chat_conversations(conversation_id);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_user ON chat_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_updated ON chat_conversations(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation ON chat_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_search ON chat_messages USING GIN(to_tsvector('spanish', message));

CREATE INDEX IF NOT EXISTS idx_system_performance_type ON system_performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_system_performance_calculated ON system_performance_metrics(calculated_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_satisfaction_user ON user_satisfaction(user_id);
CREATE INDEX IF NOT EXISTS idx_user_satisfaction_rating ON user_satisfaction(rating);
CREATE INDEX IF NOT EXISTS idx_user_satisfaction_created ON user_satisfaction(created_at DESC);