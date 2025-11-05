import warnings
import re
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

from .config import DATA_PATH, NIGERIA_STATES


def load_dataset(csv_path: Optional[Path] = None) -> pd.DataFrame:
    """Load the merged OutbreakIQ training dataset and perform basic cleaning.

    - Ensures date columns are parsed
    - Filters to valid Nigeria states
    - Drops clearly malformed rows
    """
    path = csv_path or DATA_PATH
    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise RuntimeError(f"Failed to read dataset at {path}: {e}")

    # Parse date columns when present
    if "report_date" in df.columns:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")

    # Ensure week column is integer where possible
    if "week" in df.columns:
        df["week"] = pd.to_numeric(df["week"], errors="coerce").astype("Int64")

    # Normalize and keep only realistic state names
    if "state" in df.columns:
        def normalize_state(x: str) -> str:
            s = str(x).strip()
            s = re.sub(r"\s+", " ", s)  # collapse multiple spaces
            s_low = s.lower()
            # common synonyms/mappings
            synonyms = {
                "fct": "Abuja",
                "f.c.t": "Abuja",
                "abj": "Abuja",
                "federal capital territory": "Abuja",
                "crossriver": "Cross River",
                "akwaibom": "Akwa Ibom",
                "ogun state": "Ogun",
                "ondo state": "Ondo",
                "oyo state": "Oyo",
            }
            if s_low in synonyms:
                return synonyms[s_low]
            # title case after normalization
            s = s.title()
            # fix known spacing variants
            s = s.replace("Akwa  Ibom", "Akwa Ibom")
            s = s.replace("Cross  River", "Cross River")
            return s

        df["state"] = df["state"].apply(normalize_state)
        df = df[df["state"].isin(NIGERIA_STATES)]

    # Drop rows with missing core fields
    core_cols = ["week", "disease", "state", "year", "cases"]
    for c in core_cols:
        if c not in df.columns:
            raise ValueError(f"Missing expected column '{c}' in dataset")
    df = df.dropna(subset=core_cols)

    # Sort by time for stable splitting
    sort_cols = [c for c in ["report_date", "year", "week"] if c in df.columns]
    df = df.sort_values(by=sort_cols).reset_index(drop=True)

    return df


def get_diseases(df: pd.DataFrame) -> List[str]:
    """Return list of diseases available in the dataset."""
    return sorted(df["disease"].dropna().unique().tolist())


def time_based_split(df: pd.DataFrame, test_fraction: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the dataset into train and test by time order.

    Keeps earlier records for training and later records for testing.
    """
    n = len(df)
    cutoff_idx = max(1, int((1.0 - test_fraction) * n))
    train_df = df.iloc[:cutoff_idx].copy()
    test_df = df.iloc[cutoff_idx:].copy()
    return train_df, test_df


def select_features(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """Select features, coercing numeric types and filling remaining NaNs with 0."""
    X = df[feature_cols].copy()
    for col in feature_cols:
        X[col] = pd.to_numeric(X[col], errors="coerce")
    return X.fillna(0.0)