from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from tensorflow.keras.models import load_model
    TENSORFLOW_AVAILABLE = True
except Exception as e:
    print(f"[ERROR] TensorFlow not available: {e}")
    TENSORFLOW_AVAILABLE = False

try:
    from joblib import load as joblib_load
    JOBLIB_AVAILABLE = True
except Exception:
    JOBLIB_AVAILABLE = False

try:
    from ml.features import FEATURES
except ImportError:
    from features import FEATURES  # type: ignore

# Configuration
WINDOW_SIZE = 8
BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "models" / "lstm_forecaster.h5"
FEATURE_SCALER_PATH = BASE_DIR / "models" / "feature_scaler.joblib"
TARGET_SCALER_PATH = BASE_DIR / "models" / "target_scaler.joblib"
DATA_PATH = BASE_DIR / "data" / "outbreak_dataset.csv"
REPORTS_DIR = BASE_DIR / "reports"


def load_scalers():
    """Load the feature and target scalers."""
    if not JOBLIB_AVAILABLE:
        return None, None
    
    try:
        feature_scaler = joblib_load(FEATURE_SCALER_PATH)
        target_scaler = joblib_load(TARGET_SCALER_PATH)
        return feature_scaler, target_scaler
    except Exception as e:
        print(f"[WARNING] Could not load scalers: {e}")
        return None, None


def create_sequences_for_evaluation(df, window_size):
    """Create sequences from the dataset for evaluation."""
    sequences = []
    targets = []
    metadata = []
    
    # Sort by state, disease, year, week
    df = df.sort_values(['state', 'disease', 'year', 'week']).reset_index(drop=True)
    
    # Group by state and disease
    for (state, disease), group in df.groupby(['state', 'disease']):
        if len(group) <= window_size:
            continue
        
        # Create sequences
        for i in range(len(group) - window_size):
            seq = group[FEATURES].iloc[i:i+window_size].values
            target = group['cases'].iloc[i+window_size]
            
            # Check for NaN
            if not np.isnan(seq.astype(float)).any() and not np.isnan(target):
                sequences.append(seq)
                targets.append(target)
                metadata.append({
                    'state': state,
                    'disease': disease,
                    'year': int(group['year'].iloc[i+window_size]),
                    'week': int(group['week'].iloc[i+window_size])
                })
    
    return np.array(sequences), np.array(targets), metadata


