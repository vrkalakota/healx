package metrics

import (
	"context"
	"fmt"
	"time"

	"github.com/prometheus/client_golang/api"
	v1 "github.com/prometheus/client_golang/api/prometheus/v1"
	"github.com/prometheus/common/model"
)

type PrometheusClient struct {
	client api.Client
	api    v1.API
}

// NewPrometheusClient creates a new Prometheus client
func NewPrometheusClient(url string) (*PrometheusClient, error) {
	client, err := api.NewClient(api.Config{
		Address: url,
	})
	if err != nil {
		return nil, fmt.Errorf("error creating prometheus client: %w", err)
	}

	return &PrometheusClient{
		client: client,
		api:    v1.NewAPI(client),
	}, nil
}

// QueryMemoryUsage queries memory usage for a pod
func (pc *PrometheusClient) QueryMemoryUsage(ctx context.Context, podName, namespace string) (float64, error) {
	query := fmt.Sprintf(
		`container_memory_usage_mb_bytes{pod="%s", namespace="%s"}`,
		podName, namespace,
	)

	result, warnings, err := pc.api.Query(ctx, query, time.Now())
	if err != nil {
		return 0, fmt.Errorf("error querying prometheus: %w", err)
	}
	if len(warnings) > 0 {
		fmt.Printf("Warnings: %v\n", warnings)
	}

	vector, ok := result.(model.Vector)
	if !ok || len(vector) == 0 {
		return 0, fmt.Errorf("no data found")
	}

	return float64(vector[0].Value), nil
}

// QueryCPUUsage queries CPU usage for a pod
func (pc *PrometheusClient) QueryCPUUsage(ctx context.Context, podName, namespace string) (float64, error) {
	query := fmt.Sprintf(
		`rate(container_cpu_usage_seconds_total{pod="%s", namespace="%s"}[5m])`,
		podName, namespace,
	)

	result, warnings, err := pc.api.Query(ctx, query, time.Now())
	if err != nil {
		return 0, fmt.Errorf("error querying prometheus: %w", err)
	}
	if len(warnings) > 0 {
		fmt.Printf("Warnings: %v\n", warnings)
	}

	vector, ok := result.(model.Vector)
	if !ok || len(vector) == 0 {
		return 0, fmt.Errorf("no data found")
	}

	return float64(vector[0].Value), nil
}

// QueryRange queries metrics over a time range
func (pc *PrometheusClient) QueryRange(ctx context.Context, query string, start, end time.Time, step time.Duration) ([]DataPoint, error) {
	r := v1.Range{
		Start: start,
		End:   end,
		Step:  step,
	}

	result, warnings, err := pc.api.QueryRange(ctx, query, r)
	if err != nil {
		return nil, fmt.Errorf("error querying prometheus range: %w", err)
	}
	if len(warnings) > 0 {
		fmt.Printf("Warnings: %v\n", warnings)
	}

	matrix, ok := result.(model.Matrix)
	if !ok || len(matrix) == 0 {
		return nil, fmt.Errorf("no data found")
	}

	var dataPoints []DataPoint
	for _, sample := range matrix[0].Values {
		dataPoints = append(dataPoints, DataPoint{
			Timestamp: sample.Timestamp.Time(),
			Value:     float64(sample.Value),
		})
	}

	return dataPoints, nil
}
