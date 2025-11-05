import json
from pathlib import Path
import os

import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_recall_fscore_support,
)
from joblib import dump

from .config import (
    DATA_PATH,
    FEATURE_COLUMNS,
    MODELS_DIR,
    REPORTS_DIR,
    ALERT_LABEL_STRATEGY,
    STATIC_OUTBREAK_THRESHOLD_PER_100K,
    QUANTILE_THRESHOLD,
)
from .data import load_dataset, select_features, time_based_split, get_diseases
from .models import build_classifier
from .exp_tracking import Tracker
from .config import PROJECT_ROOT


def label_outbreak_next_week(df: pd.DataFrame) -> pd.DataFrame:
    """Create binary label indicating if next week's cases_per_100k exceeds threshold.

    Threshold strategy is configurable: static or quantile-based per disease-state.
    """
    df = df.copy()
    # Compute next week's cases_per_100k within each disease-state
    df["next_cases_per_100k"] = (
        df.sort_values(["disease", "state", "year", "week"])
          .groupby(["disease", "state"])['cases_per_100k']
          .shift(-1)
    )

    if ALERT_LABEL_STRATEGY == "static":
        thresh = STATIC_OUTBREAK_THRESHOLD_PER_100K
        df["outbreak_next_week"] = (df["next_cases_per_100k"] >= thresh).astype(int)
    else:
        # Quantile per disease-state
        def compute_quantile_threshold(g: pd.DataFrame) -> float:
            return float(np.nanquantile(g["cases_per_100k"], QUANTILE_THRESHOLD))

        thresholds = (
            df.groupby(["disease", "state"])  # type: ignore
              .apply(compute_quantile_threshold)
              .rename("threshold")
        )
        df = df.merge(thresholds.reset_index(), on=["disease", "state"], how="left")
        df["outbreak_next_week"] = (df["next_cases_per_100k"] >= df["threshold"]).astype(int)

    # Drop rows where next week is missing (last rows in each group)
    df = df.dropna(subset=["next_cases_per_100k"]).copy()
    return df


def train_per_disease_alert_classifier():
    df = load_dataset(DATA_PATH)
    df = label_outbreak_next_week(df)

    diseases = get_diseases(df)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    metrics_rows = []
    tracker = Tracker(PROJECT_ROOT, MODELS_DIR)

    for disease in diseases:
        ddf = df[df["disease"] == disease].copy()
        if len(ddf) < 20:
            print(f"[WARN] Low sample size for {disease}: {len(ddf)} rows. Proceeding anyway.")

        train_df, test_df = time_based_split(ddf, test_fraction=0.2)

        X_train = select_features(train_df, FEATURE_COLUMNS)
        y_train = train_df["outbreak_next_week"].astype(int).values

        X_test = select_features(test_df, FEATURE_COLUMNS)
        y_test = test_df["outbreak_next_week"].astype(int).values

        model = build_classifier()

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
            search = GridSearchCV(model, param_grid, cv=tscv, scoring="roc_auc", n_jobs=-1)
            search.fit(X_train, y_train)
            model = search.best_estimator_
            tuned_params = search.best_params_
        else:
            model.fit(X_train, y_train)

        # Evaluate
        # Handle single-class edge case gracefully
        proba = model.predict_proba(X_test)
        if proba.shape[1] == 2:
            # standard binary case
            y_prob = proba[:, 1]
        else:
            # only one class was present in training; infer whether it's the positive class
            classes = list(model.classes_)
            if 1 in classes:
                y_prob = np.ones(len(X_test))
            else:
                y_prob = np.zeros(len(X_test))
        # Metrics: guard for single-class y_test
        if len(np.unique(y_test)) >= 2:
            roc = float(roc_auc_score(y_test, y_prob))
            pr_auc = float(average_precision_score(y_test, y_prob))
        else:
            roc = float('nan')
            pr_auc = float('nan')

        # Choose 0.5 threshold for now; can be calibrated later
        y_pred = (y_prob >= 0.5).astype(int)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average="binary", zero_division=0
        )

        metrics_rows.append({
            "disease": disease,
            "roc_auc": roc,
            "pr_auc": pr_auc,
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "n_train": int(len(train_df)),
            "n_test": int(len(test_df)),
        })

        # Save model
        model_path = MODELS_DIR / f"outbreakiq_classifier_{disease.replace(' ', '_').lower()}.pkl"
        dump(model, model_path)

        # Track experiment
        run_tags = {"script": "train_alert.py", "disease": disease}
        with tracker.start(run_name=f"classifier-{disease}", tags=run_tags):
            params = model.get_params()
            if tuned_params:
                params.update({f"tuned_{k}": v for k, v in tuned_params.items()})
            tracker.log_params(params)
            tracker.log_metrics({
                "roc_auc": roc,
                "pr_auc": pr_auc,
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
                "n_train": int(len(train_df)),
                "n_test": int(len(test_df)),
            })
            tracker.log_model(model, artifact_path="model")

        tracker.record_fallback(
            script="train_alert.py",
            disease=disease,
            dataset_path=DATA_PATH,
            model_path=model_path,
            params=params,
            metrics={"roc_auc": roc, "pr_auc": pr_auc, "precision": float(precision), "recall": float(recall), "f1": float(f1)},
            stage="staging",
        )

    # Save metrics
    metrics_df = pd.DataFrame(metrics_rows)
    metrics_csv = REPORTS_DIR / "metrics_alert_classification.csv"
    metrics_df.to_csv(metrics_csv, index=False)

    metrics_json = REPORTS_DIR / "metrics_alert_classification.json"
    metrics_json.write_text(json.dumps(metrics_rows, indent=2))

    print(f"Saved alert models to {MODELS_DIR}")
    print(f"Saved alert metrics to {metrics_csv}")


if __name__ == "__main__":
    train_per_disease_alert_classifier()