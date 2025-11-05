"""
Train annual, country-level regressors per disease using WHO historical data.

This complements the weekly, state-level pipeline by providing models where
weekly labels are unavailable. It uses simple time-aware splits and lag features.
"""

from pathlib import Path
import os
import json

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

from .models import build_regressor
from .config import REPORTS_DIR, MODELS_DIR, PROJECT_ROOT, RANDOM_STATE
from .exp_tracking import Tracker


WHO_PATH = PROJECT_ROOT / "data" / "who_disease_data.csv"


def load_who_annual() -> pd.DataFrame:
    df = pd.read_csv(WHO_PATH)
    # Keep Nigeria rows and non-null cases
    df = df[df["country"].astype(str).str.upper() == "NGA"].copy()
    df["cases"] = pd.to_numeric(df["cases"], errors="coerce")
    df = df.dropna(subset=["year", "cases", "disease"]).copy()
    df["year"] = df["year"].astype(int)
    df = df.sort_values(["disease", "year"]).reset_index(drop=True)
    # Lag feature: last year's cases per disease
    df["cases_last_year"] = df.groupby("disease")["cases"].shift(1)
    # Drop the first year per disease where lag is NaN
    df = df.dropna(subset=["cases_last_year"]).copy()
    return df


def time_based_split_annual(df: pd.DataFrame, test_fraction: float = 0.2):
    n = len(df)
    cutoff_idx = max(1, int((1.0 - test_fraction) * n))
    train_df = df.iloc[:cutoff_idx].copy()
    test_df = df.iloc[cutoff_idx:].copy()
    return train_df, test_df


def train_annual_regressors():
    df = load_who_annual()
    diseases = sorted(df["disease"].unique().tolist())

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    tracker = Tracker(PROJECT_ROOT, MODELS_DIR)
    rows = []
    for disease in diseases:
        ddf = df[df["disease"] == disease].copy()
        if len(ddf) < 5:
            # Too few annual points; skip but record
            rows.append({
                "disease": disease,
                "r2": np.nan,
                "mae": np.nan,
                "rmse": np.nan,
                "n_train": int(len(ddf)),
                "n_test": 0,
                "note": "skipped_insufficient_annual_rows",
            })
            continue

        train_df, test_df = time_based_split_annual(ddf, test_fraction=0.2)

        X_train = train_df[["year", "cases_last_year"]].copy()
        y_train = train_df["cases"].values
        X_test = test_df[["year", "cases_last_year"]].copy()
        y_test = test_df["cases"].values

        model = build_regressor()

        tuned_params = {}
        if os.getenv("OUTBREAKIQ_TUNING") == "1":
            from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
            tscv = TimeSeriesSplit(n_splits=5)
            param_grid = {
                "n_estimators": [100, 300, 500],
                "max_depth": [8, 12, 16],
                "min_samples_split": [2, 4],
                "min_samples_leaf": [1, 2],
            }
            search = GridSearchCV(model, param_grid, cv=tscv, scoring="r2", n_jobs=-1)
            search.fit(X_train, y_train)
            model = search.best_estimator_
            tuned_params = search.best_params_
        else:
            model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        r2 = float(r2_score(y_test, y_pred))
        mae = float(mean_absolute_error(y_test, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))

        rows.append({
            "disease": disease,
            "r2": r2,
            "mae": mae,
            "rmse": rmse,
            "n_train": int(len(train_df)),
            "n_test": int(len(test_df)),
        })

        model_path = MODELS_DIR / f"outbreakiq_regressor_annual_{disease.replace(' ', '_').lower()}.pkl"
        dump(model, model_path)

        run_tags = {"script": "train_regression_annual.py", "disease": disease}
        with tracker.start(run_name=f"regressor-annual-{disease}", tags=run_tags):
            params = model.get_params()
            if tuned_params:
                params.update({f"tuned_{k}": v for k, v in tuned_params.items()})
            tracker.log_params(params)
            tracker.log_metrics({"r2": r2, "mae": mae, "rmse": rmse, "n_train": int(len(train_df)), "n_test": int(len(test_df))})
            tracker.log_model(model, artifact_path="model")

        tracker.record_fallback(
            script="train_regression_annual.py",
            disease=disease,
            dataset_path=WHO_PATH,
            model_path=model_path,
            params=params,
            metrics={"r2": r2, "mae": mae, "rmse": rmse},
            stage="staging",
        )

    metrics_csv = REPORTS_DIR / "metrics_regression_annual.csv"
    pd.DataFrame(rows).to_csv(metrics_csv, index=False)

    metrics_json = REPORTS_DIR / "metrics_regression_annual.json"
    metrics_json.write_text(json.dumps(rows, indent=2))

    print(f"Saved annual models to {MODELS_DIR}")
    print(f"Saved annual regression metrics to {metrics_csv}")


if __name__ == "__main__":
    train_annual_regressors()