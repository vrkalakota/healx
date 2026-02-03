.PHONY: help build test run clean

help:
    @echo "HealX - Available commands:"
	@echo "  make setup          - Initial project setup"
	@echo "  make build          - Build all services"
	@echo "  make test           - Run all tests"
	@echo "  make run-collector  - Run metrics collector"
	@echo "  make run-controller - Run healing controller"
	@echo "  make run-ml         - Run ML API"
	@echo "  make deploy-local   - Deploy to Minikube"
	@echo "  make clean          - Clean build artifacts"

setup:
	@echo "Setting up HealX..."
	go mod download
	cd ml && python -m venv venv && . venv/bin/activate && pip install -r requirements.txt

build:
	@echo "Building services..."
	go build -o bin/collector cmd/collector/main.go
	go build -o bin/controller cmd/controller/main.go
	go build -o bin/api cmd/api/main.go

test:
	go test ./...
	cd ml && . venv/bin/activate && pytest

run-collector:
	go run cmd/collector/main.go

run-controller:
	go run cmd/controller/main.go

run-ml:
	cd ml && . venv/bin/activate && python api/app.py

clean:
	rm -rf bin/
	go clean