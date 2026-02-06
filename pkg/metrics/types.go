package metrics

import "time"

// PodMetrics represents metrics for a single pod
type PodMetrics struct {
	PodName      string            `json:"pod_name"`
	Namespace    string            `json:"namespace"`
	Timestamp    time.Time         `json:"timestamp"`
	MemoryUsage  float64           `json:"memory_usage_mb"` // bytes
	CPUUsage     float64           `json:"cpu_usage"`       // cores
	RestartCount int               `json:"restart_count"`
	Status       string            `json:"status"`
	Labels       map[string]string `json:"labels"`
}

// TimeSeriesMetrics represents time-series data for ML
type TimeSeriesMetrics struct {
	PodName   string      `json:"pod_name"`
	Namespace string      `json:"namespace"`
	Metrics   []DataPoint `json:"metrics"`
}

// DataPoint represents a single metric point
type DataPoint struct {
	Timestamp  time.Time `json:"timestamp"`
	Value      float64   `json:"value"`
	MetricType string    `json:"metric_type"`
}
