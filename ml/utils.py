from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple, Dict

import pandas as pd


DATA_PATH = Path("data/outbreakiq_training_data_filled.csv")
REPORTS_DIR = Path("reports/production")


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
        # Fallback: build a minimal frame from NCDC-only data
        ncdc_candidates = [
            Path("data/ncdc_outbreaks_clean.csv"),
            Path("data/raw/ncdc_outbreaks_clean.csv"),
        ]
        ncdc_path = next((p for p in ncdc_candidates if p.exists()), None)
        if ncdc_path is None:
            raise FileNotFoundError(
                "No training table available and NCDC fallback not found. "
                "Run rebuild_dataset.py and build_features.py first."
            )
        base = pd.read_csv(ncdc_path).copy()
        # Ensure essential columns and types
        for c in ["year", "week", "cases", "deaths"]:
            base[c] = pd.to_numeric(base.get(c), errors="coerce")
        base = base.dropna(subset=["state", "disease", "year", "week"])  # type: ignore[arg-type]
        # Synthesize minimal feature columns with safe defaults
        synth_cols = {
            "temperature_2m_mean": 0.0,
            "relative_humidity_2m_mean": 0.0,
            "precipitation_sum": 0.0,
            "who_cases_national": 0.0,
            "population": 0.0,
            "urban_percent": 0.0,
        }
        for col, default in synth_cols.items():
            if col not in base.columns:
                base[col] = default
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