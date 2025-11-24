from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime

# IMPORTS
try:
    from sklearn.preprocessing import RobustScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

try:
    from joblib import dump as joblib_dump
    JOBLIB_AVAILABLE = True
except Exception:
    JOBLIB_AVAILABLE = False

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import ReduceLROnPlateau, ModelCheckpoint, Callback, TensorBoard
    from tensorflow.keras.regularizers import l2
    TENSORFLOW_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False


# CONFIGURATION
# Use absolute paths from project root
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "outbreak_dataset.csv"
MODEL_PATH = BASE_DIR / "models" / "lstm_forecaster.h5"
FEATURE_SCALER_PATH = BASE_DIR / "models" / "feature_scaler.joblib"
TARGET_SCALER_PATH = BASE_DIR / "models" / "target_scaler.joblib"
LOGS_DIR = BASE_DIR / "logs" / "fit"

WINDOW_SIZE = 8
BATCH_SIZE = 32
EPOCHS = 100
PATIENCE = 15
DROPOUT_RATE = 0.3
L2_REG = 0.01
REAL_UNIT_THRESHOLD = 15.0


try:
    from .features import FEATURES, DISEASE_COLUMNS
except ImportError:  # Allows running as a script (python ml/train_deep.py)
    from features import FEATURES, DISEASE_COLUMNS  # type: ignore


# LOAD & CLEAN DATA
def load_and_prepare_data():

    print("\n=== Loading Training Dataset ===")

    if not DATA_PATH.exists():
        print(f"❌ ERROR: Dataset not found at {DATA_PATH}")
        sys.exit(1)

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df):,} rows.")

    # Preserve original disease label for evaluation/reporting
    if "disease" in df.columns and "disease_label" not in df.columns:
        df["disease_label"] = df["disease"]

    # Drop NaN rows and handle infinite values
    df = df.replace([np.inf, -np.inf], np.nan).dropna()

    # One-hot encode disease
    print("\n=== Encoding Disease Types ===")
    df = pd.get_dummies(df, columns=["disease"], prefix="disease")

    # Restore disease label column name for downstream grouping logic
    if "disease_label" in df.columns:
        df = df.rename(columns={"disease_label": "disease"})

    # Ensure all disease columns exist
    for d in ["disease_cholera", "disease_malaria", "disease_ebola", "disease_covid"]:
        if d not in df.columns:
            df[d] = 0.0

    # Ensure all feature columns exist (be tolerant and create missing with safe defaults)
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        print("\n⚠ WARNING: Missing feature columns detected:", missing)
        print("They will be created with default value 0.0 so reporting/evaluation can run.")
        for col in missing:
            df[col] = 0.0

    # Clip extreme cases
    df["cases"] = df["cases"].clip(upper=df["cases"].quantile(0.999))

    return df



# CREATE SEQUENCES
def create_sequences(df):

    print("\n=== Creating LSTM Sequences ===")

    sequences = []
    targets = []

    df = df.sort_values(["state", "year", "week"])

    group_cols = ["state", "disease_cholera", "disease_malaria", "disease_ebola", "disease_covid"]

    for keys, group in df.groupby(group_cols):

        if len(group) <= WINDOW_SIZE:
            continue

        for i in range(len(group) - WINDOW_SIZE):
            seq = group[FEATURES].iloc[i:i+WINDOW_SIZE].values
            target = group["cases"].iloc[i+WINDOW_SIZE]
            
            # Check for NaN values in numeric columns only
            if not np.isnan(seq.astype(float)).any():
                sequences.append(seq)
                targets.append(target)

    sequences = np.array(sequences)
    targets = np.array(targets)

    print(f"Total sequences: {len(sequences):,}")
    return sequences, targets



