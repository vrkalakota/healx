FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY model/ ./model/
COPY api/ ./api/

# Create directory for models
RUN mkdir -p /models

# ✅ Bake the trained model into the image at /models
COPY model/saved_models/lstm_predictor.keras /models/lstm_predictor.keras
COPY model/saved_models/scaling_params.json /models/scaling_params.json

WORKDIR /app/api

EXPOSE 5000

CMD ["python", "app.py"]