import json
from pathlib import Path
import os

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold, TimeSeriesSplit, GridSearchCV
from joblib import dump

from .config import (
    DATA_PATH,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    MODELS_DIR,
    REPORTS_DIR,
    PROJECT_ROOT,
)
from .data import load_dataset, select_features, time_based_split, get_diseases
from .models import build_regressor
from .exp_tracking import Tracker


def train_per_disease_regressor():
    df = load_dataset(DATA_PATH)

    diseases = get_diseases(df)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    tracker = Tracker(PROJECT_ROOT, MODELS_DIR)
    metrics_rows = []

    for disease in diseases:
        ddf = df[df["disease"] == disease].copy()
        if len(ddf) < 20:
            # For very small datasets, still attempt training but warn
            print(f"[WARN] Low sample size for {disease}: {len(ddf)} rows. Proceeding anyway.")

        # Split by time to avoid leakage
        train_df, test_df = time_based_split(ddf, test_fraction=0.2)

        X_train = select_features(train_df, FEATURE_COLUMNS)
        y_train = train_df[TARGET_COLUMN].values

        X_test = select_features(test_df, FEATURE_COLUMNS)
        y_test = test_df[TARGET_COLUMN].values

        model = build_regressor()

        # Optional time-series hyperparameter tuning
        tuned_params = {}
        if os.getenv("OUTBREAKIQ_TUNING") == "1":
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

        # Evaluate
        y_pred = model.predict(X_test)
        r2 = float(r2_score(y_test, y_pred))
        mae = float(mean_absolute_error(y_test, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))

        metrics_rows.append({
            "disease": disease,
            "r2": r2,
            "mae": mae,
            "rmse": rmse,
            "n_train": int(len(train_df)),
            "n_test": int(len(test_df)),
        })

        # Save model
        model_path = MODELS_DIR / f"outbreakiq_regressor_{disease.replace(' ', '_').lower()}.pkl"
        dump(model, model_path)

        # Track experiment
        run_tags = {"script": "train_regression.py", "disease": disease}
        with tracker.start(run_name=f"regressor-{disease}", tags=run_tags):
            # Log params (model hyperparameters + tuned params if any)
            params = model.get_params()
            if tuned_params:
                params.update({f"tuned_{k}": v for k, v in tuned_params.items()})
            tracker.log_params(params)
            tracker.log_metrics({"r2": r2, "mae": mae, "rmse": rmse, "n_train": int(len(train_df)), "n_test": int(len(test_df))})
            tracker.log_model(model, artifact_path="model")

        # Write fallback registry record
        tracker.record_fallback(
            script="train_regression.py",
            disease=disease,
            dataset_path=DATA_PATH,
            model_path=model_path,
            params=params,
            metrics={"r2": r2, "mae": mae, "rmse": rmse},
            stage="staging",
        )

    # Save metrics
    metrics_df = pd.DataFrame(metrics_rows)
    metrics_csv = REPORTS_DIR / "metrics_regression.csv"
    metrics_df.to_csv(metrics_csv, index=False)

    metrics_json = REPORTS_DIR / "metrics_regression.json"
    metrics_json.write_text(json.dumps(metrics_rows, indent=2))

    print(f"Saved models to {MODELS_DIR}")
    print(f"Saved regression metrics to {metrics_csv}")


if __name__ == "__main__":
    train_per_disease_regressor()