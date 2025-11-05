import pandas as pd
import numpy as np

from live_data.cleaners import (
    clean_weather_daily,
    clean_who_disease,
    clean_who_covid,
    clean_ncdc_outbreaks,
    clean_worldbank_population,
)


def test_clean_weather_daily_handles_nans_and_types():
    df = pd.DataFrame(
        {
            "time": ["2025-11-01", None, "2025-11-02"],
            "temperature_2m_mean": ["25.5", np.nan, 27],
            "relative_humidity_2m_mean": [np.nan, "60", None],
            "precipitation_sum": [None, "1.2", ""],
        }
    )
    out = clean_weather_daily(df)
    # Drops row without time
    assert out["time"].isna().sum() == 0
    # Coerces to numeric
    assert pd.api.types.is_numeric_dtype(out["temperature_2m_mean"]) 
    assert pd.api.types.is_numeric_dtype(out["relative_humidity_2m_mean"]) 
    assert pd.api.types.is_numeric_dtype(out["precipitation_sum"]) 
    # Fills NaNs as specified
    assert out["precipitation_sum"].min() >= 0.0


def test_clean_who_disease_normalizes_and_fills():
    df = pd.DataFrame(
        {
            "disease": ["cholera", "malaria"],
            "year": [2023, 2024],
            "country": ["Nigeria", "Nigeria"],
            "cases": [None, "100"],
            "deaths": ["", None],
        }
    )
    out = clean_who_disease(df)
    # Required columns exist
    for col in ["disease", "year", "country", "cases", "deaths"]:
        assert col in out.columns
    # Numeric coercion and fill
    assert out["cases"].dtype.kind in "fi"
    assert out["deaths"].dtype.kind in "fi"
    assert out["cases"].isna().sum() == 0
    assert out["deaths"].isna().sum() == 0


def test_clean_who_covid_basic():
    df = pd.DataFrame(
        {
            "date": ["2024-12-01", "2024-12-08"],
            "country": ["Nigeria", "Nigeria"],
            "new_cases": ["10", None],
            "new_deaths": [None, "0"],
            "cumulative_cases": ["100", "110"],
            "cumulative_deaths": [None, "1"],
            "year": [2024, 2024],
        }
    )
    out = clean_who_covid(df)
    required = {
        "date",
        "country",
        "new_cases",
        "new_deaths",
        "cumulative_cases",
        "cumulative_deaths",
        "year",
    }
    assert required.issubset(set(out.columns))
    assert out[list(required - {"date", "country"})].isna().sum().sum() == 0


def test_clean_ncdc_outbreaks_state_validation_and_fill():
    df = pd.DataFrame(
        {
            "disease": ["cholera", "cholera"],
            "state": ["Lagos", "UnknownState"],
            "report_date": ["2024-05-01", "2024-05-08"],
            "week": [18, 19],
            "cases": ["5", None],
            "deaths": [None, "1"],
        }
    )
    out = clean_ncdc_outbreaks(df)
    # Drops unknown states
    assert (out["state"] == "UnknownState").sum() == 0
    # Numeric coercion and fill
    assert out["cases"].isna().sum() == 0
    assert out["deaths"].isna().sum() == 0


def test_clean_worldbank_population_interpolation_and_bounds():
    df = pd.DataFrame(
        {
            "country": ["Nigeria", "Nigeria", "Nigeria"],
            "year": [2020, 2021, 2022],
            "total_population": [200_000_000, None, 210_000_000],
            "urban_percent": [51.0, None, 53.0],
        }
    )
    out = clean_worldbank_population(df)
    assert out["total_population"].isna().sum() == 0
    assert out["urban_percent"].isna().sum() == 0
    assert out["urban_percent"].between(0, 100).all()