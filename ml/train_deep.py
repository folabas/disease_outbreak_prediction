from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from pathlib import Path

try:
    from sklearn.preprocessing import MinMaxScaler
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

# Optional: persist scaler for inverse transforms at inference time
try:
    from joblib import dump as joblib_dump
    JOBLIB_AVAILABLE = True
except Exception:
    JOBLIB_AVAILABLE = False

try:
    # TensorFlow is heavy; import guarded
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False


DATA_PATH = Path("data/outbreakiq_training_data_filled.csv")
MODEL_PATH = Path("models/lstm_forecaster.h5")
SCALER_PATH = Path("models/feature_scaler.joblib")


FEATURES = [
    "cases",
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "precipitation_sum",
]


def make_sequences(df: pd.DataFrame, window: int = 8) -> tuple[np.ndarray, np.ndarray]:
    """Generate sequence samples (X, y) for each (state, disease).

    X: [num_samples, window, num_features]
    y: [num_samples]
    """
    X, y = [], []
    for (disease, state), g in df.groupby(["disease", "state"], sort=False):
        g = g.sort_values(["year", "week"]).reset_index(drop=True)
        vals = g[FEATURES].fillna(0).values
        for i in range(window, len(vals)):
            X.append(vals[i - window : i])
            y.append(vals[i, 0])  # next week’s cases at index i
    if not X:
        return np.empty((0, window, len(FEATURES))), np.empty((0,))
    return np.array(X), np.array(y)


def main():
    print("=== Training LSTM Deep Model ===")

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"{DATA_PATH} not found!")

    df = pd.read_csv(DATA_PATH)
    print(f"[INFO] Loaded dataset: {df.shape[0]} rows, {df.shape[1]} cols")

    # Ensure required columns
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required features: {missing}")

    if not SKLEARN_AVAILABLE:
        print("[WARN] scikit-learn not available; proceeding without scaling.")
        scaled = df[FEATURES].fillna(0).values
    else:
        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(df[FEATURES].fillna(0))
        df.loc[:, FEATURES] = scaled
        # Persist scaler for later inverse transformation of predictions
        try:
            if JOBLIB_AVAILABLE:
                SCALER_PATH.parent.mkdir(parents=True, exist_ok=True)
                joblib_dump(scaler, SCALER_PATH)
                print(f"[INFO] Saved feature scaler to {SCALER_PATH}")
            else:
                print("[WARN] joblib not available; scaler will not be saved.")
        except Exception as e:
            print(f"[WARN] Failed to save scaler: {e}")

    if not TENSORFLOW_AVAILABLE:
        print("[ERROR] TensorFlow not available. Install with: pip install tensorflow")
        sys.exit(1)

    X, y = make_sequences(df, window=8)
    print(f"[INFO] Generated {len(X)} sequences of shape {X.shape[1:]} from {len(df)} rows")

    if len(X) == 0:
        print("[ERROR] Not enough sequential data to form training windows. Add more weeks per state/disease.")
        sys.exit(1)

    model = Sequential([
        LSTM(64, input_shape=(X.shape[1], X.shape[2]), return_sequences=False),
        Dropout(0.3),
        Dense(32, activation="relu"),
        Dense(1),
    ])
    model.compile(optimizer="adam", loss="mae")
    model.summary()

    es = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
    history = model.fit(
        X, y,
        validation_split=0.1,
        epochs=100,
        batch_size=32,
        callbacks=[es],
        verbose=1,
    )

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(MODEL_PATH)
    print(f"✅ Model trained and saved as {MODEL_PATH}")

    # Optional: simple training summary
    metrics = {
        "timestamp": int(time.time()),
        "samples": int(len(X)),
        "window": 8,
        "features": FEATURES,
        "final_val_loss": float(history.history.get("val_loss", [np.nan])[-1]),
    }
    print("[SUMMARY]", metrics)


if __name__ == "__main__":
    main()