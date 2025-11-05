from math import sin, cos, pi
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from ml.config import FEATURE_COLUMNS, DATA_PATH
from ml.data import load_dataset
from .standardize import read_csv, save_csv


def _derive_week_components(week: int) -> tuple[float, float]:
    # ISO weeks 1..53 mapped to [0, 2π)
    angle = 2 * pi * ((week - 1) / 52.0)
    return sin(angle), cos(angle)


def build_latest_features(diseases: Optional[list[str]] = None) -> pd.DataFrame:
    """Combine latest known rows with live source overrides to produce features.

    Strategy:
    - Load the merged training dataset; take the last available week per disease/state.
    - If live weather data is present, overwrite `temperature_2m_mean`, `precipitation_sum`,
      and `relative_humidity_2m_mean` with the most recent values.
    - Derive `week_sin`/`week_cos` for the next week to forecast.
    - Keep other feature columns from the last known row as a reasonable fallback.
    - Save a standardized features table under `data/live/latest_features.csv`.
    """
    df = load_dataset(Path(DATA_PATH))

    # Filter diseases if provided
    if diseases:
        df = df[df["disease"].isin(diseases)].copy()

    # Take the latest row per (disease, state)
    df = df.sort_values(["disease", "state", "year", "week"]).copy()
    latest = df.groupby(["disease", "state"], as_index=False).tail(1).reset_index(drop=True)

    # Forecast next week
    latest["week"] = latest["week"].astype(int) + 1
    # Handle week rollover naïvely (if 53 → 1 and increment year)
    rollover = latest["week"] > 53
    latest.loc[rollover, "week"] = 1
    latest.loc[rollover, "year"] = latest.loc[rollover, "year"].astype(int) + 1

    # Override weather metrics if live data is available
    weather = read_csv("weather_daily")
    if weather is not None and not weather.empty:
        # Use the most recent day
        weather_recent = weather.tail(1)
        for col in ["temperature_2m_mean", "precipitation_sum", "relative_humidity_2m_mean"]:
            if col in weather_recent.columns:
                latest[col] = float(weather_recent.iloc[0][col])

    # Derive cyclical week components
    ws, wc = zip(*latest["week"].astype(int).map(_derive_week_components))
    latest["week_sin"] = ws
    latest["week_cos"] = wc

    # Ensure all model feature columns exist; fill missing with 0
    for col in FEATURE_COLUMNS:
        if col not in latest.columns:
            latest[col] = 0.0
    # Coerce numeric feature types
    for col in FEATURE_COLUMNS:
        latest[col] = pd.to_numeric(latest[col], errors="coerce").fillna(0.0)

    # Persist standardized features table
    features = latest[["disease", "state", "year", "week"] + FEATURE_COLUMNS].copy()
    save_csv(features, "latest_features")
    return features