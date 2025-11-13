from __future__ import annotations

import sys
from pathlib import Path
import math
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple, List, Dict
from datetime import datetime

try:
    from joblib import load as joblib_load
    JOBLIB_AVAILABLE = True
except Exception:
    JOBLIB_AVAILABLE = False

# Config
DATA_PATH = Path("data/evaluation_merged_clean.csv")
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

def classify_outbreaks(y: np.ndarray, thresholds: Dict[Tuple[str,str], float], meta: List[Dict], global75: float) -> np.ndarray:
    labels = []
    for i, m in enumerate(meta):
        key = (m["state"], m["disease"])
        thr = thresholds.get(key, global75)
        labels.append(1 if y[i] >= thr else 0)
    return np.array(labels, dtype=int)

def compute_classification_metrics(y_true_cls: np.ndarray, y_pred_cls: np.ndarray) -> Dict[str, float]:
    tp = int(np.sum((y_true_cls == 1) & (y_pred_cls == 1)))
    fp = int(np.sum((y_true_cls == 0) & (y_pred_cls == 1)))
    fn = int(np.sum((y_true_cls == 1) & (y_pred_cls == 0)))
    if (tp + fp) == 0:
        precision = float("nan")
    else:
        precision = tp / (tp + fp)
    if (tp + fn) == 0:
        recall = float("nan")
    else:
        recall = tp / (tp + fn)
    if math.isnan(precision) or math.isnan(recall):
        f1 = float("nan")
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "precision": (precision * 100.0) if not math.isnan(precision) else float("nan"),
        "recall": (recall * 100.0) if not math.isnan(recall) else float("nan"),
        "f1": (f1 * 100.0) if not math.isnan(f1) else float("nan"),
    }

def compute_accuracy_and_weighted(y_true_cls: np.ndarray, y_pred_cls: np.ndarray) -> Dict[str, object]:
    total = int(len(y_true_cls))
    tp = int(np.sum((y_true_cls == 1) & (y_pred_cls == 1)))
    tn = int(np.sum((y_true_cls == 0) & (y_pred_cls == 0)))
    fp = int(np.sum((y_true_cls == 0) & (y_pred_cls == 1)))
    fn = int(np.sum((y_true_cls == 1) & (y_pred_cls == 0)))
    acc = ((tp + tn) / (total + 1e-9)) * 100.0
    # Positive class metrics
    prec_pos = (tp / (tp + fp + 1e-9)) * 100.0 if (tp + fp) > 0 else float("nan")
    rec_pos = (tp / (tp + fn + 1e-9)) * 100.0 if (tp + fn) > 0 else float("nan")
    f1_pos = (2 * (prec_pos/100.0) * (rec_pos/100.0) / ((prec_pos/100.0) + (rec_pos/100.0) + 1e-9)) * 100.0 if not math.isnan(prec_pos) and not math.isnan(rec_pos) else float("nan")
    # Negative class metrics
    prec_neg = (tn / (tn + fn + 1e-9)) * 100.0 if (tn + fn) > 0 else float("nan")
    rec_neg = (tn / (tn + fp + 1e-9)) * 100.0 if (tn + fp) > 0 else float("nan")
    f1_neg = (2 * (prec_neg/100.0) * (rec_neg/100.0) / ((prec_neg/100.0) + (rec_neg/100.0) + 1e-9)) * 100.0 if not math.isnan(prec_neg) and not math.isnan(rec_neg) else float("nan")
    support_pos = tp + fn
    support_neg = tn + fp
    total_support = support_pos + support_neg
    if support_pos == 0 or support_neg == 0:
        weighted = {"precision": float("nan"), "recall": float("nan"), "f1": float("nan")}
    else:
        weighted = {
            "precision": (prec_pos * (support_pos/total_support) + prec_neg * (support_neg/total_support)),
            "recall": (rec_pos * (support_pos/total_support) + rec_neg * (support_neg/total_support)),
            "f1": (f1_pos * (support_pos/total_support) + f1_neg * (support_neg/total_support)),
        }
    return {
        "accuracy": acc,
        "per_class": {0: {"precision": prec_neg, "recall": rec_neg, "f1": f1_neg}, 1: {"precision": prec_pos, "recall": rec_pos, "f1": f1_pos}},
        "weighted": weighted,
        "supports": {0: support_neg, 1: support_pos},
        "cm": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
    }

