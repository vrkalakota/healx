-- Create tables for HealX (PostgreSQL)

-- Metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    pod_name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    "timestamp" TIMESTAMP NOT NULL,
    labels JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pod_time ON metrics (pod_name, "timestamp");
CREATE INDEX IF NOT EXISTS idx_metric_time ON metrics (metric_name, "timestamp");

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pod_status ON anomalies (pod_name, status);
CREATE INDEX IF NOT EXISTS idx_detected_time ON anomalies (detected_at);

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anomaly ON healing_actions (anomaly_id);
CREATE INDEX IF NOT EXISTS idx_pod_action ON healing_actions (pod_name, action_type);

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pod_prediction_time ON predictions (pod_name, predicted_at);