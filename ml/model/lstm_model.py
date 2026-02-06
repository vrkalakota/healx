import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from typing import Tuple
import json
import os

class LSTMPredictor:
    def __init__(self, sequence_length: int = 60, 
                 prediction_horizon: int = 10,
                 lstm_units: int = 64):
        """
        LSTM-based time series predictor
        
        Args:
            sequence_length: Number of time steps to look back
            prediction_horizon: Number of time steps to predict ahead
            lstm_units: Number of units in LSTM layers
        """
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.lstm_units = lstm_units
        self.model = None
        self.scaling_params = None
        
    def build_model(self):
        """Build LSTM model architecture"""
        model = keras.Sequential([
            # Input layer
            layers.Input(shape=(self.sequence_length, 1)),
            
            # First LSTM layer with return sequences
            layers.LSTM(self.lstm_units, return_sequences=True),
            layers.Dropout(0.2),
            
            # Second LSTM layer
            layers.LSTM(self.lstm_units // 2),
            layers.Dropout(0.2),
            
            # Dense layers
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.2),
            
            # Output layer
            layers.Dense(self.prediction_horizon)
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        return model
        
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
             X_val: np.ndarray, y_val: np.ndarray,
             epochs: int = 50, batch_size: int = 32) -> dict:
        """
        Train the LSTM model
        
        Returns:
            Training history
        """
        if self.model is None:
            self.build_model()
            
        # Reshape input for LSTM [samples, timesteps, features]
        X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
        X_val = X_val.reshape(X_val.shape[0], X_val.shape[1], 1)
        
        # Callbacks
        early_stopping = keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        reduce_lr = keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=0.00001
        )
        
        # Train
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stopping, reduce_lr],
            verbose=1
        )
        
        return history.history
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not built or loaded")
            
        X = X.reshape(X.shape[0], X.shape[1], 1)
        predictions = self.model.predict(X)
        return predictions
        
    def predict_single(self, sequence: np.ndarray) -> np.ndarray:
        """Predict for a single sequence"""
        sequence = sequence.reshape(1, -1, 1)
        prediction = self.model.predict(sequence, verbose=0)
        return prediction[0]
        
    def save_model(self, path: str):
        """Save model and scaling parameters"""
        if self.model is None:
            raise ValueError("No model to save")
            
        # Save model
        self.model.save(path)
        
        # Save scaling parameters
        if self.scaling_params:
            params_path = os.path.join(os.path.dirname(path), 'scaling_params.json')
            with open(params_path, 'w') as f:
                # Convert numpy types to Python types for JSON serialization
                params_serializable = {
                    k: float(v) if isinstance(v, (np.floating, np.integer)) else v 
                    for k, v in self.scaling_params.items()
                }
                json.dump(params_serializable, f)
                
    def load_model(self, path: str):
        """Load model and scaling parameters"""
        self.model = keras.models.load_model(path, compile=False)
        
        # Load scaling parameters
        params_path = os.path.join(os.path.dirname(path), 'scaling_params.json')
        if os.path.exists(params_path):
            with open(params_path, 'r') as f:
                self.scaling_params = json.load(f)
                
    def set_scaling_params(self, params: dict):
        """Set scaling parameters for normalization"""
        self.scaling_params = params
        
    def denormalize(self, normalized_values: np.ndarray) -> np.ndarray:
        """Denormalize predictions"""
        if self.scaling_params is None:
            raise ValueError("Scaling parameters not set")
            
        y_min = self.scaling_params['y_min']
        y_max = self.scaling_params['y_max']
        
        return normalized_values * (y_max - y_min) + y_min