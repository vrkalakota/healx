package main

import (
	"fmt"
	"log"
	"net/http"
	"runtime"
	"time"
)

var memoryLeakData [][]byte

func main() {
	// Start memory leak goroutine
	go simulateMemoryLeak()

	// Health endpoint
	http.HandleFunc("/health", healthHandler)

	// Metrics endpoint (Prometheus format)
	http.HandleFunc("/metrics", metricsHandler)

	// Load endpoint to trigger more memory usage
	http.HandleFunc("/load", loadHandler)

	fmt.Println("Leaky Demo App starting on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, "OK")
}

func metricsHandler(w http.ResponseWriter, r *http.Request) {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	fmt.Fprintf(w, "# HELP memory_usage_mb_bytes Current memory usage\n")
	fmt.Fprintf(w, "# TYPE memory_usage_mb_bytes gauge\n")
	fmt.Fprintf(w, "memory_usage_mb_bytes %d\n", m.Alloc)

	fmt.Fprintf(w, "# HELP goroutines_count Number of goroutines\n")
	fmt.Fprintf(w, "# TYPE goroutines_count gauge\n")
	fmt.Fprintf(w, "goroutines_count %d\n", runtime.NumGoroutine())
}

func loadHandler(w http.ResponseWriter, r *http.Request) {
	// Intentionally leak memory
	data := make([]byte, 10*1024*1024) // 10MB
	memoryLeakData = append(memoryLeakData, data)

	fmt.Fprintf(w, "Added 10MB to memory leak. Total leaked: %d MB\n",
		len(memoryLeakData)*10)
}

func simulateMemoryLeak() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		// Leak 5MB every 30 seconds
		data := make([]byte, 5*1024*1024)
		memoryLeakData = append(memoryLeakData, data)

		var m runtime.MemStats
		runtime.ReadMemStats(&m)
		log.Printf("Memory leak simulation: Alloc = %v MB, Sys = %v MB, NumGC = %v\n",
			m.Alloc/1024/1024, m.Sys/1024/1024, m.NumGC)
	}
}
