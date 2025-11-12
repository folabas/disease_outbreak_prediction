from __future__ import annotations

import sys
from pathlib import Path
import math
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple, List, Dict

try:
    from joblib import load as joblib_load
    JOBLIB_AVAILABLE = True
except Exception:
    JOBLIB_AVAILABLE = False

# Config
DATA_PATH = Path("data/outbreakiq_training_data_filled.csv")
MODEL_PATH = Path("models/lstm_forecaster.h5")
FEATURE_SCALER_PATH = Path("models/feature_scaler.joblib")
TARGET_SCALER_PATH = Path("models/target_scaler.joblib")
REPORTS_DIR = Path("reports/production")
WINDOW_SIZE = 8
FEATURES = [
    "cases",
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "precipitation_sum",
]

def ensure_reports_dir() -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR

def create_sequences_with_meta(df: pd.DataFrame, window_size: int) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
    sequences: List[np.ndarray] = []
    targets: List[float] = []
    meta: List[Dict] = []

    df = df.sort_values(["state", "disease", "year", "week"]).reset_index(drop=True)
    for (state, disease), group in df.groupby(["state", "disease"]):
        group = group.sort_values(["year", "week"]).reset_index(drop=True)
        if len(group) <= window_size:
            continue
        for i in range(len(group) - window_size):
            seq = group[FEATURES].iloc[i:i+window_size].values
            target = float(group["cases"].iloc[i+window_size])
            if not np.isnan(seq).any() and not math.isnan(target):
                sequences.append(seq)
                targets.append(target)
                meta.append({
                    "state": state,
                    "disease": disease,
                    "year": int(group["year"].iloc[i+window_size]),
                    "week": int(group["week"].iloc[i+window_size]),
                })
    return np.array(sequences), np.array(targets), meta

def compute_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae = float(np.mean(np.abs(y_true - y_pred))) if len(y_true) else float("nan")
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2))) if len(y_true) else float("nan")
    # R2
    var = float(np.var(y_true)) if len(y_true) else float("nan")
    r2 = float(1 - np.mean((y_true - y_pred) ** 2) / (np.var(y_true) + 1e-9)) if len(y_true) and var > 0 else float("nan")
    return {"mae": mae, "rmse": rmse, "r2": r2}

def classify_outbreaks(y: np.ndarray, thresholds: Dict[Tuple[str,str], float], meta: List[Dict]) -> np.ndarray:
    labels = []
    for i, m in enumerate(meta):
        key = (m["state"], m["disease"])
        thr = thresholds.get(key, None)
        if thr is None:
            # Fallback to global 75th percentile
            thr = float(np.percentile(y, 75)) if len(y) else 0.0
        labels.append(1 if y[i] >= thr else 0)
    return np.array(labels, dtype=int)

def compute_classification_metrics(y_true_cls: np.ndarray, y_pred_cls: np.ndarray) -> Dict[str, float]:
    tp = int(np.sum((y_true_cls == 1) & (y_pred_cls == 1)))
    fp = int(np.sum((y_true_cls == 0) & (y_pred_cls == 1)))
    fn = int(np.sum((y_true_cls == 1) & (y_pred_cls == 0)))
    precision = tp / (tp + fp + 1e-9)
    recall = tp / (tp + fn + 1e-9)
    f1 = 2 * precision * recall / (precision + recall + 1e-9)
    return {
        "precision": precision * 100.0,
        "recall": recall * 100.0,
        "f1": f1 * 100.0,
    }

def build_thresholds(y_train: np.ndarray, meta_train: List[Dict]) -> Dict[Tuple[str,str], float]:
    # 75th percentile per (state,disease)
    thresholds: Dict[Tuple[str,str], float] = {}
    dfm = pd.DataFrame(meta_train)
    dfm["y"] = y_train
    for (state, disease), group in dfm.groupby(["state", "disease"]):
        if len(group) >= 10:
            thresholds[(state, disease)] = float(np.percentile(group["y"], 75))
    return thresholds

