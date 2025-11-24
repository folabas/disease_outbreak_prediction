from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple, Dict

import pandas as pd

try:
    from .features import FEATURES
except ImportError:
    from features import FEATURES  # type: ignore


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "outbreak_dataset.csv"
REPORTS_DIR = BASE_DIR / "reports" / "production"


def ensure_reports_dir() -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR


def load_training(path: Path = DATA_PATH) -> pd.DataFrame:
    """
    Load the merged training table if available; otherwise fall back to NCDC-only
    cleaned outbreaks and synthesize minimal feature columns.

    This enables realtime prediction stubs to run even when the full feature
    build has not been executed.
    """
    try:
        df = pd.read_csv(path)
        # Basic sanity: enforce expected columns and types
        expected = {
            "state",
            "disease",
            "year",
            "week",
            "cases",
            "deaths",
            "temperature_2m_mean",
            "relative_humidity_2m_mean",
            "precipitation_sum",
            "who_cases_national",
            "population",
            "urban_percent",
        }
        missing = expected - set(df.columns)
        if missing:
            raise ValueError(f"Training CSV missing columns: {sorted(missing)}")
    except Exception:
        # Fallback: try alternative merged datasets
        fallback_candidates = [
            BASE_DIR / "data" / "final_merged_datasets.csv",
        ]
        fallback_path = next((p for p in fallback_candidates if p.exists()), None)
        if fallback_path is None:
            raise FileNotFoundError(
                f"No training table available at {path} and no fallback datasets found. "
                "Expected files: data/outbreak_dataset.csv, data/final_merged_datasets.csv, or data/final_merged_with_wash.csv"
            )
        base = pd.read_csv(fallback_path).copy()
        # Ensure essential columns and types
        for c in ["year", "week", "cases", "deaths"]:
            base[c] = pd.to_numeric(base.get(c), errors="coerce")
        base = base.dropna(subset=["state", "disease", "year", "week"])  # type: ignore[arg-type]
        
        # Improved imputation strategy: use appropriate defaults based on feature type
        # Sort by state, disease, year, week for time-series operations
        base = base.sort_values(["disease", "state", "year", "week"]).reset_index(drop=True)
        
        # Time-series features: use forward-fill then backward-fill (carry last known value)
        time_series_features = [
            "temperature_2m_mean",
            "relative_humidity_2m_mean",
            "precipitation_sum",
        ]
        for col in time_series_features:
            if col not in base.columns:
                base[col] = None
            # Forward fill within each state/disease group
            if col in base.columns:
                base[col] = base.groupby(["disease", "state"])[col].ffill()
                # Backward fill for any remaining NaNs at the start
                base[col] = base.groupby(["disease", "state"])[col].bfill()
                # If still NaN, use group mean
                if base[col].isna().any():
                    group_means = base.groupby(["disease", "state"])[col].transform("mean")
                    base[col] = base[col].fillna(group_means)
                # Final fallback: use overall mean
                if base[col].isna().any():
                    base[col] = base[col].fillna(base[col].mean() if base[col].notna().any() else 0.0)
        
        # Static/demographic features: use group mean/median
        demographic_features = {
            "population": "mean",  # Use mean for population
            "urban_percent": "mean",  # Use mean for urban percent
        }
        for col, method in demographic_features.items():
            if col not in base.columns:
                base[col] = None
            if col in base.columns:
                if method == "mean":
                    # Fill with state-level mean
                    state_means = base.groupby("state")[col].transform("mean")
                    base[col] = base[col].fillna(state_means)
                    # Fallback to overall mean
                    if base[col].isna().any():
                        base[col] = base[col].fillna(base[col].mean() if base[col].notna().any() else 0.0)
        
        # National/aggregate features: use 0.0 as default (these are often sparse)
        national_features = ["who_cases_national"]
        for col in national_features:
            if col not in base.columns:
                base[col] = 0.0
            else:
                base[col] = base[col].fillna(0.0)
        
        df = base

    # Coerce numerics where appropriate
    for col in [
        "year",
        "week",
        "cases",
        "deaths",
        "temperature_2m_mean",
        "relative_humidity_2m_mean",
        "precipitation_sum",
        "who_cases_national",
        "population",
        "urban_percent",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["year", "week", "cases"]).copy()

    # Ensure all canonical feature columns exist with improved imputation
    missing_features = [c for c in FEATURES if c not in df.columns]
    
    # Categorize features for appropriate imputation
    time_series_feat = [f for f in FEATURES if any(x in f for x in ["temperature", "humidity", "precipitation", "cases", "deaths", "growth"])]
    demographic_feat = [f for f in FEATURES if any(x in f for x in ["population", "urban", "density"])]
    lag_feat = [f for f in FEATURES if any(x in f for x in ["last_week", "2w_avg", "mean_4w", "std_4w"])]
    disease_onehot = [f for f in FEATURES if f.startswith("disease_")]
    other_feat = [f for f in FEATURES if f not in time_series_feat + demographic_feat + lag_feat + disease_onehot]
    
    # Sort for time-series operations
    df = df.sort_values(["disease", "state", "year", "week"]).reset_index(drop=True)
    grp = df.groupby(["disease", "state"], sort=False)
    
    # Handle missing features by category
    for col in missing_features:
        if col in time_series_feat:
            # Time-series: forward-fill
            df[col] = grp[col].ffill().bfill() if col in df.columns else 0.0
            if col not in df.columns:
                df[col] = 0.0
        elif col in demographic_feat:
            # Demographic: use group mean
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = df[col].fillna(df.groupby("state")[col].transform("mean"))
                df[col] = df[col].fillna(df[col].mean() if df[col].notna().any() else 0.0)
        elif col in lag_feat:
            # Lag features: compute from base features if possible
            if col not in df.columns:
                df[col] = 0.0
        elif col in disease_onehot:
            # Disease one-hot: 0.0 is correct (only one disease per row is 1.0)
            df[col] = 0.0
        else:
            # Other features: use 0.0 as safe default
            df[col] = 0.0
    
    # Apply numeric coercion with improved fill strategy
    for col in FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # Only fill remaining NaNs (after coercion) with 0.0
            df[col] = df[col].fillna(0.0)

    # Sort for consistent grouping behaviour
    df = df.sort_values(["disease", "state", "year", "week"]).reset_index(drop=True)
    return df


def next_week(year: int, week: int) -> Tuple[int, int]:
    nxt_w = week + 1
    nxt_y = year
    if nxt_w > 53:
        nxt_w = 1
        nxt_y = year + 1
    return nxt_y, nxt_w


def write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)