# BUILD NEURAL NETWORK
def build_model(input_shape):

    print("\n=== Building Multi-Disease LSTM Model ===")

    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=input_shape,
             kernel_regularizer=l2(L2_REG)),
        BatchNormalization(),
        Dropout(DROPOUT_RATE),

        LSTM(64, return_sequences=False, kernel_regularizer=l2(L2_REG)),
        BatchNormalization(),
        Dropout(DROPOUT_RATE),

        Dense(64, activation="relu"),
        BatchNormalization(),
        Dropout(0.25),

        Dense(1, activation="linear")
    ])

    model.compile(
        optimizer="adam",
        loss="huber",
        metrics=["mae", "mse", "mape"]  # Added MAPE for percentage error tracking
    )

    model.summary()
    return model



# TRAINING FUNCTION
def train_model():

    if not TENSORFLOW_AVAILABLE:
        print("❌ ERROR: TensorFlow not installed")
        return

    df = load_and_prepare_data()

    # Build sequences
    X, y = create_sequences(df)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, shuffle=True, random_state=42
    )

    # Scaling (3D → 2D → 3D)
    feature_scaler = RobustScaler()
    X_train_scaled = feature_scaler.fit_transform(
        X_train.reshape(-1, len(FEATURES))
    ).reshape(X_train.shape)

    X_val_scaled = feature_scaler.transform(
        X_val.reshape(-1, len(FEATURES))
    ).reshape(X_val.shape)

    target_scaler = RobustScaler()
    y_train_scaled = target_scaler.fit_transform(y_train.reshape(-1, 1)).flatten()
    y_val_scaled = target_scaler.transform(y_val.reshape(-1, 1)).flatten()

    # Save scalers
    joblib_dump(feature_scaler, FEATURE_SCALER_PATH)
    joblib_dump(target_scaler, TARGET_SCALER_PATH)

    # Build model
    model = build_model((WINDOW_SIZE, len(FEATURES)))

    # Create timestamped log directory for TensorBoard
    log_dir = LOGS_DIR / datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n=== TensorBoard Logging ===")
    print(f"Logs will be saved to: {log_dir}")
    print(f"To view TensorBoard, run: tensorboard --logdir {LOGS_DIR}")

    # Callbacks with TensorBoard integration
    callbacks = [
        # TensorBoard callback with comprehensive logging
        TensorBoard(
            log_dir=str(log_dir),
            histogram_freq=1,  # Log weight histograms every epoch
            write_graph=True,  # Visualize model graph
            write_images=False,  # Don't write model weights as images (can be large)
            update_freq='epoch',  # Update metrics every epoch
            profile_batch=0,  # Disable profiling to avoid overhead
            embeddings_freq=0  # Disable embeddings (not applicable here)
        ),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, verbose=1),
        ModelCheckpoint(str(MODEL_PATH), save_best_only=True, monitor="val_loss", verbose=1)
    ]

    # Train
    print("\n=== Training LSTM ===")
    model.fit(
        X_train_scaled, y_train_scaled,
        validation_data=(X_val_scaled, y_val_scaled),
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1
    )

    print("\n=== Training Finished ===")
    print(f"Model saved to: {MODEL_PATH}")
    print(f"\n=== View Training Metrics in TensorBoard ===")
    print(f"Run this command to launch TensorBoard:")
    print(f"  tensorboard --logdir {LOGS_DIR}")
    print(f"\nThen open your browser to: http://localhost:6006")
    print(f"\nAvailable visualizations:")
    print(f"  • Scalars: Loss, MAE, MSE, MAPE over epochs")
    print(f"  • Graphs: Model architecture and layer connections")
    print(f"  • Histograms: Weight and bias distributions")
    print(f"  • Distributions: Weight distribution changes over time")
    
    # Track model version with dataset version
    try:
        from .data_versioning import track_model_version, get_dataset_version
        
        # Track dataset version
        dataset_version = get_dataset_version("outbreak_dataset")
        dataset_versions = {}
        if dataset_version:
            dataset_versions["outbreak_dataset"] = dataset_version.get("hash", "unknown")
        
        # Track model version
        model_version = track_model_version("lstm_forecaster", MODEL_PATH, dataset_versions)
        if model_version:
            print(f"Model version tracked: v{model_version.get('version', 1)}")
    except Exception as e:
        print(f"[WARNING] Could not track model version: {e}")


# ENTRY POINT
if __name__ == "__main__":
    train_model()
