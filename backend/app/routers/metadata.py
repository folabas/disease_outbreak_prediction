import os
from typing import List, Optional, Literal, Dict, Any

import pandas as pd
from fastapi import APIRouter, Query
import logging
from app.core.response import success
from app.core.validators import validate_disease

from app.core.config import DATA_DIR, REPORTS_DIR, ALLOWED_DISEASES


router = APIRouter()

# Simple in-memory cache for options to avoid repeated CSV reads
_CACHE: Dict[str, Any] = {}
_CACHE_TS: Optional[float] = None
_CACHE_TTL_SECONDS: int = 600  # 10 minutes


def _read_training_table() -> Optional[pd.DataFrame]:
    path = os.path.join(DATA_DIR, "outbreakiq_training_data_filled.csv")
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def _read_live_weather_state() -> Optional[pd.DataFrame]:
    path = os.path.join(DATA_DIR, "live", "weather_weekly_by_state.csv")
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        # Ensure a year column exists
        if "year" not in df.columns and "date" in df.columns:
            # Try to infer year from ISO date
            try:
                df["year"] = pd.to_datetime(df["date"]).dt.year
            except Exception:
                pass
        return df
    except Exception:
        return None


def _read_live_predictions() -> Optional[pd.DataFrame]:
    path = os.path.join(REPORTS_DIR, "predictions_live.csv")
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def _unique_sorted(series: pd.Series) -> List[Any]:
    try:
        values = sorted(set(v for v in series.dropna().tolist()))
        return values
    except Exception:
        return []


@router.get("/metadata/options")
def get_metadata_options(
    source: Literal["auto", "training", "live"] = Query(
        default="auto", description="Which dataset to use for options"
    ),
    disease: Optional[str] = Query(default=None, description="Optional disease filter"),
) -> Dict[str, Any]:
    logging.info("/metadata/options GET source=%s disease=%s", source, disease)
    """
    Return available diseases, years, and regions from real project data.

    - training: data/outbreakiq_training_data_filled.csv
    - live: data/live/weather_weekly_by_state.csv or reports/production/predictions_live.csv
    - auto: prefer training, else live, else empty with status
    """
    status: str = "missing"
    used_source: str = source
    diseases: List[str] = []
    years: List[int] = []
    regions: List[str] = []

    # Validate disease if provided
    _ = validate_disease(disease)

    # Serve from cache when available and source=auto (most common case)
    import time
    now = time.time()
    if source == "auto" and _CACHE and _CACHE_TS and (now - _CACHE_TS) < _CACHE_TTL_SECONDS:
        cached = _CACHE.copy()
        # If disease filter requested, narrow regions/years using training table only (best-effort)
        if disease:
            train_df = _read_training_table()
            if train_df is not None and "disease" in train_df.columns:
                sub = train_df[train_df["disease"] == disease]
                region_col = "state" if "state" in sub.columns else ("region" if "region" in sub.columns else None)
                year_col = "year" if "year" in sub.columns else None
                if region_col:
                    cached["data"]["regions"] = _unique_sorted(sub[region_col])
                if year_col:
                    cached["data"]["years"] = _unique_sorted(sub[year_col])
        cached["source"] = cached.get("source", "training")
        return cached

    # Resolve source
    train_df = _read_training_table()
    live_weather_df = _read_live_weather_state()
    live_preds_df = _read_live_predictions()

    if source == "auto":
        if train_df is not None:
            used_source = "training"
        elif live_weather_df is not None or live_preds_df is not None:
            used_source = "live"
        else:
            used_source = "none"

    # Extract depending on chosen source
    if used_source == "training" and train_df is not None:
        status = "ready"
        # Column names can vary: prefer explicit names
        disease_col = "disease" if "disease" in train_df.columns else None
        region_col = (
            "state"
            if "state" in train_df.columns
            else ("region" if "region" in train_df.columns else None)
        )
        year_col = "year" if "year" in train_df.columns else None

        if disease_col:
            diseases = _unique_sorted(train_df[disease_col])
        if region_col:
            regions = _unique_sorted(train_df[region_col])
        if year_col:
            years = _unique_sorted(train_df[year_col])

        # Optional filter by disease
        if disease and disease_col:
            sub = train_df[train_df[disease_col] == disease]
            if region_col:
                regions = _unique_sorted(sub[region_col])
            if year_col:
                years = _unique_sorted(sub[year_col])

    elif used_source == "live" and (live_weather_df is not None or live_preds_df is not None):
        status = "ready"
        # Weather weekly by state determines regions and years
        if live_weather_df is not None:
            if "state" in live_weather_df.columns:
                regions = _unique_sorted(live_weather_df["state"])
            if "year" in live_weather_df.columns:
                years = _unique_sorted(live_weather_df["year"])
        # Predictions can carry disease field and region
        if live_preds_df is not None:
            if "disease" in live_preds_df.columns:
                diseases = _unique_sorted(live_preds_df["disease"]) or diseases
            if not regions and "region" in live_preds_df.columns:
                regions = _unique_sorted(live_preds_df["region"]) or regions
            if not years and "year" in live_preds_df.columns:
                years = _unique_sorted(live_preds_df["year"]) or years

        # If diseases still empty, fall back to allowed set present in codebase (not dummy)
        if not diseases:
            diseases = sorted(ALLOWED_DISEASES)

    else:
        status = "missing"
        used_source = "none"

    result_data = {
        "source": used_source,
        "diseases": diseases,
        "years": years,
        "regions": regions,
    }

    # Update cache for auto resolution
    if source == "auto" and status == "ready":
        _CACHE = {"status": "success", "data": result_data.copy()}
        _CACHE_TS = now
    if status == "ready":
        return success(result_data)
    else:
        # When missing, still return a success with empty lists to keep contract stable
        return success(result_data, message="options missing; no source available")