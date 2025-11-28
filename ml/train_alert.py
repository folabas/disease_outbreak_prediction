from __future__ import annotations

from pathlib import Path
import time
import numpy as np
import pandas as pd

from utils import load_training, ensure_reports_dir

try:
    from .features import FEATURES, TARGET
except ImportError:
    from features import FEATURES, TARGET  # type: ignore

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.utils.class_weight import compute_class_weight
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False


# -----------------------------------------------------
# 1. Improved Outbreak Label (More Sensitive)
# -----------------------------------------------------
def label_outbreak_next_week(df: pd.DataFrame, window: int = 8, k_std: float = 1.5) -> pd.DataFrame:
    """
    Label an outbreak when next week's cases exceed mean + (k * std).
    Lower k_std = more sensitive outbreak detection.
    """
    df = df.sort_values(["disease", "state", "year", "week"]).reset_index(drop=True)
    grp = df.groupby(["disease", "state"], sort=False)

    roll_mean = grp["cases"].rolling(window=window, min_periods=1).mean().reset_index(level=[0,1], drop=True)
    roll_std  = grp["cases"].rolling(window=window, min_periods=1).std().reset_index(level=[0,1], drop=True)

    df["thr_roll"] = roll_mean + k_std * roll_std.fillna(0)
    df["true_cases_next_week"] = grp["cases"].shift(-1)

    df["outbreak_next_week"] = (df["true_cases_next_week"] > df["thr_roll"]).astype("Int64")
    return df


# -----------------------------------------------------
# 2. UPGRADED FEATURE SET (Aligned with deep model)
# -----------------------------------------------------
IMPROVED_FEATURES = [c for c in FEATURES if c != TARGET]


# -----------------------------------------------------
# 3. Prediction Model (Balanced Random Forest)
# -----------------------------------------------------
def predict_alert(df: pd.DataFrame) -> pd.DataFrame:

    if not SKLEARN_AVAILABLE:
        print("[WARNING] Falling back to rule-based outbreak detector")
        df["pred_outbreak_next_week"] = (df["cases"] > df["thr_roll"]).astype("Int64")
        return df

    rows = []

    for disease, g in df.groupby("disease"):
        missing = [c for c in IMPROVED_FEATURES if c not in g.columns]
        for col in missing:
            g[col] = 0.0
        g2 = g.dropna(subset=IMPROVED_FEATURES + ["outbreak_next_week"]).copy()
        if g2.empty:
            continue

        X = g2[IMPROVED_FEATURES]
        y = g2["outbreak_next_week"].astype(int)

        # --- CLASS BALANCING (Fixes Ebola/Malaria imbalance) ---
        classes = np.unique(y)
        weights = compute_class_weight(class_weight="balanced", classes=classes, y=y)
        class_weights = {cls: w for cls, w in zip(classes, weights)}

        model = RandomForestClassifier(
            n_estimators=400,
            max_depth=None,
            min_samples_split=3,
            class_weight=class_weights,   # <-- major improvement
            random_state=42
        )
        model.fit(X, y)

        # Save predicted probability (not just 0/1)
        prob = model.predict_proba(X)[:, 1]
        g2["outbreak_probability"] = prob

        # Convert probability → binary label using dynamic threshold
        threshold = 0.40  # more sensitive to outbreaks
        g2["pred_outbreak_next_week"] = (prob >= threshold).astype(int)

        rows.append(g2)

    # Merge predictions back into main df
    if rows:
        df = pd.concat(rows + [df[df["outbreak_next_week"].isna()]], ignore_index=True)
    else:
        df["pred_outbreak_next_week"] = pd.NA

    return df


# -----------------------------------------------------
# 4. Metrics
# -----------------------------------------------------
def evaluate_alert(df: pd.DataFrame) -> pd.DataFrame:
    eval_df = df.dropna(subset=["outbreak_next_week", "pred_outbreak_next_week"]).copy()

    if eval_df.empty:
        return pd.DataFrame({"disease": [], "precision": [], "recall": [], "f1": [],})

    def prf(g: pd.DataFrame):
        tp = int(((g["pred_outbreak_next_week"] == 1) & (g["outbreak_next_week"] == 1)).sum())
        fp = int(((g["pred_outbreak_next_week"] == 1) & (g["outbreak_next_week"] == 0)).sum())
        fn = int(((g["pred_outbreak_next_week"] == 0) & (g["outbreak_next_week"] == 1)).sum())

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        return pd.Series({"precision": precision, "recall": recall, "f1": f1})

    return eval_df.groupby("disease").apply(prf).reset_index()


# -----------------------------------------------------
# 5. Main
# -----------------------------------------------------
def main():
    df = load_training()
    reports_dir = ensure_reports_dir()

    df = label_outbreak_next_week(df)
    df = predict_alert(df)
    metrics = evaluate_alert(df)

    out_path = reports_dir / "metrics_alert_classification.csv"
    metrics.to_csv(out_path, index=False)

    health = {
        "timestamp": int(time.time()),
        "status": "ok",
        "alert_rows_used_for_eval": int(len(df.dropna(subset=["outbreak_next_week"]))),
        "sklearn": SKLEARN_AVAILABLE,
    }
    (reports_dir / "health.json").write_text(pd.Series(health).to_json(indent=2), encoding="utf-8")

    print(f"🚀 Alert metrics written to: {out_path}")


if __name__ == "__main__":
    main()
