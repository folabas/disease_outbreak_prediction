from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from joblib import load

from .config import FEATURE_COLUMNS, MODELS_DIR
from .data import select_features


def _disease_slug(name: str) -> str:
    return name.replace(" ", "_").lower()


def _available_models() -> Dict[str, Dict[str, Path]]:
    """Discover available trained models and map per disease.

    Returns: {disease: {"reg": path?, "clf": path?}} using supported types.
    """
    mapping: Dict[str, Dict[str, Path]] = {}
    for p in MODELS_DIR.glob("*.pkl"):
        fname = p.name
        parts = fname.split("_")
        if len(parts) < 3:
            continue
        # outbreakiq_{type}_{disease}.pkl (type may include extra parts)
        typ = parts[1]
        if typ == "regressor":
            # weekly_state regressor
            disease = fname.replace("outbreakiq_regressor_", "").replace(".pkl", "")
            mapping.setdefault(disease, {})["reg"] = p
        elif typ == "classifier":
            disease = fname.replace("outbreakiq_classifier_", "").replace(".pkl", "")
            mapping.setdefault(disease, {})["clf"] = p
        elif typ == "regressor":
            # handled above
            pass
        elif fname.startswith("outbreakiq_regressor_weekly_from_annual_"):
            disease = fname.replace("outbreakiq_regressor_weekly_from_annual_", "").replace(".pkl", "")
            mapping.setdefault(disease, {})["reg"] = p
    return mapping


def predict_live(features_df: pd.DataFrame, diseases: Optional[List[str]] = None) -> pd.DataFrame:
    """Run live predictions across diseases using available trained models.

    - Selects features by `FEATURE_COLUMNS` and fills missing values.
    - Loads per-disease regressors to predict weekly cases.
    - Uses per-disease classifiers (if available) to compute outbreak risk probability.
    - Returns a tidy DataFrame keyed by `disease`, `state`, `year`, `week`.
    """
    # Normalize disease filter to slugs
    disease_filter = None
    if diseases:
        disease_filter = set(_disease_slug(d) for d in diseases)

    models = _available_models()

    rows = []
    def _safe_int(val: object, default: int = 0) -> int:
        try:
            num = pd.to_numeric(val, errors="coerce")
            if pd.isna(num):
                return default
            return int(num)
        except Exception:
            return default

    for _, row in features_df.iterrows():
        disease_name = str(row["disease"]) if "disease" in row else ""
        disease_name = disease_name.strip()
        state = str(row["state"]) if "state" in row else ""
        state = state.strip()
        year = _safe_int(row["year"], default=0) if "year" in row else 0
        week = _safe_int(row["week"], default=0) if "week" in row else 0
        slug = _disease_slug(disease_name)
        if disease_filter and slug not in disease_filter:
            continue
        m = models.get(slug)
        if not m:
            continue
        # Select features using a dict to avoid index issues
        feat_dict = {col: row[col] if col in row.index else 0.0 for col in FEATURE_COLUMNS}
        X = select_features(pd.DataFrame([feat_dict]), FEATURE_COLUMNS)

        cases_pred = np.nan
        risk_prob = np.nan

        # Regression
        if "reg" in m:
            try:
                reg = load(m["reg"])  # type: ignore[arg-type]
                y_pred = reg.predict(X)
                cases_pred = float(y_pred[0]) if len(y_pred) else np.nan
            except Exception:
                cases_pred = np.nan

        # Classification (risk probability)
        if "clf" in m:
            try:
                clf = load(m["clf"])  # type: ignore[arg-type]
                proba = clf.predict_proba(X)
                if proba.shape[1] >= 2:
                    risk_prob = float(proba[0, 1])
                else:
                    # Fallback if model reports single-class
                    risk_prob = float(proba[0, 0]) if proba.size else np.nan
            except Exception:
                risk_prob = np.nan

        rows.append({
            "disease": disease_name,
            "state": state,
            "year": year,
            "week": week,
            "cases_pred": cases_pred,
            "outbreak_risk_prob": risk_prob,
        })

    return pd.DataFrame(rows)