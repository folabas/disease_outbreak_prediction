from datetime import date, timedelta
from typing import Optional

import pandas as pd
import requests

from ..standardize import append_and_dedupe, log_ingest, LIVE_DATA_DIR
from ..cleaners import clean_weather_daily


OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/era5"


def fetch_daily(lat: float, lon: float, start: str, end: str, timezone: str = "Africa/Lagos") -> Optional[pd.DataFrame]:
    """Fetch daily weather metrics and save standardized CSV.

    Output columns: `time`, `temperature_2m_mean`, `precipitation_sum`, `relative_humidity_2m_mean`.
    Saved to `data/live/weather_daily.csv`.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": "temperature_2m_mean,precipitation_sum,relative_humidity_2m_mean",
        "timezone": timezone,
    }
    try:
        r = requests.get(OPEN_METEO_ARCHIVE_URL, params=params, timeout=60)
        r.raise_for_status()
        daily = r.json().get("daily", {})
        df = pd.DataFrame(daily)
        if not df.empty:
            df_clean = clean_weather_daily(df)
            path = LIVE_DATA_DIR / "weather_daily.csv"
            append_and_dedupe(path, df_clean, key_cols=["time"])
            log_ingest(source="weather_daily", new_rows=len(df_clean), written_rows=len(pd.read_csv(path)), path=path)
        return df
    except Exception:
        return None


def fetch_latest_week(lat: float, lon: float, timezone: str = "Africa/Lagos") -> Optional[pd.DataFrame]:
    """Convenience wrapper to fetch the last 7 days of weather data."""
    end = date.today()
    start = end - timedelta(days=7)
    return fetch_daily(lat=lat, lon=lon, start=start.isoformat(), end=end.isoformat(), timezone=timezone)