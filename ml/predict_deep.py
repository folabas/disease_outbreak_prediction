from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

try:
    from tensorflow.keras.models import load_model
    TENSORFLOW_AVAILABLE = True
except Exception as e:
    print(f"[ERROR] TensorFlow not available: {e}")
    print("Install with: pip install tensorflow")
    TENSORFLOW_AVAILABLE = False

try:
    from joblib import load as joblib_load
    JOBLIB_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Joblib not available: {e}")
    JOBLIB_AVAILABLE = False

try:
    from sklearn.preprocessing import RobustScaler
    SKLEARN_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] scikit-learn not available: {e}")
    SKLEARN_AVAILABLE = False

# Configuration
WINDOW_SIZE = 8  # Must match training configuration
MODEL_PATH = Path("models/lstm_forecaster.h5")
FEATURE_SCALER_PATH = Path("models/feature_scaler.joblib")
TARGET_SCALER_PATH = Path("models/target_scaler.joblib")  # Distinct file for target scaler saved during training
DATA_PATH = Path("data/outbreakiq_training_data_filled.csv")

# Features must match training configuration
FEATURES = [
    "cases",
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "precipitation_sum",
]

def get_week_date_range(year: int, week: int) -> tuple[str, str]:
    """Convert year and week to date range (start and end of week)."""
    first_day = datetime.strptime(f"{year}-W{week-1}-1", "%Y-W%W-%w").date()
    last_day = first_day + timedelta(days=6.9)
    return first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")

def load_scalers():
    """Load the feature and target scalers."""
    if not JOBLIB_AVAILABLE or not SKLEARN_AVAILABLE:
        return None, None
    
    try:
        feature_scaler = joblib_load(FEATURE_SCALER_PATH)
        target_scaler = joblib_load(TARGET_SCALER_PATH)
        return feature_scaler, target_scaler
    except Exception as e:
        print(f"[WARNING] Could not load scalers: {e}")
        return None, None

def prepare_prediction_data(df, window_size):
    """Prepare the most recent window of data for prediction."""
    # Get the latest data point for context
    latest_data = df.sort_values(['state', 'disease', 'year', 'week'])
    latest_data_point = latest_data.iloc[-1]
    
    # Get the most recent sequence
    latest_sequence = latest_data[FEATURES].tail(window_size).values
    
    return latest_sequence, latest_data_point

def main():
    # Check dependencies
    if not TENSORFLOW_AVAILABLE:
        print("[ERROR] Required dependencies not available.")
        sys.exit(1)

    # Check if model exists
    if not MODEL_PATH.exists():
        print(f"[ERROR] Model not found at {MODEL_PATH}. Train it first: python -m ml.train_deep")
        sys.exit(1)

    # Check if data exists
    if not DATA_PATH.exists():
        print(f"[ERROR] Data not found at {DATA_PATH}")
        sys.exit(1)

    # Load and prepare data
    print("\n=== Loading Data ===")
    try:
        df = pd.read_csv(DATA_PATH)
    except Exception as e:
        print(f"[ERROR] Could not read data file: {e}")
        sys.exit(1)
    
    # Ensure required columns exist
    required_cols = FEATURES + ["year", "week", "state", "disease"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(f"[ERROR] Dataset missing required columns: {missing_cols}")
        sys.exit(1)
    
    # Sort and clean data
    df = df.sort_values(["state", "disease", "year", "week"]).reset_index(drop=True)
    df = df.fillna(0)
    
    # Prepare prediction data
    sequence, latest = prepare_prediction_data(df, WINDOW_SIZE)
    
    # Get context
    current_year = int(latest["year"])
    current_week = int(latest["week"])
    state = latest["state"]
    disease = latest["disease"]
    
    # Calculate prediction week
    if current_week == 52:
        pred_year = current_year + 1
        pred_week = 1
    else:
        pred_year = current_year
        pred_week = current_week + 1
    
    # Get date ranges
    current_start, current_end = get_week_date_range(current_year, current_week)
    pred_start, pred_end = get_week_date_range(pred_year, pred_week)
    
    print(f"\n=== Prediction Context ===")
    print(f"Latest data point: Week {current_week}, {current_year} ({current_start} to {current_end})")
    print(f"Location: {state}")
    print(f"Disease: {disease}")
    print(f"\n=== Making Prediction ===")
    print(f"Predicting for: Week {pred_week}, {pred_year} ({pred_start} to {pred_end})")
    
    # Load scalers
    feature_scaler, target_scaler = load_scalers()

    # Ensure correct model input shape (batch, timesteps, features)
    n_timesteps, n_features = sequence.shape

    # Try scaling if a compatible feature scaler is available; always produce 3D input
    if feature_scaler is not None:
        try:
            # Guard against accidentally loading the target scaler (1 feature) as feature scaler
            if hasattr(feature_scaler, "n_features_in_") and feature_scaler.n_features_in_ != n_features:
                raise ValueError(
                    f"Scaler expects {getattr(feature_scaler, 'n_features_in_', 'unknown')} features, "
                    f"but input has {n_features}."
                )

            # Reshape for scaling (timesteps, features) -> (timesteps, features)
            sequence_scaled = feature_scaler.transform(sequence.reshape(-1, n_features))
            sequence_3d = sequence_scaled.reshape(1, WINDOW_SIZE, n_features)
        except Exception as e:
            print(f"[WARNING] Error scaling features: {e}")
            sequence_3d = sequence.reshape(1, WINDOW_SIZE, n_features)
    else:
        sequence_3d = sequence.reshape(1, WINDOW_SIZE, n_features)
    
    # Load model and make prediction
    try:
        model = load_model(MODEL_PATH)
        predicted_scaled = float(model.predict(sequence_3d, verbose=0)[0][0])
        
        # Inverse transform the prediction if we have the target scaler
        if target_scaler is not None:
            # Create a dummy array with the same shape as the scaler expects
            dummy = np.zeros((1, 1))  # Shape: (n_samples, n_features)
            dummy[0, 0] = predicted_scaled
            
            try:
                predicted = target_scaler.inverse_transform(dummy)[0][0]
                predicted = max(0, predicted)  # Ensure non-negative cases
                
                # Print final prediction
                print("\n=== Prediction Result ===")
                print(f"Location: {state}")
                print(f"Disease: {disease}")
                print(f"Prediction for: Week {pred_week}, {pred_year} ({pred_start} to {pred_end})")
                print(f"Predicted cases: {predicted:,.2f}")
                
                # Add context - compare with recent average
                recent_weeks = 4
                if len(df) >= recent_weeks:
                    recent_cases = df["cases"].tail(recent_weeks).mean()
                    print(f"Recent average cases (last {recent_weeks} weeks): {recent_cases:,.2f}")
                    
                    # Calculate percentage change if possible
                    if recent_cases > 0:
                        pct_change = ((predicted - recent_cases) / recent_cases) * 100
                        trend = "increase" if pct_change > 0 else "decrease"
                        print(f"Predicted {trend} of {abs(pct_change):.1f}% from recent average")
                
                # Add confidence interval (example)
                print("\nNote: This is a statistical prediction. Actual values may vary.")
                
            except Exception as e:
                print(f"[WARNING] Could not inverse-transform prediction: {e}")
                print(f"Scaled prediction: {predicted_scaled:.6f}")
        else:
            print(f"\nPredicted (scaled) cases: {predicted_scaled:.6f}")
            print("[INFO] Target scaler not available; showing scaled prediction.")
    
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()