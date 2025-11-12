from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime

try:
    from sklearn.preprocessing import MinMaxScaler, RobustScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except Exception as e:
    print(f"scikit-learn import error: {e}")
    SKLEARN_AVAILABLE = False

try:
    from joblib import dump as joblib_dump
    JOBLIB_AVAILABLE = True
except Exception:
    JOBLIB_AVAILABLE = False

try:
    # TensorFlow is heavy; import guarded
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, Callback
    from tensorflow.keras.regularizers import l2
    TENSORFLOW_AVAILABLE = True
except Exception as e:
    print(f"TensorFlow import error: {e}")
    TENSORFLOW_AVAILABLE = False

# Configuration
DATA_PATH = Path("data/outbreakiq_training_data_filled.csv")
MODEL_PATH = Path("models/lstm_forecaster.h5")
SCALER_PATH = Path("models/target_scaler.joblib")  # Save target scaler separately
FEATURE_SCALER_PATH = Path("models/feature_scaler.joblib")

# Model hyperparameters
WINDOW_SIZE = 8  # Number of weeks to look back
BATCH_SIZE = 32
EPOCHS = 200
PATIENCE = 15
LEARNING_RATE = 0.001
DROPOUT_RATE = 0.3
L2_REG = 0.01
REAL_UNIT_THRESHOLD = float(os.getenv("REAL_UNIT_THRESHOLD", "100.0"))  # cases MAE threshold

# Features to use for prediction
FEATURES = [
    "cases",
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "precipitation_sum",
]