def plot_actual_vs_predicted(df_val_meta: List[Dict], y_true: np.ndarray, y_pred: np.ndarray, state: str, disease: str, out_path: Path) -> bool:
    idx = [i for i, m in enumerate(df_val_meta) if m["state"] == state and m["disease"] == disease]
    if not idx:
        return False
    y_t = y_true[idx]
    y_p = y_pred[idx]
    weeks = [f"{df_val_meta[i]['year']}-W{df_val_meta[i]['week']}" for i in idx]
    plt.figure(figsize=(10, 5))
    plt.plot(weeks, y_t, label="Actual", marker="o")
    plt.plot(weeks, y_p, label="Predicted", marker="x")
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Cases")
    plt.title(f"Actual vs Predicted: {state} - {disease}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    return True

def main():
    # CLI args
    parser = argparse.ArgumentParser(description="OutbreakIQ console report")
    parser.add_argument("--state", type=str, default=None, help="Target state (optional)")
    parser.add_argument("--disease", type=str, default=None, help="Target disease (optional; partial match allowed)")
    args = parser.parse_args()

    ensure_reports_dir()
    # Load data
    if not DATA_PATH.exists():
        print(f"[ERROR] Data not found at {DATA_PATH}")
        sys.exit(1)
    df = pd.read_csv(DATA_PATH).fillna(0)
    # Determine latest context
    df = df.sort_values(["state", "disease", "year", "week"]).reset_index(drop=True)
    # Optional filter by disease/state
    df_ctx = df
    if args.disease:
        df_ctx = df_ctx[df_ctx["disease"].astype(str).str.contains(args.disease, case=False, na=False)]
    if args.state:
        df_ctx = df_ctx[df_ctx["state"].astype(str).str.lower() == args.state.lower()]
    # Fallback if filter yields no rows
    if df_ctx.empty:
        df_ctx = df
    latest = df_ctx.iloc[-1]
    state = str(latest["state"]) 
    disease = str(latest["disease"]) 
    # Latest confirmed and average weekly (last 4 weeks of the same state/disease)
    group = df[(df["state"] == state) & (df["disease"] == disease)].sort_values(["year", "week"]).reset_index(drop=True)
    latest_confirmed = float(group["cases"].iloc[-1]) if len(group) else 0.0
    avg_weekly = float(group["cases"].tail(4).mean()) if len(group) else 0.0

    # Prepare sequences and split train/val similar to training
    X, y, meta = create_sequences_with_meta(df, WINDOW_SIZE)
    if len(X) == 0:
        print("[ERROR] Not enough data to evaluate.")
        sys.exit(1)
    # Simple split (same as train script): 80/20
    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    meta_train, meta_val = meta[:split], meta[split:]

    # Load scalers and model
    if not JOBLIB_AVAILABLE or not FEATURE_SCALER_PATH.exists() or not TARGET_SCALER_PATH.exists():
        print("[ERROR] Scalers not available; train the model first.")
        sys.exit(1)
    feature_scaler = joblib_load(FEATURE_SCALER_PATH)
    target_scaler = joblib_load(TARGET_SCALER_PATH)
    try:
        from tensorflow.keras.models import load_model
    except Exception as e:
        print(f"[ERROR] TensorFlow not available: {e}")
        sys.exit(1)
    if not MODEL_PATH.exists():
        print(f"[ERROR] Model not found at {MODEL_PATH}")
        sys.exit(1)
    model = load_model(MODEL_PATH)

    # Scale features
    n_features = X.shape[-1]
    X_train_scaled = feature_scaler.transform(X_train.reshape(-1, n_features)).reshape(X_train.shape)
    X_val_scaled = feature_scaler.transform(X_val.reshape(-1, n_features)).reshape(X_val.shape)

    # Predict and inverse transform
    y_val_pred_scaled = model.predict(X_val_scaled, verbose=0).flatten()
    y_val_pred = target_scaler.inverse_transform(y_val_pred_scaled.reshape(-1, 1)).flatten()
    # y_val is already in real units from the dataset; do NOT inverse-transform
    y_val_true = y_val.astype(float)
    # Clamp negatives in predictions
    y_val_pred = np.maximum(0.0, y_val_pred)

    # Regression metrics
    reg_metrics = compute_regression_metrics(y_val_true, y_val_pred)

    # Classification metrics (outbreak if >= 75th percentile per state/disease from train)
    thresholds = build_thresholds(y_train, meta_train)
    y_true_cls = classify_outbreaks(y_val_true, thresholds, meta_val)
    y_pred_cls = classify_outbreaks(y_val_pred, thresholds, meta_val)
    cls_metrics = compute_classification_metrics(y_true_cls, y_pred_cls)

    # Risk level based on predicted vs thresholds for latest context
    key = (state, disease)
    thr_latest = thresholds.get(key, float(np.percentile(y_train, 75)))
    # Predict next week for latest context window
    latest_window = group[FEATURES].tail(WINDOW_SIZE).values
    # Pad sequence if fewer than WINDOW_SIZE rows exist
    if latest_window.shape[0] < WINDOW_SIZE:
        if latest_window.shape[0] == 0:
            # No data for this context; fall back to global recent window
            fallback = df[FEATURES].tail(WINDOW_SIZE).values
            latest_window = fallback
        else:
            pad_rows = WINDOW_SIZE - latest_window.shape[0]
            pad = np.repeat(latest_window[[-1], :], pad_rows, axis=0)
            latest_window = np.vstack([latest_window, pad])
    latest_window_scaled = feature_scaler.transform(latest_window.reshape(-1, n_features)).reshape(1, WINDOW_SIZE, n_features)
    pred_next_scaled = float(model.predict(latest_window_scaled, verbose=0)[0][0])
    pred_next = float(target_scaler.inverse_transform(np.array([[pred_next_scaled]]))[0][0])
    pred_next = max(0.0, pred_next)

    risk_level = (
        "Low" if pred_next < 0.5 * thr_latest else
        "Moderate" if pred_next < thr_latest else
        "High" if pred_next < 1.5 * thr_latest else
        "Severe"
    )
    # Confidence from residuals on val for this state/disease
    idx_sd = [i for i, m in enumerate(meta_val) if m["state"] == state and m["disease"] == disease]
    if idx_sd:
        mae_sd = float(np.mean(np.abs(y_val_true[idx_sd] - y_val_pred[idx_sd])))
        # Use recent variability and threshold as baseline scale
        std_recent = float(group["cases"].tail(8).std() or 0.0)
        baseline = max(std_recent, thr_latest / 4.0, 1.0)
        conf = 100.0 * (1.0 - mae_sd / (baseline + 1e-6))
    else:
        # Fall back to global validation residuals and variability
        std_global = float(np.std(y_val_true) or 0.0)
        baseline = max(std_global, np.percentile(y_train, 75) / 4.0, 1.0)
        conf = 100.0 * (1.0 - reg_metrics["mae"] / (baseline + 1e-6))
    conf = float(max(0.0, min(100.0, conf)))

    # Chart
    chart_path = ensure_reports_dir() / "actual_vs_predicted.png"
    chart_ok = plot_actual_vs_predicted(meta_val, y_val_true, y_val_pred, state, disease, chart_path)

    # Console output
    print("\n=== Console Report ===")
    print(f"Context: {state} - {disease}")
    print(f"Latest Confirmed Cases: {latest_confirmed:.0f}")
    print(f"Average Weekly Cases (last 4): {avg_weekly:.0f}")
    print(f"Predicted Next Week: {pred_next:.0f}")
    print(f"Risk Level: {risk_level}")
    print(f"Confidence: {conf:.1f}%")
    print("\nModel Accuracy (Validation)")
    print(f"MAE: {reg_metrics['mae']:.2f} cases, RMSE: {reg_metrics['rmse']:.2f} cases, R2: {reg_metrics['r2']:.3f}")
    print(f"Precision: {cls_metrics['precision']:.1f}% | Recall: {cls_metrics['recall']:.1f}% | F1: {cls_metrics['f1']:.1f}%")
    if chart_ok:
        print(f"Chart saved: {chart_path}")
    else:
        print("Chart: not enough validation points for this context; skipped.")

if __name__ == "__main__":
    main()