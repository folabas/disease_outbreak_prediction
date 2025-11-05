from __future__ import annotations

from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from ml.config import NIGERIA_STATES


def clean_weather_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Clean Open-Meteo daily weather dataframe.

    - Ensure required columns exist
    - Cast numeric columns
    - Fill NaNs (ffill → bfill → median for temp/RH, 0 for precipitation)
    - Drop rows without a valid `time`
    """
    df = df.copy()
    # Expected columns may include: time, temperature_2m_mean, precipitation_sum, relative_humidity_2m_mean
    for col in ["temperature_2m_mean", "precipitation_sum", "relative_humidity_2m_mean"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "temperature_2m_mean" in df.columns:
        df["temperature_2m_mean"] = (
            df["temperature_2m_mean"].ffill()
            .bfill()
        )
        if df["temperature_2m_mean"].isna().any():
            median = pd.to_numeric(df["temperature_2m_mean"], errors="coerce").median()
            df["temperature_2m_mean"] = df["temperature_2m_mean"].fillna(median)

    if "relative_humidity_2m_mean" in df.columns:
        df["relative_humidity_2m_mean"] = (
            df["relative_humidity_2m_mean"].ffill()
            .bfill()
        )
        if df["relative_humidity_2m_mean"].isna().any():
            median = pd.to_numeric(df["relative_humidity_2m_mean"], errors="coerce").median()
            df["relative_humidity_2m_mean"] = df["relative_humidity_2m_mean"].fillna(median)

    if "precipitation_sum" in df.columns:
        df["precipitation_sum"] = df["precipitation_sum"].fillna(0.0)

    # Drop rows without time
    if "time" in df.columns:
        df = df.dropna(subset=["time"]).copy()
    return df


def _normalize_state(name: str) -> str:
    s = str(name).strip()
    s = " ".join(s.split())  # collapse whitespace
    s_low = s.lower()
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
    s = s.title()
    s = s.replace("Akwa  Ibom", "Akwa Ibom").replace("Cross  River", "Cross River")
    return s


def clean_ncdc_outbreaks(df: pd.DataFrame) -> pd.DataFrame:
    """Clean NCDC situational reports dataframe.

    - Coerce numeric counts; fill NaNs with 0
    - Normalize states and keep only valid Nigeria states
    - Parse report_date; compute ISO week when missing
    - Keep core columns: week, disease, state, cases, deaths, cfr, report_date
    """
    df = df.copy()
    # Normalize columns present
    for col in ["cases", "deaths", "cfr"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # Normalize state values
    if "state" in df.columns:
        df["state"] = df["state"].apply(_normalize_state)
        df = df[df["state"].isin(NIGERIA_STATES)].copy()

    # Parse report_date if present
    if "report_date" in df.columns:
        df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
    else:
        df["report_date"] = pd.NaT

    # Derive week from report_date if missing or non-numeric
    if "week" in df.columns:
        df["week"] = pd.to_numeric(df["week"], errors="coerce")
    else:
        df["week"] = np.nan

    need_week = df["week"].isna()
    if need_week.any():
        # compute ISO week for rows with valid date
        def iso_week(dt: Optional[pd.Timestamp]) -> Optional[int]:
            if pd.isna(dt):
                return None
            try:
                return int(datetime.isocalendar(dt).week)  # type: ignore[attr-defined]
            except Exception:
                return None

        df.loc[need_week, "week"] = df.loc[need_week, "report_date"].apply(iso_week)

    # Ensure core fields exist
    for col in ["disease", "state", "week"]:
        if col not in df.columns:
            df[col] = np.nan
    # Drop rows without core identifiers and a valid report_date
    df = df.dropna(subset=["disease", "state", "week", "report_date"]).copy()

    # Coerce week to int
    df["week"] = pd.to_numeric(df["week"], errors="coerce").astype(int)

    # Final column order
    cols = [c for c in ["week", "disease", "state", "cases", "deaths", "cfr", "report_date"] if c in df.columns]
    return df[cols].copy()


def clean_who_disease(df: pd.DataFrame) -> pd.DataFrame:
    """Clean WHO annual disease data.

    - Keep Nigeria rows (country 'NGA' or 'Nigeria')
    - Coerce year and cases to numeric; fill NaNs
    - Ensure columns: disease, year, country, cases, deaths
    - Standardize country to ISO3 'NGA'
    """
    df = df.copy()
    # Normalize country
    if "country" in df.columns:
        df["country"] = df["country"].astype(str)
        df["country_norm"] = df["country"].str.upper().replace({"NIGERIA": "NGA"})
    else:
        df["country_norm"] = "NGA"

    df = df[df["country_norm"] == "NGA"].copy()

    # Coerce numeric
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    else:
        df["year"] = pd.NA
    if "cases" in df.columns:
        df["cases"] = pd.to_numeric(df["cases"], errors="coerce").fillna(0.0)
    else:
        df["cases"] = 0.0

    # Deaths may not be present; fill 0
    if "deaths" in df.columns:
        df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce").fillna(0.0)
    else:
        df["deaths"] = 0.0

    df = df.dropna(subset=["year", "disease"]).copy()
    df["year"] = df["year"].astype(int)

    # Rename country_norm -> country and select canonical columns
    df = df.rename(columns={"country_norm": "country"})
    cols = [c for c in ["disease", "year", "country", "cases", "deaths"] if c in df.columns]
    return df[cols].copy()


def clean_who_covid(df: pd.DataFrame) -> pd.DataFrame:
    """Clean WHO Covid-19 timeseries.

    - Ensure numeric counts and year
    - If country missing, set to 'NGA' (Nigeria) for local dataset
    - Keep columns: date, country, new_cases, new_deaths, cumulative_cases, cumulative_deaths, year
    - Drop rows missing date
    """
    df = df.copy()
    # Default country
    if "country" not in df.columns:
        df["country"] = "NGA"
    else:
        df["country"] = df["country"].astype(str).str.upper().replace({"NIGERIA": "NGA"})

    # Numeric coercion
    for c in ["new_cases", "cumulative_cases", "new_deaths", "cumulative_deaths", "year"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Fill NaNs
    for c in ["new_cases", "cumulative_cases", "new_deaths", "cumulative_deaths"]:
        if c in df.columns:
            df[c] = df[c].fillna(0.0)
    if "year" in df.columns:
        df["year"] = df["year"].ffill().bfill()

    # Drop rows without date
    if "date" in df.columns:
        df = df.dropna(subset=["date"]).copy()

    cols = [c for c in ["date", "country", "new_cases", "new_deaths", "cumulative_cases", "cumulative_deaths", "year"] if c in df.columns]
    return df[cols].copy()


def clean_worldbank_population(df: pd.DataFrame) -> pd.DataFrame:
    """Clean World Bank population/demographics.

    - Ensure uppercase ISO3 country codes for 'NGA' if country string present
    - Fill population via forward-fill; urban_percent interpolate and clamp [0, 100]
    - Keep columns: country, year, total_population, urban_percent
    """
    df = df.copy()
    if "country" in df.columns:
        df["country"] = df["country"].astype(str)
        # Map common names to ISO3 for Nigeria
        df["country"] = df["country"].str.upper().replace({"NIGERIA": "NGA"})

    for c in ["year", "total_population", "urban_percent"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "total_population" in df.columns:
        df = df.sort_values(["country", "year"]).copy()
        df["total_population"] = df.groupby("country")["total_population"].ffill().bfill()

    if "urban_percent" in df.columns:
        df = df.sort_values(["country", "year"]).copy()
        df["urban_percent"] = (
            df.groupby("country")["urban_percent"]
            .transform(lambda s: s.interpolate(limit_direction="both"))
            .clip(lower=0.0, upper=100.0)
        )

    cols = [c for c in ["country", "year", "total_population", "urban_percent"] if c in df.columns]
    return df[cols].copy()