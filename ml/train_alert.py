from __future__ import annotations

from pathlib import Path
import time

import pandas as pd

from .utils import load_training, ensure_reports_dir

try:
    from sklearn.ensemble import RandomForestClassifier
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False


def label_outbreak_next_week(df: pd.DataFrame, window: int = 8, k_std: float = 2.0) -> pd.DataFrame:
    # True label: next-week is an outbreak if it exceeds rolling mean + k*std
    df = df.sort_values(["disease", "state", "year", "week"]).reset_index(drop=True)
    grp = df.groupby(["disease", "state"], sort=False)
    roll_mean = grp["cases"].rolling(window=window, min_periods=1).mean().reset_index(level=[0,1], drop=True)
    roll_std = grp["cases"].rolling(window=window, min_periods=1).std().reset_index(level=[0,1], drop=True)
    df["thr_roll"] = (roll_mean + k_std * roll_std.fillna(0))
    df["true_cases_next_week"] = grp["cases"].shift(-1)
    df["outbreak_next_week"] = (df["true_cases_next_week"] > df["thr_roll"]).astype("Int64")
    return df


def predict_alert(df: pd.DataFrame) -> pd.DataFrame:
    # If sklearn available, train a classifier on enriched features; else threshold rule
    feature_cols = [
        "cases_last_week","cases_2w_avg","cases_growth_rate","cases_per_100k",
        "cases_mean_4w","cases_std_4w","deaths_last_week","deaths_mean_4w",
        "temperature_2m_mean","relative_humidity_2m_mean","precipitation_sum",
        "who_cases_national","population","urban_percent",
    ]

    if SKLEARN_AVAILABLE:
        rows = []
        for disease, g in df.groupby("disease"):
            g2 = g.dropna(subset=feature_cols + ["outbreak_next_week"]).copy()
            if g2.empty:
                continue
            X = g2[feature_cols]
            y = g2["outbreak_next_week"].astype(int)
            model = RandomForestClassifier(n_estimators=200, random_state=42)
            model.fit(X, y)
            yhat = model.predict(X)
            g2["pred_outbreak_next_week"] = yhat
            rows.append(g2)
        if rows:
            df = pd.concat(rows + [df[df["outbreak_next_week"].isna()]], ignore_index=True)
        else:
            df["pred_outbreak_next_week"] = pd.NA
    else:
        df["pred_outbreak_next_week"] = (df["cases"] > df["thr_roll"]).astype("Int64")
    return df


def evaluate_alert(df: pd.DataFrame) -> pd.DataFrame:
    eval_df = df.dropna(subset=["outbreak_next_week", "pred_outbreak_next_week"]).copy()
    if eval_df.empty:
        return pd.DataFrame({
            "disease": [],
            "precision": [],
            "recall": [],
            "f1": [],
        })

    def prf(g: pd.DataFrame):
        tp = int(((g["pred_outbreak_next_week"] == 1) & (g["outbreak_next_week"] == 1)).sum())
        fp = int(((g["pred_outbreak_next_week"] == 1) & (g["outbreak_next_week"] == 0)).sum())
        fn = int(((g["pred_outbreak_next_week"] == 0) & (g["outbreak_next_week"] == 1)).sum())
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        return pd.Series({"precision": precision, "recall": recall, "f1": f1})

    return eval_df.groupby("disease").apply(prf).reset_index()


def main():
    df = load_training()
    reports_dir = ensure_reports_dir()

    df = label_outbreak_next_week(df)
    df = predict_alert(df)
    metrics = evaluate_alert(df)
    out_path = reports_dir / "metrics_alert_classification.csv"
    metrics.to_csv(out_path, index=False)

    # Drift and health placeholders updated here if needed; keep minimal in train_regression
    health = {
        "timestamp": int(time.time()),
        "status": "ok",
        "alert_rows_used_for_eval": int(len(df.dropna(subset=["outbreak_next_week"]))),
        "sklearn": SKLEARN_AVAILABLE,
    }
    (reports_dir / "health.json").write_text(pd.Series(health).to_json(indent=2), encoding="utf-8")

    print(f"Alert metrics written to: {out_path}")


if __name__ == "__main__":
    main()