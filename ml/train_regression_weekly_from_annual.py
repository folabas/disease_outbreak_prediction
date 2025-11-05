"""
Disaggregate WHO annual country counts into weekly series per disease,
then train weekly country-level regressors. This provides broad coverage
when true weekly data is sparse or missing state granularity.

Assumption: annual cases are distributed uniformly across 52 weeks.
You can later replace with disease-specific seasonal weights.
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


WHO_PATH = PROJECT_ROOT / "data" / "who_disease_data.csv"


def load_who_annual() -> pd.DataFrame:
    df = pd.read_csv(WHO_PATH)
    df = df[df["country"].astype(str).str.upper() == "NGA"].copy()
    df["cases"] = pd.to_numeric(df["cases"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year", "disease"]).copy()
    # Fill missing annual cases with 0
    df["cases"] = df["cases"].fillna(0.0)
    df["year"] = df["year"].astype(int)
    return df


def make_weekly_from_annual(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        disease = r["disease"]
        year = int(r["year"])
        annual_cases = float(r["cases"]) if pd.notnull(r["cases"]) else 0.0
        weekly_cases = annual_cases / 52.0
        who_country_cases = annual_cases
        for week in range(1, 53):
            rows.append({
                "disease": disease,
                "year": year,
                "week": week,
                "cases": weekly_cases,
                "who_country_cases": who_country_cases,
            })
    weekly = pd.DataFrame(rows)
    # Seasonality
    weekly["week_sin"] = np.sin(2 * np.pi * weekly["week"] / 52)
    weekly["week_cos"] = np.cos(2 * np.pi * weekly["week"] / 52)
    weekly = weekly.sort_values(["disease", "year", "week"]).reset_index(drop=True)
    # Lag
    weekly["cases_last_week"] = weekly.groupby("disease")["cases"].shift(1)
    weekly = weekly.dropna(subset=["cases_last_week"]).copy()
    return weekly


def time_split(df: pd.DataFrame, test_fraction: float = 0.2):
    n = len(df)
    cutoff = max(1, int((1.0 - test_fraction) * n))
    return df.iloc[:cutoff].copy(), df.iloc[cutoff:].copy()


def train_weekly_from_annual():
    annual = load_who_annual()
    weekly = make_weekly_from_annual(annual)
    diseases = sorted(weekly["disease"].unique().tolist())

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    tracker = Tracker(PROJECT_ROOT, MODELS_DIR)
    rows = []
    for disease in diseases:
        ddf = weekly[weekly["disease"] == disease].copy()
        if len(ddf) < 100:  # at least ~2 years of weekly points
            rows.append({
                "disease": disease,
                "r2": np.nan,
                "mae": np.nan,
                "rmse": np.nan,
                "n_train": int(len(ddf)),
                "n_test": 0,
                "note": "skipped_insufficient_weekly_points",
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

        model_path = MODELS_DIR / f"outbreakiq_regressor_weekly_from_annual_{disease.replace(' ', '_').lower()}.pkl"
        dump(model, model_path)

        run_tags = {"script": "train_regression_weekly_from_annual.py", "disease": disease}
        with tracker.start(run_name=f"regressor-weekly-from-annual-{disease}", tags=run_tags):
            params = model.get_params()
            if tuned_params:
                params.update({f"tuned_{k}": v for k, v in tuned_params.items()})
            tracker.log_params(params)
            tracker.log_metrics({"r2": r2, "mae": mae, "rmse": rmse, "n_train": int(len(train_df)), "n_test": int(len(test_df))})
            tracker.log_model(model, artifact_path="model")

        tracker.record_fallback(
            script="train_regression_weekly_from_annual.py",
            disease=disease,
            dataset_path=WHO_PATH,
            model_path=model_path,
            params=params,
            metrics={"r2": r2, "mae": mae, "rmse": rmse},
            stage="staging",
        )

    metrics_csv = REPORTS_DIR / "metrics_regression_weekly_from_annual.csv"
    pd.DataFrame(rows).to_csv(metrics_csv, index=False)

    metrics_json = REPORTS_DIR / "metrics_regression_weekly_from_annual.json"
    metrics_json.write_text(json.dumps(rows, indent=2))

    print(f"Saved weekly-from-annual models to {MODELS_DIR}")
    print(f"Saved weekly-from-annual regression metrics to {metrics_csv}")


if __name__ == "__main__":
    train_weekly_from_annual()