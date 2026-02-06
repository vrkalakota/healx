import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import psycopg2
from typing import Tuple, List

class DataLoader:
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.conn = None
        
    def connect(self):
        """Connect to PostgreSQL database"""
        self.conn = psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            dbname=self.db_config['dbname']
        )
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def load_metrics(self, pod_name: str, namespace: str, 
                    metric_name: str, hours_back: int = 24) -> pd.DataFrame:
        """Load metrics from database"""
        if not self.conn:
            self.connect()
            
        query = """
            SELECT timestamp, metric_value
            FROM metrics
            WHERE pod_name = %s 
              AND namespace = %s 
              AND metric_name = %s
              AND timestamp >= NOW() - INTERVAL '%s hours'
            ORDER BY timestamp ASC
        """
        
        df = pd.read_sql_query(
            query, 
            self.conn, 
            params=(pod_name, namespace, metric_name, hours_back)
        )
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        return df
        
    def prepare_sequences(self, df: pd.DataFrame, 
                         sequence_length: int = 60,
                         prediction_horizon: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequences for LSTM training
        
        Args:
            df: DataFrame with metric values
            sequence_length: Number of time steps to look back
            prediction_horizon: Number of time steps to predict ahead
            
        Returns:
            X: Input sequences (samples, sequence_length, features)
            y: Target values (samples, prediction_horizon)
        """
        values = df['metric_value'].values
        
        X, y = [], []
        
        for i in range(len(values) - sequence_length - prediction_horizon):
            X.append(values[i:i + sequence_length])
            y.append(values[i + sequence_length:i + sequence_length + prediction_horizon])
            
        return np.array(X), np.array(y)
        
    def normalize_data(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, dict]:
        """
        Normalize data using min-max scaling
        
        Returns:
            Normalized X, y, and scaling parameters
        """
        X_min, X_max = X.min(), X.max()
        y_min, y_max = y.min(), y.max()
        
        X_normalized = (X - X_min) / (X_max - X_min + 1e-8)
        y_normalized = (y - y_min) / (y_max - y_min + 1e-8)
        
        scaling_params = {
            'X_min': X_min,
            'X_max': X_max,
            'y_min': y_min,
            'y_max': y_max
        }
        
        return X_normalized, y_normalized, scaling_params
        
    def create_labeled_dataset(self, df: pd.DataFrame, 
                              anomaly_threshold: float = None) -> pd.DataFrame:
        """
        Create labeled dataset for anomaly detection
        
        Args:
            df: DataFrame with metrics
            anomaly_threshold: Threshold for labeling anomalies (e.g., 90th percentile)
            
        Returns:
            DataFrame with 'is_anomaly' column
        """
        if anomaly_threshold is None:
            # Use 95th percentile as threshold
            anomaly_threshold = df['metric_value'].quantile(0.95)
            
        df['is_anomaly'] = (df['metric_value'] > anomaly_threshold).astype(int)
        
        # Mark sequences leading up to anomalies
        window = 10  # Mark 10 minutes before anomaly
        for idx in df[df['is_anomaly'] == 1].index:
            start_idx = max(0, df.index.get_loc(idx) - window)
            end_idx = df.index.get_loc(idx)
            df.iloc[start_idx:end_idx, df.columns.get_loc('is_anomaly')] = 1
            
        return df