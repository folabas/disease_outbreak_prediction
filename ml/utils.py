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