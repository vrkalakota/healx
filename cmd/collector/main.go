package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/vrkalakota/healx/pkg/metrics"
	"github.com/vrkalakota/healx/pkg/storage"
)

func main() {
	log.Println("HealX Metrics Collector - Starting...")

	// Create context with cancellation
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Setup signal handling
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	// Initialize Prometheus client
	promClient, err := metrics.NewPrometheusClient("http://localhost:9090") // Update for production
	if err != nil {
		log.Fatalf("Failed to create Prometheus client: %v", err)
	}

	// Initialize database
	db, err := storage.NewDB(storage.Config{
		Host:     "localhost", // Update for production
		Port:     5432,
		User:     "healx_user",
		Password: "healx_pass_dev_only",
		DBName:   "healx",
	})
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	metricsStore := storage.NewMetricsStore(db)

	// Start collection loop
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	log.Println("Metrics collector started successfully")

	for {
		select {
		case <-ticker.C:
			if err := collectMetrics(ctx, promClient, metricsStore); err != nil {
				log.Printf("Error collecting metrics: %v", err)
			}
		case <-sigChan:
			log.Println("Received shutdown signal, stopping collector...")
			return
		}
	}
}

func collectMetrics(ctx context.Context, promClient *metrics.PrometheusClient, store *storage.MetricsStore) error {
	// For now, hardcode pod to collect metrics from
	// In production, this would query k8s API for all pods with label
	podName := "leaky-app"
	namespace := "healx"

	memory, err := promClient.QueryMemoryUsage(ctx, podName, namespace)
	if err != nil {
		return fmt.Errorf("error querying memory: %w", err)
	}

	cpu, err := promClient.QueryCPUUsage(ctx, podName, namespace)
	if err != nil {
		return fmt.Errorf("error querying CPU: %w", err)
	}

	podMetrics := &metrics.PodMetrics{
		PodName:     podName,
		Namespace:   namespace,
		Timestamp:   time.Now(),
		MemoryUsage: memory,
		CPUUsage:    cpu,
		Labels:      map[string]string{"app": "leaky-app"},
	}

	if err := store.SaveMetrics(podMetrics); err != nil {
		return fmt.Errorf("error saving metrics: %w", err)
	}

	log.Printf("Collected metrics for %s: Memory=%.2f bytes, CPU=%.4f cores",
		podName, memory, cpu)

	return nil
}
