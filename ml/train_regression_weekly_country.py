"""
Train weekly, country-level regressors per disease by aggregating across states.

This uses the merged weekly dataset and WHO country counts, avoiding state
requirements. Features include last-week cases, WHO annual counts, seasonality,
and year. It’s a pragmatic fallback when state-level data is sparse.
"""

from pathlib import Path
import os
import json

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

from .models import build_regressor
from .config import PROJECT_ROOT, REPORTS_DIR, MODELS_DIR
from .exp_tracking import Tracker


DATA_PATH = PROJECT_ROOT / "data" / "outbreakiq_training_data_filled.csv"


def load_weekly_country() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    # Basic validation
    core = ["disease", "year", "week", "cases"]
    for c in core:
        if c not in df.columns:
            raise ValueError(f"Missing expected column '{c}' in dataset")
    # Coerce numeric
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["week"] = pd.to_numeric(df["week"], errors="coerce")
    df["cases"] = pd.to_numeric(df["cases"], errors="coerce")
    if "who_country_cases" in df.columns:
        df["who_country_cases"] = pd.to_numeric(df["who_country_cases"], errors="coerce")
    else:
        df["who_country_cases"] = np.nan

    # Keep rows even if cases are missing; fill with 0 to allow aggregation
    df = df.dropna(subset=["disease", "year", "week"]).copy()
    df["cases"] = df["cases"].fillna(0.0)

    # Aggregate to country-week per disease
    agg = (
        df.groupby(["disease", "year", "week"], as_index=False)
          .agg({
              "cases": "sum",
              # WHO counts are annual; take max within year-week group (identical across states)
              "who_country_cases": "max",
          })
    )

    # Seasonality
    agg["week_sin"] = np.sin(2 * np.pi * agg["week"] / 52)
    agg["week_cos"] = np.cos(2 * np.pi * agg["week"] / 52)

    # Lag feature per disease
    agg = agg.sort_values(["disease", "year", "week"]).reset_index(drop=True)
    agg["cases_last_week"] = agg.groupby("disease")["cases"].shift(1)
    agg = agg.dropna(subset=["cases_last_week"]).copy()

    # Fill WHO missing with 0
    agg["who_country_cases"] = agg["who_country_cases"].fillna(0.0)

    return agg


def time_split(df: pd.DataFrame, test_fraction: float = 0.2):
    n = len(df)
    cutoff = max(1, int((1.0 - test_fraction) * n))
    return df.iloc[:cutoff].copy(), df.iloc[cutoff:].copy()


def train_weekly_country_regressors():
    df = load_weekly_country()
    diseases = sorted(df["disease"].unique().tolist())

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    tracker = Tracker(PROJECT_ROOT, MODELS_DIR)
    rows = []
    for disease in diseases:
        ddf = df[df["disease"] == disease].copy()
        if len(ddf) < 20:
            rows.append({
                "disease": disease,
                "r2": np.nan,
                "mae": np.nan,
                "rmse": np.nan,
                "n_train": int(len(ddf)),
                "n_test": 0,
                "note": "skipped_insufficient_rows",
            })
            continue

        train_df, test_df = time_split(ddf, test_fraction=0.2)

        feature_cols = ["who_country_cases", "cases_last_week", "week_sin", "week_cos", "year"]
        X_train = train_df[feature_cols].copy()
        y_train = train_df["cases"].values
        X_test = test_df[feature_cols].copy()
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

        model_path = MODELS_DIR / f"outbreakiq_regressor_weekly_country_{disease.replace(' ', '_').lower()}.pkl"
        dump(model, model_path)

        run_tags = {"script": "train_regression_weekly_country.py", "disease": disease}
        with tracker.start(run_name=f"regressor-weekly-country-{disease}", tags=run_tags):
            params = model.get_params()
            if tuned_params:
                params.update({f"tuned_{k}": v for k, v in tuned_params.items()})
            tracker.log_params(params)
            tracker.log_metrics({"r2": r2, "mae": mae, "rmse": rmse, "n_train": int(len(train_df)), "n_test": int(len(test_df))})
            tracker.log_model(model, artifact_path="model")

        tracker.record_fallback(
            script="train_regression_weekly_country.py",
            disease=disease,
            dataset_path=DATA_PATH,
            model_path=model_path,
            params=params,
            metrics={"r2": r2, "mae": mae, "rmse": rmse},
            stage="staging",
        )

    metrics_csv = REPORTS_DIR / "metrics_regression_weekly_country.csv"
    pd.DataFrame(rows).to_csv(metrics_csv, index=False)

    metrics_json = REPORTS_DIR / "metrics_regression_weekly_country.json"
    metrics_json.write_text(json.dumps(rows, indent=2))

    print(f"Saved weekly country models to {MODELS_DIR}")
    print(f"Saved weekly country regression metrics to {metrics_csv}")


if __name__ == "__main__":
    train_weekly_country_regressors()