def evaluate_model():
    """Evaluate the trained model on test data."""
    print("\n" + "="*60)
    print("MODEL EVALUATION")
    print("="*60)
    
    # Check dependencies
    if not TENSORFLOW_AVAILABLE or not JOBLIB_AVAILABLE:
        print("[ERROR] Required dependencies not available.")
        return
    
    # Load data
    print("\n[1/5] Loading dataset...")
    try:
        df = pd.read_csv(DATA_PATH)
        print(f"   ✓ Loaded {len(df):,} rows")
    except Exception as e:
        print(f"[ERROR] Could not read data: {e}")
        return
    
    # Ensure all features exist
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        print(f"   ⚠ Missing columns: {missing}. Filling with zeros.")
        for col in missing:
            df[col] = 0.0
    
    # Clean data: replace inf and NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(0)
    
    print(f"   ✓ Data cleaned")
    
    # Create sequences
    print("\n[2/5] Creating evaluation sequences...")
    X, y, metadata = create_sequences_for_evaluation(df, WINDOW_SIZE)
    print(f"   ✓ Created {len(X):,} sequences")
    
    # Split into train/test (use last 20% as test)
    test_size = int(len(X) * 0.2)
    X_test = X[-test_size:]
    y_test = y[-test_size:]
    metadata_test = metadata[-test_size:]
    
    print(f"   ✓ Test set: {len(X_test):,} samples")
    
    # Load scalers
    print("\n[3/5] Loading scalers...")
    feature_scaler, target_scaler = load_scalers()
    if feature_scaler is None or target_scaler is None:
        print("[ERROR] Could not load scalers")
        return
    print("   ✓ Scalers loaded")
    
    # Scale features
    print("\n[4/5] Scaling features...")
    X_test_scaled = feature_scaler.transform(
        X_test.reshape(-1, len(FEATURES))
    ).reshape(X_test.shape)
    
    # Scale targets
    y_test_scaled = target_scaler.transform(y_test.reshape(-1, 1)).flatten()
    print("   ✓ Features scaled")
    
    # Load model and predict
    print("\n[5/5] Making predictions...")
    try:
        model = load_model(MODEL_PATH)
        y_pred_scaled = model.predict(X_test_scaled, verbose=0).flatten()
        
        # Inverse transform predictions
        y_pred = target_scaler.inverse_transform(
            y_pred_scaled.reshape(-1, 1)
        ).flatten()
        y_pred = np.maximum(y_pred, 0)  # Ensure non-negative
        
        print("   ✓ Predictions complete")
        
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        return
    
    # Calculate metrics
    print("\n" + "="*60)
    print("EVALUATION METRICS")
    print("="*60)
    
    # Overall metrics
    mae = np.mean(np.abs(y_test - y_pred))
    mse = np.mean((y_test - y_pred) ** 2)
    rmse = np.sqrt(mse)
    
    # R² score
    ss_res = np.sum((y_test - y_pred) ** 2)
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # MAPE (avoid division by zero)
    mask = y_test > 0
    mape = np.mean(np.abs((y_test[mask] - y_pred[mask]) / y_test[mask])) * 100 if mask.any() else 0
    
    print(f"\n📊 Overall Performance:")
    print(f"   MAE (Mean Absolute Error):  {mae:.2f} cases")
    print(f"   RMSE (Root Mean Squared):   {rmse:.2f} cases")
    print(f"   R² Score:                   {r2:.4f}")
    print(f"   MAPE:                       {mape:.2f}%")
    
    # Per-disease metrics
    print(f"\n📊 Per-Disease Performance:")
    diseases = set([m['disease'] for m in metadata_test])
    
    for disease in sorted(diseases):
        disease_mask = [m['disease'] == disease for m in metadata_test]
        if not any(disease_mask):
            continue
        
        y_disease = y_test[disease_mask]
        y_pred_disease = y_pred[disease_mask]
        
        mae_disease = np.mean(np.abs(y_disease - y_pred_disease))
        rmse_disease = np.sqrt(np.mean((y_disease - y_pred_disease) ** 2))
        
        print(f"   {disease.capitalize():12s} - MAE: {mae_disease:6.2f}, RMSE: {rmse_disease:6.2f}")
    
    # Sample predictions
    print(f"\n📋 Sample Predictions (first 10):")
    print(f"{'State':<12} {'Disease':<10} {'Year':<6} {'Week':<6} {'Actual':>8} {'Predicted':>10} {'Error':>8}")
    print("-" * 70)
    
    for i in range(min(10, len(y_test))):
        meta = metadata_test[i]
        actual = y_test[i]
        predicted = y_pred[i]
        error = actual - predicted
        
        print(f"{meta['state']:<12} {meta['disease']:<10} {meta['year']:<6} "
              f"{meta['week']:<6} {actual:8.1f} {predicted:10.1f} {error:8.1f}")
    
    # Save results
    REPORTS_DIR.mkdir(exist_ok=True)
    results_df = pd.DataFrame({
        'state': [m['state'] for m in metadata_test],
        'disease': [m['disease'] for m in metadata_test],
        'year': [m['year'] for m in metadata_test],
        'week': [m['week'] for m in metadata_test],
        'actual_cases': y_test,
        'predicted_cases': y_pred,
        'error': y_test - y_pred,
        'abs_error': np.abs(y_test - y_pred)
    })
    
    output_path = REPORTS_DIR / f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    results_df.to_csv(output_path, index=False)
    print(f"\n💾 Results saved to: {output_path}")
    
    # Summary statistics
    print(f"\n📈 Summary Statistics:")
    print(f"   Total predictions:          {len(y_test):,}")
    print(f"   Average actual cases:       {np.mean(y_test):.2f}")
    print(f"   Average predicted cases:    {np.mean(y_pred):.2f}")
    print(f"   Std dev (actual):           {np.std(y_test):.2f}")
    print(f"   Std dev (predicted):        {np.std(y_pred):.2f}")
    
    print("\n" + "="*60)
    print("✅ EVALUATION COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    evaluate_model()
