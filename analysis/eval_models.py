import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from joblib import load
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
    average_precision_score,
    precision_recall_fscore_support,
)

# Ensure project root is on the Python path when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from ml.config import FEATURE_COLUMNS, TARGET_COLUMN, MODELS_DIR, REPORTS_DIR
from ml.data import load_dataset, time_based_split, select_features

# Import helpers for alternate datasets
from ml.train_regression_weekly_country import load_weekly_country as _load_weekly_country
from ml.train_regression_weekly_from_annual import (
    load_who_annual as _load_who_annual_for_weekly,
    make_weekly_from_annual as _make_weekly_from_annual,
)
from ml.train_regression_annual import load_who_annual as _load_who_annual
from ml.train_alert import label_outbreak_next_week as _label_outbreak_next_week


def parse_model_filename(path: Path) -> dict:
    name = path.name
    # Expected formats:
    # - outbreakiq_regressor_{disease}.pkl
    # - outbreakiq_classifier_{disease}.pkl
    # - outbreakiq_regressor_weekly_country_{disease}.pkl
    # - outbreakiq_regressor_weekly_from_annual_{disease}.pkl
    # - outbreakiq_regressor_annual_{disease}.pkl
    parts = name.replace(".pkl", "").split("_")
    if len(parts) < 3:
        return {"type": "unknown", "disease": None}
    kind = parts[1]  # regressor or classifier
    if kind == "regressor" and len(parts) >= 3:
        # detect subtype
        if parts[2] == "weekly" and parts[3] == "country":
            disease = "_".join(parts[4:])
            return {"type": "regressor_weekly_country", "disease": disease}
        if parts[2] == "weekly" and parts[3] == "from" and parts[4] == "annual":
            disease = "_".join(parts[5:])
            return {"type": "regressor_weekly_from_annual", "disease": disease}
        if parts[2] == "annual":
            disease = "_".join(parts[3:])
            return {"type": "regressor_annual", "disease": disease}
        # base weekly state-level
        disease = "_".join(parts[2:])
        return {"type": "regressor_weekly_state", "disease": disease}
    elif kind == "classifier":
        disease = "_".join(parts[2:])
        return {"type": "classifier_weekly_state", "disease": disease}
    return {"type": "unknown", "disease": None}


def evaluate_regressor_weekly_state(disease_slug: str):
    df = load_dataset()
    # disease names in dataset use spaces and capitalization; normalize comparison
    disease = disease_slug.replace("_", " ").title()
    ddf = df[df["disease"].str.lower() == disease.lower()].copy()
    if len(ddf) < 2:
        return {"model_type": "regressor_weekly_state", "disease": disease, "error": "insufficient_rows"}

    train_df, test_df = time_based_split(ddf, test_fraction=0.2)
    X_test = select_features(test_df, FEATURE_COLUMNS)
    y_test = test_df[TARGET_COLUMN].values

    model_path = MODELS_DIR / f"outbreakiq_regressor_{disease_slug}.pkl"
    if not model_path.exists():
        return {"model_type": "regressor_weekly_state", "disease": disease, "error": f"model_not_found: {model_path.name}"}

    model = load(model_path)
    y_pred = model.predict(X_test)
    metrics = _reg_metrics("regressor_weekly_state", disease, y_test, y_pred, len(train_df), len(test_df))
    preds = _pred_rows_regression(
        model_type="regressor_weekly_state",
        disease=disease,
        test_df=test_df,
        y_true=y_test,
        y_pred=y_pred,
        keys=["year", "week", "state"],
    )
    return metrics, preds


def evaluate_regressor_weekly_country(disease_slug: str):
    df = _load_weekly_country()
    disease = disease_slug.replace("_", " ").title()
    ddf = df[df["disease"].str.lower() == disease.lower()].copy()
    if len(ddf) < 20:
        return {"model_type": "regressor_weekly_country", "disease": disease, "error": "insufficient_rows"}
    # time split
    n = len(ddf)
    cutoff = max(1, int(0.8 * n))
    train_df = ddf.iloc[:cutoff].copy()
    test_df = ddf.iloc[cutoff:].copy()
    feature_cols = ["who_country_cases", "cases_last_week", "week_sin", "week_cos", "year"]
    X_test = test_df[feature_cols].copy()
    y_test = test_df["cases"].values
    model_path = MODELS_DIR / f"outbreakiq_regressor_weekly_country_{disease_slug}.pkl"
    if not model_path.exists():
        return {"model_type": "regressor_weekly_country", "disease": disease, "error": f"model_not_found: {model_path.name}"}
    model = load(model_path)
    y_pred = model.predict(X_test)
    metrics = _reg_metrics("regressor_weekly_country", disease, y_test, y_pred, len(train_df), len(test_df))
    preds = _pred_rows_regression(
        model_type="regressor_weekly_country",
        disease=disease,
        test_df=test_df,
        y_true=y_test,
        y_pred=y_pred,
        keys=["year", "week"],
    )
    return metrics, preds


