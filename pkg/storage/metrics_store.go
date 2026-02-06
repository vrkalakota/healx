package storage

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/vrkalakota/healx/pkg/metrics"
)

type MetricsStore struct {
	db *DB
}

// NewMetricsStore creates a new metrics store
func NewMetricsStore(db *DB) *MetricsStore {
	return &MetricsStore{db: db}
}

// SaveMetrics saves pod metrics to database
func (ms *MetricsStore) SaveMetrics(m *metrics.PodMetrics) error {
	labelsJSON, err := json.Marshal(m.Labels)
	if err != nil {
		return fmt.Errorf("error marshaling labels: %w", err)
	}

	// Save memory metric
	_, err = ms.db.conn.Exec(`
        INSERT INTO metrics (pod_name, namespace, metric_name, metric_value, timestamp, labels)
        VALUES ($1, $2, $3, $4, $5, $6)
    `, m.PodName, m.Namespace, "memory_usage_mb", m.MemoryUsage, m.Timestamp, labelsJSON)
	if err != nil {
		return fmt.Errorf("error saving memory metric: %w", err)
	}

	// Save CPU metric
	_, err = ms.db.conn.Exec(`
        INSERT INTO metrics (pod_name, namespace, metric_name, metric_value, timestamp, labels)
        VALUES ($1, $2, $3, $4, $5, $6)
    `, m.PodName, m.Namespace, "cpu_usage", m.CPUUsage, m.Timestamp, labelsJSON)
	if err != nil {
		return fmt.Errorf("error saving cpu metric: %w", err)
	}

	return nil
}

// GetTimeSeriesMetrics retrieves time-series metrics for a pod
func (ms *MetricsStore) GetTimeSeriesMetrics(podName, namespace, metricName string, since time.Time) ([]metrics.DataPoint, error) {
	rows, err := ms.db.conn.Query(`
        SELECT metric_value, timestamp
        FROM metrics
        WHERE pod_name = $1 AND namespace = $2 AND metric_name = $3 AND timestamp >= $4
        ORDER BY timestamp ASC
    `, podName, namespace, metricName, since)
	if err != nil {
		return nil, fmt.Errorf("error querying metrics: %w", err)
	}
	defer rows.Close()

	var dataPoints []metrics.DataPoint
	for rows.Next() {
		var dp metrics.DataPoint
		if err := rows.Scan(&dp.Value, &dp.Timestamp); err != nil {
			return nil, fmt.Errorf("error scanning row: %w", err)
		}
		dp.MetricType = metricName
		dataPoints = append(dataPoints, dp)
	}

	return dataPoints, nil
}
