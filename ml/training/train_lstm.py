import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from model.data_loader import DataLoader
from model.lstm_model import LSTMPredictor
import numpy as np
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

def main():
    print("Starting LSTM model training...")
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'healx_user',
        'password': 'healx_pass_dev_only',
        'dbname': 'healx'
    }
    
    # Initialize data loader
    loader = DataLoader(db_config)
    
    # Load metrics
    print("Loading data from database...")
    df = loader.load_metrics(
        pod_name='leaky-app',
        namespace='healx',
        metric_name='memory_usage_mb_mb',
        hours_back=24
    )
    
    print(f"Loaded {len(df)} data points")
    
    # Prepare sequences
    print("Preparing sequences...")
    X, y = loader.prepare_sequences(
        df, 
        sequence_length=60,  # 30 minutes of data (30s intervals)
        prediction_horizon=10  # Predict next 5 minutes
    )
    
    print(f"Created {len(X)} sequences")
    
    # Normalize
    print("Normalizing data...")
    X_norm, y_norm, scaling_params = loader.normalize_data(X, y)
    
    # Split into train and validation
    X_train, X_val, y_train, y_val = train_test_split(
        X_norm, y_norm, test_size=0.2, random_state=42
    )
    
    print(f"Training set: {len(X_train)} samples")
    print(f"Validation set: {len(X_val)} samples")
    
    # Create and train model
    print("Building LSTM model...")
    predictor = LSTMPredictor(
        sequence_length=60,
        prediction_horizon=10,
        lstm_units=64
    )
    
    predictor.set_scaling_params(scaling_params)
    
    print("Training model...")
    history = predictor.train(
        X_train, y_train,
        X_val, y_val,
        epochs=50,
        batch_size=32
    )
    
    # Save model
    model_dir = '../model/saved_models'
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, 'lstm_predictor.keras')
    
    print(f"Saving model to {model_path}")
    predictor.save_model(model_path)
    
    # Plot training history
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(history['loss'], label='Training Loss')
    plt.plot(history['val_loss'], label='Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Model Loss')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history['mae'], label='Training MAE')
    plt.plot(history['val_mae'], label='Validation MAE')
    plt.xlabel('Epoch')
    plt.ylabel('MAE')
    plt.title('Model MAE')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('../model/training_history.png')
    print("Training history plot saved to ../model/training_history.png")
    
    # Test prediction
    print("\nTesting prediction on validation data...")
    test_idx = 0
    test_sequence = X_val[test_idx]
    test_actual = y_val[test_idx]
    
    prediction = predictor.predict_single(test_sequence)
    
    # Denormalize
    prediction_denorm = predictor.denormalize(prediction)
    actual_denorm = predictor.denormalize(test_actual)
    
    print(f"Predicted: {prediction_denorm[:5]}")
    print(f"Actual: {actual_denorm[:5]}")
    
    loader.close()
    print("\nTraining complete!")

if __name__ == '__main__':
    main()