def load_and_validate_data():
    """Load and validate the training data."""
    print("\n=== Loading and Validating Data ===")
    
    # Load data
    if not DATA_PATH.exists():
        print(f"Error: Data file not found at {DATA_PATH}")
        sys.exit(1)
    
    df = pd.read_csv(DATA_PATH)
    
    # Check required columns
    required_cols = FEATURES + ["year", "week", "state", "disease"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        sys.exit(1)
    
    # Handle missing values
    df = df.fillna(0)
    
    # Basic data stats
    print(f"\n=== Data Summary ===")
    print(f"Total records: {len(df):,}")
    print(f"Date range: {df['year'].min()}-{df['year'].max()}")
    print("\nNumber of records by disease:")
    print(df['disease'].value_counts())
    
    # Check for extreme values
    print("\n=== Cases Distribution ===")
    print(df['cases'].describe(percentiles=[0.5, 0.75, 0.9, 0.95, 0.99]))
    
    # Cap extreme values at 99.9th percentile
    cases_cap = df['cases'].quantile(0.999)
    print(f"\nCapping cases at {cases_cap:,.2f} (99.9th percentile)")
    df['cases'] = df['cases'].clip(upper=cases_cap)
    
    return df

def create_sequences(df, window_size):
    """Create sequences for LSTM training."""
    print("\n=== Creating Sequences ===")
    
    sequences = []
    targets = []
    
    # Sort by state, disease, year, week
    df = df.sort_values(['state', 'disease', 'year', 'week'])
    
    # Create sequences for each state and disease combination
    for (state, disease), group in df.groupby(['state', 'disease']):
        group = group.sort_values(['year', 'week'])
        
        # Skip if not enough data points
        if len(group) <= window_size:
            continue
            
        # Create sequences
        for i in range(len(group) - window_size):
            seq = group[FEATURES].iloc[i:i+window_size].values
            target = group['cases'].iloc[i+window_size]
            
            # Skip sequences with missing values
            if not np.isnan(seq).any() and not np.isnan(target):
                sequences.append(seq)
                targets.append(target)
    
    print(f"Created {len(sequences)} sequences")
    return np.array(sequences), np.array(targets)

def build_model(input_shape):
    """Build and compile the LSTM model."""
    print("\n=== Building Model ===")
    
    model = Sequential([
        # First LSTM layer
        LSTM(128, 
             input_shape=input_shape,
             return_sequences=True,
             kernel_regularizer=l2(L2_REG),
             recurrent_regularizer=l2(L2_REG)),
        BatchNormalization(),
        Dropout(DROPOUT_RATE),
        
        # Second LSTM layer
        LSTM(64, 
             return_sequences=False,
             kernel_regularizer=l2(L2_REG),
             recurrent_regularizer=l2(L2_REG)),
        BatchNormalization(),
        Dropout(DROPOUT_RATE),
        
        # Dense layers
        Dense(32, activation='relu', kernel_regularizer=l2(L2_REG)),
        BatchNormalization(),
        Dropout(DROPOUT_RATE/2),
        
        # Output layer
        Dense(1, activation='linear')
    ])
    
    # Compile the model
    model.compile(
        optimizer='adam',
        loss='huber',  # More robust to outliers than MSE
        metrics=['mae', 'mse']
    )
    
    model.summary()
    return model

def train_model():
    """Main function to train the model."""
    if not all([TENSORFLOW_AVAILABLE, SKLEARN_AVAILABLE, JOBLIB_AVAILABLE]):
        print("Error: Required dependencies not available.")
        sys.exit(1)
    
    # Create models directory if it doesn't exist
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Load and validate data
    df = load_and_validate_data()
    
    # Create sequences
    X, y = create_sequences(df, WINDOW_SIZE)
    
    # Split into train/validation sets
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=True
    )
    
    print(f"\n=== Data Shapes ===")
    print(f"Training data: {X_train.shape}, {y_train.shape}")
    print(f"Validation data: {X_val.shape}, {y_val.shape}")
    
    # Feature scaling
    print("\n=== Scaling Features ===")
    
    # Reshape for scaling (samples*timesteps, features)
    n_samples, n_timesteps, n_features = X_train.shape
    X_reshaped = X_train.reshape(-1, n_features)
    
    # Scale features
    feature_scaler = RobustScaler()  # More robust to outliers
    X_scaled = feature_scaler.fit_transform(X_reshaped).reshape(X_train.shape)
    
    # Scale the validation set
    X_val_scaled = feature_scaler.transform(
        X_val.reshape(-1, n_features)
    ).reshape(X_val.shape)
    
    # Scale target variable (cases)
    target_scaler = RobustScaler()
    y_scaled = target_scaler.fit_transform(y_train.reshape(-1, 1)).flatten()
    y_val_scaled = target_scaler.transform(y_val.reshape(-1, 1)).flatten()
    
    # Save the scalers
    if JOBLIB_AVAILABLE:
        joblib_dump(feature_scaler, FEATURE_SCALER_PATH)
        joblib_dump(target_scaler, SCALER_PATH)
    
    # Build the model
    model = build_model((WINDOW_SIZE, len(FEATURES)))
    
    # Callbacks
    # Custom callback: compute validation metrics in original units and stop on threshold
    class StopOnRealUnitThreshold(Callback):
        def __init__(self, X_val_scaled, y_val_scaled, target_scaler, threshold: float = REAL_UNIT_THRESHOLD, metric: str = 'mae'):
            super().__init__()
            self.X_val_scaled = X_val_scaled
            self.y_val_scaled = y_val_scaled
            self.target_scaler = target_scaler
            self.threshold = threshold
            self.metric = metric
            self.best_metric = float('inf')

        def on_epoch_end(self, epoch, logs=None):
            logs = logs or {}
            # Predict on validation set
            y_pred_scaled = self.model.predict(self.X_val_scaled, verbose=0).flatten()
            # Inverse transform to original case counts
            y_pred = self.target_scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
            y_true = self.target_scaler.inverse_transform(self.y_val_scaled.reshape(-1, 1)).flatten()

            # Compute MAE and RMSE in original units
            mae = np.mean(np.abs(y_true - y_pred))
            rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

            # Log metrics for visibility
            print(f"\n[RealUnits] val_mae_cases={mae:.2f}, val_rmse_cases={rmse:.2f} (threshold={self.threshold:.2f}, metric={self.metric})")

            # Update best metric
            metric_value = mae if self.metric == 'mae' else rmse
            if metric_value < self.best_metric:
                self.best_metric = metric_value

            # Early stop condition in original units
            if metric_value <= self.threshold:
                print(f"=== Early stop: real-unit {self.metric} <= {self.threshold:.2f} at epoch {epoch+1} ===")
                self.model.stop_training = True

    callbacks = [
        # Keep LR scheduling to help converge
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=PATIENCE//2,
            min_lr=1e-6,
            verbose=1
        ),
        # Stop when real-unit metric threshold is met
        StopOnRealUnitThreshold(
            X_val_scaled=X_val_scaled,
            y_val_scaled=y_val_scaled,
            target_scaler=target_scaler,
            threshold=REAL_UNIT_THRESHOLD,
            metric='mae'
        ),
        # Still save best weights throughout training
        ModelCheckpoint(
            str(MODEL_PATH),
            monitor='val_loss',
            save_best_only=True,
            save_weights_only=False,
            mode='min',
            verbose=1
        )
    ]
    
    # Train the model
    print("\n=== Training Model ===")
    history = model.fit(
        X_scaled, y_scaled,
        validation_data=(X_val_scaled, y_val_scaled),
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1
    )
    
    # Evaluate the model
    print("\n=== Model Evaluation ===")
    train_loss = model.evaluate(X_scaled, y_scaled, verbose=0)
    val_loss = model.evaluate(X_val_scaled, y_val_scaled, verbose=0)
    
    print(f"Training Loss: {train_loss[0]:.4f}, MAE: {train_loss[1]:.4f}, MSE: {train_loss[2]:.4f}")
    print(f"Validation Loss: {val_loss[0]:.4f}, MAE: {val_loss[1]:.4f}, MSE: {val_loss[2]:.4f}")

    # Also report validation metrics in original units
    y_val_pred_scaled = model.predict(X_val_scaled, verbose=0).flatten()
    y_val_pred = target_scaler.inverse_transform(y_val_pred_scaled.reshape(-1, 1)).flatten()
    y_val_true = target_scaler.inverse_transform(y_val_scaled.reshape(-1, 1)).flatten()
    val_mae_cases = np.mean(np.abs(y_val_true - y_val_pred))
    val_rmse_cases = np.sqrt(np.mean((y_val_true - y_val_pred) ** 2))
    print(f"Validation MAE (cases): {val_mae_cases:.2f}, RMSE (cases): {val_rmse_cases:.2f}")
    
    # Make some example predictions
    print("\n=== Example Predictions ===")
    for i in range(3):
        # Get a random validation example
        idx = np.random.randint(len(X_val_scaled))
        x = X_val_scaled[np.newaxis, idx]
        y_true_scaled = y_val_scaled[idx]
        y_pred_scaled = model.predict(x, verbose=0)[0][0]
        
        # Inverse transform
        y_true = target_scaler.inverse_transform([[y_true_scaled]])[0][0]
        y_pred = target_scaler.inverse_transform([[y_pred_scaled]])[0][0]
        
        print(f"\nExample {i+1}:")
        print(f"True: {y_true:.2f}, Predicted: {y_pred:.2f}")
        if y_true > 0:
            print(f"Error: {abs(y_true - y_pred):.2f} ({abs((y_true - y_pred)/y_true*100):.1f}%)")
    
    print("\n=== Training Complete ===")
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Feature scaler saved to: {FEATURE_SCALER_PATH}")
    print(f"Target scaler saved to: {SCALER_PATH}")

if __name__ == "__main__":
    train_model()