def evaluate_regressor_weekly_from_annual(disease_slug: str):
    annual = _load_who_annual_for_weekly()
    weekly = _make_weekly_from_annual(annual)
    disease = disease_slug.replace("_", " ").title()
    ddf = weekly[weekly["disease"].str.lower() == disease.lower()].copy()
    if len(ddf) < 100:
        return {"model_type": "regressor_weekly_from_annual", "disease": disease, "error": "insufficient_weekly_points"}
    n = len(ddf)
    cutoff = max(1, int(0.8 * n))
    train_df = ddf.iloc[:cutoff].copy()
    test_df = ddf.iloc[cutoff:].copy()
    feature_cols = ["who_country_cases", "cases_last_week", "week_sin", "week_cos", "year"]
    X_test = test_df[feature_cols].copy()
    y_test = test_df["cases"].values
    model_path = MODELS_DIR / f"outbreakiq_regressor_weekly_from_annual_{disease_slug}.pkl"
    if not model_path.exists():
        return {"model_type": "regressor_weekly_from_annual", "disease": disease, "error": f"model_not_found: {model_path.name}"}
    model = load(model_path)
    y_pred = model.predict(X_test)
    metrics = _reg_metrics("regressor_weekly_from_annual", disease, y_test, y_pred, len(train_df), len(test_df))
    preds = _pred_rows_regression(
        model_type="regressor_weekly_from_annual",
        disease=disease,
        test_df=test_df,
        y_true=y_test,
        y_pred=y_pred,
        keys=["year", "week"],
    )
    return metrics, preds


def evaluate_regressor_annual(disease_slug: str):
    df = _load_who_annual()
    disease = disease_slug.replace("_", " ").title()
    ddf = df[df["disease"].str.lower() == disease.lower()].copy()
    if len(ddf) < 5:
        return {"model_type": "regressor_annual", "disease": disease, "error": "insufficient_annual_rows"}
    n = len(ddf)
    cutoff = max(1, int(0.8 * n))
    train_df = ddf.iloc[:cutoff].copy()
    test_df = ddf.iloc[cutoff:].copy()
    X_test = test_df[["year", "cases_last_year"]].copy()
    y_test = test_df["cases"].values
    model_path = MODELS_DIR / f"outbreakiq_regressor_annual_{disease_slug}.pkl"
    if not model_path.exists():
        return {"model_type": "regressor_annual", "disease": disease, "error": f"model_not_found: {model_path.name}"}
    model = load(model_path)
    y_pred = model.predict(X_test)
    metrics = _reg_metrics("regressor_annual", disease, y_test, y_pred, len(train_df), len(test_df))
    preds = _pred_rows_regression(
        model_type="regressor_annual",
        disease=disease,
        test_df=test_df,
        y_true=y_test,
        y_pred=y_pred,
        keys=["year"],
    )
    return metrics, preds


def evaluate_classifier_weekly_state(disease_slug: str):
    df = load_dataset()
    df = _label_outbreak_next_week(df)
    disease = disease_slug.replace("_", " ").title()
    ddf = df[df["disease"].str.lower() == disease.lower()].copy()
    if len(ddf) < 20:
        return {"model_type": "classifier_weekly_state", "disease": disease, "error": "insufficient_rows"}
    train_df, test_df = time_based_split(ddf, test_fraction=0.2)
    X_test = select_features(test_df, FEATURE_COLUMNS)
    y_test = test_df["outbreak_next_week"].astype(int).values
    model_path = MODELS_DIR / f"outbreakiq_classifier_{disease_slug}.pkl"
    if not model_path.exists():
        return {"model_type": "classifier_weekly_state", "disease": disease, "error": f"model_not_found: {model_path.name}"}
    model = load(model_path)
    proba = model.predict_proba(X_test)
    if proba.shape[1] == 2:
        y_prob = proba[:, 1]
    else:
        classes = list(model.classes_)
        y_prob = np.ones(len(X_test)) if 1 in classes else np.zeros(len(X_test))
    if len(np.unique(y_test)) >= 2:
        roc = float(roc_auc_score(y_test, y_prob))
        pr_auc = float(average_precision_score(y_test, y_prob))
    else:
        roc = float("nan")
        pr_auc = float("nan")
    y_pred = (y_prob >= 0.5).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="binary", zero_division=0)
    metrics = {
        "model_type": "classifier_weekly_state",
        "disease": disease,
        "roc_auc": roc,
        "pr_auc": pr_auc,
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "n_train": int(len(train_df)),
        "n_test": int(len(test_df)),
    }
    preds = _pred_rows_classification(
        model_type="classifier_weekly_state",
        disease=disease,
        test_df=test_df,
        y_true=y_test,
        y_prob=y_prob,
        y_pred=y_pred,
        keys=["year", "week", "state"],
    )
    return metrics, preds


