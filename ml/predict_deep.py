from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from tensorflow.keras.models import load_model
    TENSORFLOW_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False

try:
    from joblib import load as joblib_load
    JOBLIB_AVAILABLE = True
except Exception:
    JOBLIB_AVAILABLE = False

WINDOW = 8
MODEL_PATH = Path("models/lstm_forecaster.h5")
SCALER_PATH = Path("models/feature_scaler.joblib")
DATA_PATH = Path("data/outbreakiq_training_data_filled.csv")

FEATURES = [
    "cases",
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "precipitation_sum",
]


def main():
    if not TENSORFLOW_AVAILABLE:
        print("[ERROR] TensorFlow not available. Install with: pip install tensorflow")
        sys.exit(1)

    if not MODEL_PATH.exists():
        print(f"[ERROR] Model not found at {MODEL_PATH}. Train it first: python -m ml.train_deep")
        sys.exit(1)

    if not DATA_PATH.exists():
        print(f"[ERROR] Data not found at {DATA_PATH}. Build it first: python build_features.py")
        sys.exit(1)

    df = pd.read_csv(DATA_PATH)
    df = df.sort_values(["year", "week"]).reset_index(drop=True)

    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        print(f"[ERROR] Dataset missing required features: {missing}")
        sys.exit(1)

    if len(df) < WINDOW:
        print(f"[ERROR] Not enough rows ({len(df)}) to form a window of {WINDOW}")
        sys.exit(1)

    latest = df[FEATURES].tail(WINDOW).fillna(0).values
    latest = np.expand_dims(latest, axis=0)  # shape (1, WINDOW, len(FEATURES))

    model = load_model(MODEL_PATH)
    predicted_scaled = float(model.predict(latest, verbose=0)[0][0])
    print(f"Predicted (scaled) next-week cases: {predicted_scaled:.6f}")

    if JOBLIB_AVAILABLE and SCALER_PATH.exists():
        try:
            scaler = joblib_load(SCALER_PATH)
            # Clamp to [0,1] before inverse-transform to avoid extrapolation
            ps = predicted_scaled
            ps_clamped = min(max(ps, 0.0), 1.0)
            if ps_clamped != ps:
                print(f"[INFO] Clamped scaled prediction from {ps:.6f} to {ps_clamped:.6f}")
            # Inverse transform requires full feature vector; we place the prediction in the cases slot
            inv = scaler.inverse_transform([[ps_clamped, 0, 0, 0]])[0][0]
            print(f"Predicted next-week cases (real scale): {inv:.3f}")
        except Exception as e:
            print(f"[WARN] Could not inverse-transform prediction: {e}")
    else:
        print("[INFO] Scaler not available; skipping inverse-transform to real case counts.")


if __name__ == "__main__":
    main()