def compute_roc_auc(scores: np.ndarray, labels: np.ndarray) -> Dict[str, object]:
    if len(scores) == 0:
        return {"fpr": np.array([]), "tpr": np.array([]), "auc": float("nan")}
    order = np.argsort(-scores)
    s = scores[order]
    l = labels[order]
    P = float(np.sum(l == 1))
    N = float(np.sum(l == 0))
    if P == 0 or N == 0:
        return {"fpr": np.array([]), "tpr": np.array([]), "auc": float("nan")}
    tpr = []
    fpr = []
    tp = 0.0
    fp = 0.0
    prev = None
    for i in range(len(s)):
        if prev is None or s[i] != prev:
            tpr.append(tp / P)
            fpr.append(fp / N)
            prev = s[i]
        if l[i] == 1:
            tp += 1.0
        else:
            fp += 1.0
    tpr.append(tp / P)
    fpr.append(fp / N)
    fpr_arr = np.array(fpr)
    tpr_arr = np.array(tpr)
    auc = float(np.trapz(tpr_arr, fpr_arr))
    return {"fpr": fpr_arr, "tpr": tpr_arr, "auc": auc}

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
    plt.savefig(out_path, dpi=200)
    plt.close()
    return True

def evaluate_per_disease(df: pd.DataFrame) -> pd.DataFrame:
    ensure_reports_dir()
    X, y, meta = create_sequences_with_meta(df, WINDOW_SIZE)
    if len(X) == 0:
        return pd.DataFrame()
    feature_scaler = None
    target_scaler = None
    model = None
    if JOBLIB_AVAILABLE and FEATURE_SCALER_PATH.exists() and TARGET_SCALER_PATH.exists() and MODEL_PATH.exists():
        feature_scaler = joblib_load(FEATURE_SCALER_PATH)
        target_scaler = joblib_load(TARGET_SCALER_PATH)
        from tensorflow.keras.models import load_model
        model = load_model(MODEL_PATH)
    n_features = X.shape[-1]
    diseases = sorted(set(str(d) for d in df["disease"].dropna().unique()))
    rows = []
    ts = datetime.utcnow().isoformat()
    model_version = "lstm_forecaster"
    for disease in diseases:
        idx_all = [i for i, m in enumerate(meta) if m["disease"] == disease]
        if not idx_all:
            rows.append({
                "disease": disease,
                "sample_size": 0,
                "positive": 0,
                "negative": 0,
                "accuracy_pct": None,
                "precision_weighted_pct": None,
                "recall_weighted_pct": None,
                "f1_weighted_pct": None,
                "precision_pos_pct": None,
                "recall_pos_pct": None,
                "f1_pos_pct": None,
                "precision_neg_pct": None,
                "recall_neg_pct": None,
                "f1_neg_pct": None,
                "auc": None,
                "timestamp": ts,
                "model_version": model_version,
                "roc_path": "",
                "chart_path": "",
            })
            continue
        split_d = max(1, int(len(idx_all) * 0.8))
        idx_train_d = idx_all[:split_d]
        idx_val_d = idx_all[split_d:]
        if not idx_val_d:
            rows.append({
                "disease": disease,
                "sample_size": 0,
                "positive": 0,
                "negative": 0,
                "accuracy_pct": None,
                "precision_weighted_pct": None,
                "recall_weighted_pct": None,
                "f1_weighted_pct": None,
                "precision_pos_pct": None,
                "recall_pos_pct": None,
                "f1_pos_pct": None,
                "precision_neg_pct": None,
                "recall_neg_pct": None,
                "f1_neg_pct": None,
                "auc": None,
                "timestamp": ts,
                "model_version": model_version,
                "roc_path": "",
                "chart_path": "",
            })
            continue
        X_train_d = X[idx_train_d]
        y_train_d = y[idx_train_d]
        meta_train_d = [meta[i] for i in idx_train_d]
        X_val_d = X[idx_val_d]
        y_val_d = y[idx_val_d]
        meta_val_d = [meta[i] for i in idx_val_d]
        global75_d = float(np.percentile(y_train_d, 75)) if len(y_train_d) else 0.0
        if model is not None and feature_scaler is not None and target_scaler is not None:
            X_val_scaled_d = feature_scaler.transform(X_val_d.reshape(-1, n_features)).reshape(X_val_d.shape)
            y_val_pred_scaled_d = model.predict(X_val_scaled_d, verbose=0).flatten()
            y_val_pred_d = target_scaler.inverse_transform(y_val_pred_scaled_d.reshape(-1, 1)).flatten()
        else:
            y_val_pred_d = X_val_d[:, -1, 0].astype(float)
        y_val_true_d = y_val_d.astype(float)
        y_val_pred_d = np.maximum(0.0, y_val_pred_d)
        thresholds_d = build_thresholds(y_train_d, meta_train_d)
        thr_list = []
        for j in range(len(meta_val_d)):
            key = (meta_val_d[j]["state"], meta_val_d[j]["disease"])
            thr_list.append(thresholds_d.get(key, global75_d))
        y_true_cls = np.array([1 if y_val_true_d[j] >= thr_list[j] else 0 for j in range(len(meta_val_d))])
        y_pred_cls = np.array([1 if y_val_pred_d[j] >= thr_list[j] else 0 for j in range(len(meta_val_d))])
        pos = int(np.sum(y_true_cls == 1))
        neg = int(np.sum(y_true_cls == 0))
        viable = (len(meta_val_d) >= 50) and (pos > 0) and (neg > 0)
        if viable:
            cls = compute_classification_metrics(y_true_cls, y_pred_cls)
            acc_w = compute_accuracy_and_weighted(y_true_cls, y_pred_cls)
            roc = compute_roc_auc(y_val_pred_d, y_true_cls)
        else:
            cls = {"precision": float("nan"), "recall": float("nan"), "f1": float("nan")}
            acc_w = {"accuracy": float("nan"), "per_class": {0: {"precision": float("nan"), "recall": float("nan"), "f1": float("nan")}, 1: {"precision": float("nan"), "recall": float("nan"), "f1": float("nan")}}, "weighted": {"precision": float("nan"), "recall": float("nan"), "f1": float("nan")}, "supports": {0: neg, 1: pos}, "cm": {"tp": 0, "tn": 0, "fp": 0, "fn": 0}}
            roc = {"fpr": np.array([]), "tpr": np.array([]), "auc": float("nan")}
        states_d = [m["state"] for m in meta_val_d]
        weeks_d = [f"{m['year']}-W{m['week']}" for m in meta_val_d]
        chart_path = REPORTS_DIR / f"actual_vs_predicted_{disease}.png"
        plt.figure(figsize=(10, 5))
        colors = ["green" if y_true_cls[j] == y_pred_cls[j] else "red" for j in range(len(meta_val_d))]
        plt.scatter(weeks_d, y_val_true_d, label="Actual", marker="o", c="blue")
        plt.scatter(weeks_d, y_val_pred_d, label="Predicted", marker="x", c=colors)
        plt.xticks(rotation=45, ha='right')
        plt.ylabel("Cases")
        plt.title(f"Actual vs Predicted: {disease}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(chart_path, dpi=200)
        plt.close()
        roc_path = REPORTS_DIR / f"roc_{disease}.png"
        if roc["fpr"].size == 0 or math.isnan(float(roc["auc"])):
            plt.figure(figsize=(6, 6))
            plt.text(0.5, 0.5, "ROC undefined (single-class)", ha="center", va="center")
            plt.axis("off")
            plt.tight_layout()
            plt.savefig(roc_path, dpi=200)
            plt.close()
        else:
            plt.figure(figsize=(6, 6))
            plt.plot(roc["fpr"], roc["tpr"], label=f"AUC={roc['auc']:.3f}")
            plt.plot([0, 1], [0, 1], linestyle="--", c="gray")
            plt.xlabel("False Positive Rate")
            plt.ylabel("True Positive Rate")
            plt.title(f"ROC Curve: {disease}")
            plt.legend()
            plt.tight_layout()
            plt.savefig(roc_path, dpi=200)
            plt.close()
        df_pred = pd.DataFrame({
            "state": states_d,
            "week": weeks_d,
            "actual": y_val_true_d,
            "predicted": y_val_pred_d,
            "correct": (y_true_cls == y_pred_cls).astype(int),
        })
        std_recent = float(np.std(y_val_true_d) or 0.0)
        base_q = (float(np.percentile(y_train_d, 75)) if len(y_train_d) else 0.0)
        baseline = max(std_recent, base_q / 4.0, 1.0)
        df_pred["confidence_pct"] = 100.0 * (1.0 - np.abs(df_pred["actual"] - df_pred["predicted"]) / (baseline + 1e-6))
        df_pred["confidence_pct"] = df_pred["confidence_pct"].clip(lower=0.0, upper=100.0)
        pred_csv = REPORTS_DIR / f"eval_predictions_{disease}.csv"
        df_pred.to_csv(pred_csv, index=False)
        rows.append({
            "disease": disease,
            "sample_size": len(meta_val_d),
            "positive": pos,
            "negative": neg,
            "accuracy_pct": round(acc_w["accuracy"], 2),
            "precision_weighted_pct": (round(acc_w["weighted"]["precision"], 2) if not math.isnan(acc_w["weighted"]["precision"]) else None),
            "recall_weighted_pct": (round(acc_w["weighted"]["recall"], 2) if not math.isnan(acc_w["weighted"]["recall"]) else None),
            "f1_weighted_pct": (round(acc_w["weighted"]["f1"], 2) if not math.isnan(acc_w["weighted"]["f1"]) else None),
            "precision_pos_pct": (round(acc_w["per_class"][1]["precision"], 2) if not math.isnan(acc_w["per_class"][1]["precision"]) else None),
            "recall_pos_pct": (round(acc_w["per_class"][1]["recall"], 2) if not math.isnan(acc_w["per_class"][1]["recall"]) else None),
            "f1_pos_pct": (round(acc_w["per_class"][1]["f1"], 2) if not math.isnan(acc_w["per_class"][1]["f1"]) else None),
            "precision_neg_pct": (round(acc_w["per_class"][0]["precision"], 2) if not math.isnan(acc_w["per_class"][0]["precision"]) else None),
            "recall_neg_pct": (round(acc_w["per_class"][0]["recall"], 2) if not math.isnan(acc_w["per_class"][0]["recall"]) else None),
            "f1_neg_pct": (round(acc_w["per_class"][0]["f1"], 2) if not math.isnan(acc_w["per_class"][0]["f1"]) else None),
            "auc": (round(float(roc["auc"]), 3) if not math.isnan(float(roc["auc"])) else None),
            "timestamp": ts,
            "model_version": model_version,
            "roc_path": str(roc_path).replace("\\", "/"),
            "chart_path": str(chart_path).replace("\\", "/"),
        })
    df_metrics = pd.DataFrame(rows)
    metrics_csv = REPORTS_DIR / "evaluation_metrics.csv"
    df_metrics.to_csv(metrics_csv, index=False)
    summary_txt = REPORTS_DIR / "summary_report.txt"
    def fmt(v, digits=2):
        if pd.isna(v) or v is None:
            return "NA"
        try:
            return f"{float(v):.{digits}f}"
        except Exception:
            return str(v)
    with open(summary_txt, "w", encoding="utf-8") as f:
        for _, r in df_metrics.iterrows():
            line = (
                f"{r['disease']}: n={int(r['sample_size'])}, pos={int(r['positive'])}, neg={int(r['negative'])}, "
                f"acc={fmt(r['accuracy_pct'])}%, f1_w={fmt(r['f1_weighted_pct'])}%, auc={fmt(r['auc'], 3)}\n"
            )
            f.write(line)
    return df_metrics

def main():
    # CLI args
    parser = argparse.ArgumentParser(description="OutbreakIQ console report")
    parser.add_argument("--state", type=str, default=None, help="Target state (optional)")
    parser.add_argument("--disease", type=str, default=None, help="Target disease (optional; partial match allowed)")
    parser.add_argument("--all", action="store_true", help="Evaluate all diseases and save reports")
    args = parser.parse_args()

    ensure_reports_dir()
    # Load data
    if not DATA_PATH.exists():
        print(f"[ERROR] Data not found at {DATA_PATH}")
        sys.exit(1)
    df = pd.read_csv(DATA_PATH)
    required = ["state", "disease", "year", "week", "cases"]
    df = df.dropna(subset=required).reset_index(drop=True)
    df[FEATURES] = df[FEATURES].ffill().bfill()
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

    if args.all:
        metrics_df = evaluate_per_disease(df)
        if metrics_df.empty:
            print("[ERROR] Not enough data to evaluate.")
            sys.exit(1)
        print("\n=== Evaluation Summary (All Diseases) ===")
        print(metrics_df.to_string(index=False))
        return
    X, y, meta = create_sequences_with_meta(df, WINDOW_SIZE)
    if len(X) == 0:
        print("[ERROR] Not enough data to evaluate.")
        sys.exit(1)
    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    meta_train, meta_val = meta[:split], meta[split:]

    # Load scalers and model (fallback to baseline if unavailable)
    feature_scaler = None
    target_scaler = None
    model = None
    if JOBLIB_AVAILABLE and FEATURE_SCALER_PATH.exists() and TARGET_SCALER_PATH.exists() and MODEL_PATH.exists():
        feature_scaler = joblib_load(FEATURE_SCALER_PATH)
        target_scaler = joblib_load(TARGET_SCALER_PATH)
        try:
            from tensorflow.keras.models import load_model
            model = load_model(MODEL_PATH)
        except Exception:
            model = None

    # Scale features
    n_features = X.shape[-1]
    if model is not None and feature_scaler is not None and target_scaler is not None:
        X_train_scaled = feature_scaler.transform(X_train.reshape(-1, n_features)).reshape(X_train.shape)
        X_val_scaled = feature_scaler.transform(X_val.reshape(-1, n_features)).reshape(X_val.shape)
        y_val_pred_scaled = model.predict(X_val_scaled, verbose=0).flatten()
        y_val_pred = target_scaler.inverse_transform(y_val_pred_scaled.reshape(-1, 1)).flatten()
    else:
        y_val_pred = X_val[:, -1, 0].astype(float)
    # y_val is already in real units from the dataset; do NOT inverse-transform
    y_val_true = y_val.astype(float)
    # Clamp negatives in predictions
    y_val_pred = np.maximum(0.0, y_val_pred)

    # Regression metrics
    reg_metrics = compute_regression_metrics(y_val_true, y_val_pred)

    # Classification metrics restricted to current state/disease context
    thresholds = build_thresholds(y_train, meta_train)
    global75 = float(np.percentile(y_train, 75)) if len(y_train) else 0.0
    idx_sd = [i for i, m in enumerate(meta_val) if m["state"] == state and m["disease"] == disease]
    if idx_sd:
        thr_ctx = thresholds.get((state, disease), global75)
        y_true_cls = np.array([1 if y_val_true[i] >= thr_ctx else 0 for i in idx_sd])
        y_pred_cls = np.array([1 if y_val_pred[i] >= thr_ctx else 0 for i in idx_sd])
        pos_sd = int(np.sum(y_true_cls == 1))
        neg_sd = int(np.sum(y_true_cls == 0))
        viable_sd = (len(idx_sd) >= 50) and (pos_sd > 0) and (neg_sd > 0)
        if viable_sd:
            cls_metrics = compute_classification_metrics(y_true_cls, y_pred_cls)
        else:
            cls_metrics = {"precision": float("nan"), "recall": float("nan"), "f1": float("nan")}
    else:
        thr_ctx = thresholds.get((state, disease), global75)
        idx_all = [i for i, m in enumerate(meta) if m["state"] == state and m["disease"] == disease]
        if idx_all:
            split_ctx = max(1, int(len(idx_all) * 0.8))
            idx_train_ctx = idx_all[:split_ctx]
            idx_val_ctx = idx_all[split_ctx:]
            if idx_val_ctx:
                X_val_ctx = X[idx_val_ctx]
                if model is not None and feature_scaler is not None and target_scaler is not None:
                    X_val_ctx_scaled = feature_scaler.transform(X_val_ctx.reshape(-1, n_features)).reshape(X_val_ctx.shape)
                    y_val_pred_scaled_ctx = model.predict(X_val_ctx_scaled, verbose=0).flatten()
                    y_val_pred_ctx = target_scaler.inverse_transform(y_val_pred_scaled_ctx.reshape(-1, 1)).flatten()
                else:
                    y_val_pred_ctx = X_val_ctx[:, -1, 0].astype(float)
                y_val_true_ctx = y[idx_val_ctx].astype(float)
                y_true_cls = np.array([1 if y_val_true_ctx[j] >= thr_ctx else 0 for j in range(len(idx_val_ctx))])
                y_pred_cls = np.array([1 if y_val_pred_ctx[j] >= thr_ctx else 0 for j in range(len(idx_val_ctx))])
                pos_ctx = int(np.sum(y_true_cls == 1))
                neg_ctx = int(np.sum(y_true_cls == 0))
                viable_ctx = (len(idx_val_ctx) >= 50) and (pos_ctx > 0) and (neg_ctx > 0)
                if viable_ctx:
                    cls_metrics = compute_classification_metrics(y_true_cls, y_pred_cls)
                else:
                    cls_metrics = {"precision": float("nan"), "recall": float("nan"), "f1": float("nan")}
            else:
                y_true_cls = np.array([])
                y_pred_cls = np.array([])
                cls_metrics = {"precision": float("nan"), "recall": float("nan"), "f1": float("nan")}
        else:
            y_true_cls = np.array([])
            y_pred_cls = np.array([])
            cls_metrics = {"precision": float("nan"), "recall": float("nan"), "f1": float("nan")}

    # Risk level based on predicted vs thresholds for latest context
    key = (state, disease)
    thr_latest = thresholds.get(key, global75)
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
    if model is not None and feature_scaler is not None and target_scaler is not None:
        latest_window_scaled = feature_scaler.transform(latest_window.reshape(-1, n_features)).reshape(1, WINDOW_SIZE, n_features)
        pred_next_scaled = float(model.predict(latest_window_scaled, verbose=0)[0][0])
        pred_next = float(target_scaler.inverse_transform(np.array([[pred_next_scaled]]))[0][0])
        pred_next = max(0.0, pred_next)
    else:
        pred_next = float(latest_window[-1, 0])

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
        baseline = max(std_global, global75 / 4.0, 1.0)
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