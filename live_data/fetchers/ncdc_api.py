from typing import Optional

import pandas as pd

from ..standardize import append_and_dedupe, log_ingest, LIVE_DATA_DIR
from ..cleaners import clean_ncdc_outbreaks


def fetch_ncdc_outbreaks(source_csv_path: Optional[str] = None) -> Optional[pd.DataFrame]:
    """Standardize NCDC outbreaks situational reports.

    Saves to `data/live/ncdc_outbreaks.csv`.
    """
    try:
        if source_csv_path:
            df = pd.read_csv(source_csv_path)
        else:
            # Fallback to local consolidated file if available
            df = pd.read_csv("ncdc_outbreaks.csv")
        if not df.empty:
            df_clean = clean_ncdc_outbreaks(df)
            path = LIVE_DATA_DIR / "ncdc_outbreaks.csv"
            # Unique key: disease+state+report_date+week (where available)
            key_cols = [c for c in ["disease", "state", "report_date", "week"] if c in df_clean.columns]
            append_and_dedupe(path, df_clean, key_cols=key_cols)
            try:
                written = len(pd.read_csv(path))
            except Exception:
                written = len(df_clean)
            log_ingest(source="ncdc_outbreaks", new_rows=len(df_clean), written_rows=written, path=path)
        return df
    except Exception:
        return None