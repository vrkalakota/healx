-- Create tables for HealX

-- Metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    pod_name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    labels JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pod_time (pod_name, timestamp),
    INDEX idx_metric_time (metric_name, timestamp)
);

-- Anomalies table
CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    pod_name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    anomaly_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    confidence DOUBLE PRECISION,
    metrics JSONB,
    detected_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'detected',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pod_status (pod_name, status),
    INDEX idx_detected_time (detected_at)
);

-- Healing actions table
CREATE TABLE IF NOT EXISTS healing_actions (
    id SERIAL PRIMARY KEY,
    anomaly_id INTEGER REFERENCES anomalies(id),
    pod_name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    action_details JSONB,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_anomaly (anomaly_id),
    INDEX idx_pod_action (pod_name, action_type)
);

-- Model predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    pod_name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    prediction_type VARCHAR(100) NOT NULL,
    predicted_value DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    prediction_window INTEGER, -- minutes ahead
    features JSONB,
    predicted_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pod_prediction_time (pod_name, predicted_at)
);