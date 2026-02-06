from flask import Flask, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from model.lstm_model import LSTMPredictor
from model.data_loader import DataLoader
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

# Global model instance
predictor = None
data_loader = None

# Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'healx_user'),
    'password': os.getenv('DB_PASSWORD', 'healx_pass_dev_only'),
    'dbname': os.getenv('DB_NAME', 'healx')
}

MODEL_PATH = os.getenv('MODEL_PATH', '../model/saved_models/lstm_predictor.keras')

def load_model():
    """Load the trained model"""
    global predictor
    predictor = LSTMPredictor()
    predictor.load_model(MODEL_PATH)
    print(f"Model loaded from {MODEL_PATH}")

def init_data_loader():
    """Initialize data loader"""
    global data_loader
    data_loader = DataLoader(DB_CONFIG)
    data_loader.connect()
    print("Data loader initialized")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'model_loaded': predictor is not None})

@app.route('/predict', methods=['POST'])
def predict():
    """
    Predict future memory usage
    
    Request body:
    {
        "pod_name": "leaky-app-xxx",
        "namespace": "healx",
        "metric_name": "memory_usage_mb"
    }
    
    Response:
    {
        "predictions": [value1, value2, ...],
        "timestamps": ["time1", "time2", ...],
        "confidence": 0.95,
        "anomaly_detected": true/false
    }
    """
    if predictor is None:
        return jsonify({'error': 'Model not loaded'}), 500
        
    data = request.get_json()
    
    pod_name = data.get('pod_name')
    namespace = data.get('namespace', 'healx')
    metric_name = data.get('metric_name', 'memory_usage_mb')
    
    if not pod_name:
        return jsonify({'error': 'pod_name required'}), 400
    
    try:
        # Load recent metrics (last 30 minutes for 60 data points at 30s intervals)
        df = data_loader.load_metrics(
            pod_name=pod_name,
            namespace=namespace,
            metric_name=metric_name,
            hours_back=1
        )
        
        if len(df) < 60:
            return jsonify({'error': 'Insufficient data for prediction'}), 400
        
        # Get last 60 points
        recent_data = df['metric_value'].values[-60:]
        
        # Normalize
        X_min = predictor.scaling_params['X_min']
        X_max = predictor.scaling_params['X_max']
        recent_normalized = (recent_data - X_min) / (X_max - X_min + 1e-8)
        
        # Predict
        prediction_normalized = predictor.predict_single(recent_normalized)
        
        # Denormalize
        prediction = predictor.denormalize(prediction_normalized)
        
        # Generate timestamps for predictions
        last_timestamp = df.index[-1]
        prediction_timestamps = [
            (last_timestamp + timedelta(seconds=30 * (i + 1))).isoformat()
            for i in range(len(prediction))
        ]
        
        # Simple anomaly detection: check if prediction exceeds threshold
        # Using 90th percentile of recent data as threshold
        threshold = np.percentile(recent_data, 90)
        anomaly_detected = any(p > threshold * 1.2 for p in prediction)
        
        # Calculate confidence (inverse of prediction variance)
        confidence = 1.0 / (1.0 + np.std(prediction) / np.mean(prediction))
        
        response = {
            'pod_name': pod_name,
            'namespace': namespace,
            'metric_name': metric_name,
            'predictions': prediction.tolist(),
            'timestamps': prediction_timestamps,
            'confidence': float(confidence),
            'anomaly_detected': anomaly_detected,
            'threshold': float(threshold),
            'predicted_at': datetime.utcnow().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/detect-anomaly', methods=['POST'])
def detect_anomaly():
    """
    Detect if current metrics show anomalous behavior
    
    Request body:
    {
        "pod_name": "leaky-app-xxx",
        "namespace": "healx",
        "metric_name": "memory_usage_mb"
    }
    """
    data = request.get_json()
    
    pod_name = data.get('pod_name')
    namespace = data.get('namespace', 'healx')
    metric_name = data.get('metric_name', 'memory_usage_mb')
    
    if not pod_name:
        return jsonify({'error': 'pod_name required'}), 400
    
    try:
        # Load recent metrics
        df = data_loader.load_metrics(
            pod_name=pod_name,
            namespace=namespace,
            metric_name=metric_name,
            hours_back=2
        )
        
        if len(df) < 60:
            return jsonify({'error': 'Insufficient data'}), 400
        
        # Label anomalies
        df_labeled = data_loader.create_labeled_dataset(df)
        
        # Check recent data for anomalies
        recent_anomalies = df_labeled.tail(10)['is_anomaly'].sum()
        is_anomaly = recent_anomalies > 5  # More than half of recent points are anomalous
        
        # Calculate severity based on how far current value is from normal
        current_value = df['metric_value'].iloc[-1]
        normal_mean = df['metric_value'].quantile(0.5)
        normal_std = df['metric_value'].std()
        
        severity_score = abs(current_value - normal_mean) / (normal_std + 1e-8)
        
        if severity_score < 2:
            severity = 'low'
        elif severity_score < 3:
            severity = 'medium'
        else:
            severity = 'high'
        
        response = {
            'pod_name': pod_name,
            'namespace': namespace,
            'is_anomaly': bool(is_anomaly),
            'severity': severity,
            'severity_score': float(severity_score),
            'current_value': float(current_value),
            'normal_range': {
                'mean': float(normal_mean),
                'std': float(normal_std)
            },
            'detected_at': datetime.utcnow().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("HealX ML API - Starting...")
    load_model()
    init_data_loader()
    app.run(host='0.0.0.0', port=5000, debug=True)