def _reg_metrics(model_type: str, disease: str, y_true, y_pred, n_train: int, n_test: int) -> dict:
    return {
        "model_type": model_type,
        "disease": disease,
        "r2": float(r2_score(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "n_train": int(n_train),
        "n_test": int(n_test),
    }


def _pred_rows_regression(model_type: str, disease: str, test_df: pd.DataFrame, y_true, y_pred, keys):
    rows = []
    for i in range(len(test_df)):
        row = {
            "model_type": model_type,
            "disease": disease,
            "y_true": float(y_true[i]) if np.isfinite(y_true[i]) else float("nan"),
            "y_pred": float(y_pred[i]) if np.isfinite(y_pred[i]) else float("nan"),
        }
        for k in keys:
            if k in test_df.columns:
                val = test_df.iloc[i][k]
                row[k] = int(val) if pd.api.types.is_integer(val) or str(val).isdigit() else (float(val) if pd.api.types.is_number(val) else str(val))
        rows.append(row)
    return rows


def _pred_rows_classification(model_type: str, disease: str, test_df: pd.DataFrame, y_true, y_prob, y_pred, keys):
    rows = []
    for i in range(len(test_df)):
        row = {
            "model_type": model_type,
            "disease": disease,
            "y_true": int(y_true[i]),
            "y_prob": float(y_prob[i]) if np.isfinite(y_prob[i]) else float("nan"),
            "y_pred": int(y_pred[i]),
        }
        for k in keys:
            if k in test_df.columns:
                val = test_df.iloc[i][k]
                row[k] = int(val) if pd.api.types.is_integer(val) or str(val).isdigit() else (float(val) if pd.api.types.is_number(val) else str(val))
        rows.append(row)
    return rows


def main():
    results = []
    pred_rows = []
    for path in MODELS_DIR.glob("*.pkl"):
        info = parse_model_filename(path)
        mtype = info["type"]
        disease_slug = info["disease"]
        if mtype == "unknown" or not disease_slug:
            results.append({"file": path.name, "error": "unknown_model_type"})
            continue
        try:
            if mtype == "regressor_weekly_state":
                metrics, preds = evaluate_regressor_weekly_state(disease_slug)
                results.append(metrics)
                pred_rows.extend(preds)
            elif mtype == "regressor_weekly_country":
                metrics, preds = evaluate_regressor_weekly_country(disease_slug)
                results.append(metrics)
                pred_rows.extend(preds)
            elif mtype == "regressor_weekly_from_annual":
                metrics, preds = evaluate_regressor_weekly_from_annual(disease_slug)
                results.append(metrics)
                pred_rows.extend(preds)
            elif mtype == "regressor_annual":
                metrics, preds = evaluate_regressor_annual(disease_slug)
                results.append(metrics)
                pred_rows.extend(preds)
            elif mtype == "classifier_weekly_state":
                metrics, preds = evaluate_classifier_weekly_state(disease_slug)
                results.append(metrics)
                pred_rows.extend(preds)
            else:
                results.append({"file": path.name, "error": f"unsupported_type:{mtype}"})
        except Exception as e:
            results.append({"file": path.name, "error": f"evaluation_failed: {e}"})

    # Save predictions CSV for downstream consumption
    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        pred_df = pd.DataFrame(pred_rows)
        pred_csv = REPORTS_DIR / "predictions_all_models.csv"
        pred_df.to_csv(pred_csv, index=False)
        print(f"Saved predictions → {pred_csv}")

        # Build best-by-disease compact CSV (recommended production mapping)
        best = {
            "Covid-19": ["regressor_weekly_state", "classifier_weekly_state"],
            "Cholera": ["regressor_weekly_from_annual"],
            "Measles": ["regressor_weekly_from_annual"],
            "Yellow Fever": ["regressor_weekly_from_annual"],
            "Malaria": ["regressor_weekly_from_annual"],
            "Meningitis": ["regressor_weekly_from_annual"],
        }
        best_rows = []
        for dis, models in best.items():
            df_dis = pred_df[(pred_df["disease"] == dis) & (pred_df["model_type"].isin(models))]
            if not df_dis.empty:
                best_rows.append(df_dis)
        if best_rows:
            best_df = pd.concat(best_rows, ignore_index=True)
            best_csv = REPORTS_DIR / "predictions_best_by_disease.csv"
            best_df.to_csv(best_csv, index=False)
            print(f"Saved best-by-disease → {best_csv}")
        else:
            print("[WARN] No rows matched best-by-disease selection.")
    except Exception as e:
        print(f"[WARN] Failed to write predictions CSV: {e}")

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()