from typing import Optional

import pandas as pd

from ..standardize import append_and_dedupe, log_ingest, LIVE_DATA_DIR
from ..cleaners import clean_who_disease, clean_who_covid


def fetch_who_disease_timeseries(source_csv_path: Optional[str] = None) -> Optional[pd.DataFrame]:
    """Standardize WHO disease/outbreak timeseries.

    If `source_csv_path` is provided, read from it; otherwise attempt to read
    the existing consolidated `data/who_disease_data.csv` maintained offline.

    Saves to `data/live/who_disease.csv`.
    """
    try:
        if source_csv_path:
            df = pd.read_csv(source_csv_path)
        else:
            df = pd.read_csv("data/who_disease_data.csv")
        if not df.empty:
            df_clean = clean_who_disease(df)
            path = LIVE_DATA_DIR / "who_disease.csv"
            append_and_dedupe(path, df_clean, key_cols=["disease", "year", "country"])
            # Log with best-effort; count written rows from file
            try:
                written = len(pd.read_csv(path))
            except Exception:
                written = len(df_clean)
            log_ingest(source="who_disease", new_rows=len(df_clean), written_rows=written, path=path)
        return df
    except Exception:
        return None


def fetch_who_covid_timeseries(source_csv_path: Optional[str] = None) -> Optional[pd.DataFrame]:
    """Standardize WHO Covid-19 timeseries (country-level).

    Saves to `data/live/who_covid.csv`.
    """
    try:
        if source_csv_path:
            df = pd.read_csv(source_csv_path)
        else:
            df = pd.read_csv("data/who_covid19_data.csv")
        if not df.empty:
            df_clean = clean_who_covid(df)
            path = LIVE_DATA_DIR / "who_covid.csv"
            append_and_dedupe(path, df_clean, key_cols=["date", "country"])
            try:
                written = len(pd.read_csv(path))
            except Exception:
                written = len(df_clean)
            log_ingest(source="who_covid", new_rows=len(df_clean), written_rows=written, path=path)
        return df
    except Exception:
        return None