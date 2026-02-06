from data_loader import DataLoader
import matplotlib.pyplot as plt

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
df = loader.load_metrics(
    pod_name='leaky-app',
    namespace='healx',
    metric_name='memory_usage_mb',
    hours_back=24
)

print(f"Loaded {len(df)} data points")
print(df.head())

# Create labeled dataset
df_labeled = loader.create_labeled_dataset(df)
print(f"Anomalies detected: {df_labeled['is_anomaly'].sum()}")

# Prepare sequences
X, y = loader.prepare_sequences(df_labeled, sequence_length=60, prediction_horizon=10)
print(f"X shape: {X.shape}, y shape: {y.shape}")

# Normalize
X_norm, y_norm, params = loader.normalize_data(X, y)
print(f"Normalization params: {params}")

# Plot
plt.figure(figsize=(15, 5))
plt.plot(df.index, df['metric_value'], label='Memory Usage')
plt.scatter(df_labeled[df_labeled['is_anomaly'] == 1].index, 
            df_labeled[df_labeled['is_anomaly'] == 1]['metric_value'],
            color='red', label='Anomalies', zorder=5)
plt.xlabel('Time')
plt.ylabel('Memory (bytes)')
plt.title('Memory Usage with Anomaly Labels')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('memory_usage_mb_labeled.png')
print("Plot saved to memory_usage_mb_labeled.png")

loader.close()