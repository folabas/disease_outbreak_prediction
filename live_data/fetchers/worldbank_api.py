from typing import Optional

import pandas as pd

from ..standardize import append_and_dedupe, log_ingest, LIVE_DATA_DIR
from ..cleaners import clean_worldbank_population


def fetch_worldbank_population(source_csv_path: Optional[str] = None) -> Optional[pd.DataFrame]:
    """Standardize World Bank population/demographics.

    Saves to `data/live/worldbank_population.csv`.
    """
    try:
        if source_csv_path:
            df = pd.read_csv(source_csv_path)
        else:
            df = pd.read_csv("data/worldbank_population.csv")
        if not df.empty:
            df_clean = clean_worldbank_population(df)
            path = LIVE_DATA_DIR / "worldbank_population.csv"
            append_and_dedupe(path, df_clean, key_cols=["country", "year"])
            try:
                written = len(pd.read_csv(path))
            except Exception:
                written = len(df_clean)
            log_ingest(source="worldbank_population", new_rows=len(df_clean), written_rows=written, path=path)
        return df
    except Exception:
        return None