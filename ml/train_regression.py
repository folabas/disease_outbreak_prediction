from __future__ import annotations

from pathlib import Path
import time

import pandas as pd

from .utils import load_training, ensure_reports_dir, REPORTS_DIR

try:
    from sklearn.ensemble import RandomForestRegressor
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False


def train_and_evaluate() -> Path:
    df = load_training()
    reports_dir = ensure_reports_dir()

    # Baseline: predict next-week cases = last-week cases (lag-1)
    # Target: next-week cases
    df["true_cases_next_week"] = df.groupby(["disease", "state"]) ["cases"].shift(-1)

    feature_cols = [
        "cases_last_week","cases_2w_avg","cases_growth_rate","cases_per_100k",
        "cases_mean_4w","cases_std_4w","deaths_last_week","deaths_mean_4w",
        "temperature_2m_mean","relative_humidity_2m_mean","precipitation_sum",
        "who_cases_national","population","urban_percent",
    ]

    results = []
    preds = []

    if SKLEARN_AVAILABLE:
        for disease, g in df.groupby("disease"):
            g2 = g.dropna(subset=feature_cols + ["true_cases_next_week"]).copy()
            if g2.empty:
                continue
            X = g2[feature_cols]
            y = g2["true_cases_next_week"]

            model = RandomForestRegressor(n_estimators=200, random_state=42)
            model.fit(X, y)
            yhat = model.predict(X)
            g2["pred_cases_next_week"] = yhat
            preds.append(g2[["disease","state","year","week","pred_cases_next_week","true_cases_next_week"]])

            abs_err = (yhat - y).abs()
            mae = float(abs_err.mean())
            results.append({"disease": disease, "mae": mae, "model": "RandomForestRegressor"})
        eval_df = pd.concat(preds, ignore_index=True) if preds else pd.DataFrame()
    else:
        # Fallback baseline: lag-1
        df["pred_cases_next_week"] = df.groupby(["disease", "state"]) ["cases"].shift(1)
        eval_df = df.dropna(subset=["pred_cases_next_week", "true_cases_next_week"]).copy()
        eval_df["abs_err"] = (eval_df["pred_cases_next_week"] - eval_df["true_cases_next_week"]).abs()
        for disease, g in eval_df.groupby("disease"):
            mae = float(g["abs_err"].mean())
            results.append({"disease": disease, "mae": mae, "model": "Lag1Baseline"})

    disease_mae = pd.DataFrame(results)
    overall_mae = float(disease_mae["mae"].mean()) if not disease_mae.empty else float("nan")
    disease_mae["overall_mae"] = overall_mae
    out_path = reports_dir / "metrics_regression.csv"
    disease_mae.to_csv(out_path, index=False)

    # Minimal health file noting training success
    health = {
        "timestamp": int(time.time()),
        "status": "ok",
        "rows_used_for_eval": int(len(eval_df)),
        "overall_mae": overall_mae,
        "diseases": sorted(df["disease"].unique().tolist()),
        "sklearn": SKLEARN_AVAILABLE,
    }
    (reports_dir / "health.json").write_text(pd.Series(health).to_json(indent=2), encoding="utf-8")

    return out_path


def main():
    out = train_and_evaluate()
    print(f"Regression metrics written to: {out}")


if __name__ == "__main__":
    main()