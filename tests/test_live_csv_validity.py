import pandas as pd
import pathlib
import pytest

from live_data.fetchers.who_api import (
    fetch_who_disease_timeseries,
    fetch_who_covid_timeseries,
)
from live_data.fetchers.worldbank_api import fetch_worldbank_population
from live_data.fetchers.ncdc_api import fetch_ncdc_outbreaks


def _read_csv_or_skip(path: str):
    p = pathlib.Path(path)
    if not p.exists():
        pytest.skip(f"Missing file: {path}")
    df = pd.read_csv(p)
    if df.empty:
        pytest.skip(f"Empty file: {path}")
    return df


def test_weather_daily_schema_and_no_nans():
    df = _read_csv_or_skip("data/live/weather_daily.csv")
    required = {
        "time",
        "temperature_2m_mean",
        "relative_humidity_2m_mean",
        "precipitation_sum",
    }
    assert required.issubset(set(df.columns))
    assert df[sorted(required)].isna().sum().sum() == 0


def test_who_disease_schema_and_no_nans():
    # Force rebuild to ensure cleaned schema
    fetch_who_disease_timeseries()
    df = _read_csv_or_skip("data/live/who_disease.csv")
    required = {"disease", "year", "country", "cases", "deaths"}
    assert required.issubset(set(df.columns))
    assert df[list(required)].isna().sum().sum() == 0


def test_worldbank_population_schema_and_no_nans():
    path = pathlib.Path("data/live/worldbank_population.csv")
    if not path.exists() or pd.read_csv(path).empty:
        fetch_worldbank_population()
    df = _read_csv_or_skip("data/live/worldbank_population.csv")
    required = {"country", "year", "total_population", "urban_percent"}
    assert required.issubset(set(df.columns))
    assert df[list(required)].isna().sum().sum() == 0
    assert df["urban_percent"].between(0, 100).all()


def test_ncdc_outbreaks_schema_and_no_nans():
    # Force rebuild to ensure cleaned schema
    fetch_ncdc_outbreaks()
    df = _read_csv_or_skip("data/live/ncdc_outbreaks.csv")
    required = {"disease", "state", "report_date", "week", "cases", "deaths"}
    assert required.issubset(set(df.columns))
    assert df[list(required)].isna().sum().sum() == 0


def test_latest_features_core_columns_and_no_nans():
    df = _read_csv_or_skip("data/live/latest_features.csv")
    required = {"disease", "state", "year", "week"}
    assert required.issubset(set(df.columns))
    # Ensure no NaNs in core features used for prediction if present
    core_feats = [
        "temperature_2m_mean",
        "relative_humidity_2m_mean",
        "precipitation_sum",
        "population",
        "urban_percent",
    ]
    present = [c for c in core_feats if c in df.columns]
    if present:
        assert df[present].isna().sum().sum() == 0