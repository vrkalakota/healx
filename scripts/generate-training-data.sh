#!/bin/bash
   
echo "Generating training data for ML model..."

# Port forward Prometheus
kubectl port-forward -n healx svc/prometheus-server 9090:80 &
PF_PID=$!

sleep 5

# Let the leaky app run for data collection
echo "Collecting normal behavior data (5 minutes)..."
sleep 300

# Trigger memory leak
echo "Triggering memory leak..."
POD=$(kubectl get pods -n healx -l app=leaky-app -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward -n healx $POD 8080:8080 &
PF_APP_PID=$!

sleep 5

for i in {1..20}; do
    curl http://localhost:8080/load
    sleep 10
done

echo "Waiting for OOM kill and recovery (10 minutes)..."
sleep 600

# Kill port forwards
kill $PF_PID
kill $PF_APP_PID

echo "Training data generation complete!"