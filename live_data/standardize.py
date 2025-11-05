from pathlib import Path
from typing import Optional, List

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LIVE_DATA_DIR = PROJECT_ROOT / "data" / "live"


def ensure_dirs():
    LIVE_DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_csv(df: pd.DataFrame, name: str) -> Path:
    """Save a DataFrame to `data/live/{name}.csv` and return the path.

    - Creates directories if needed
    - Ensures index is not saved
    """
    ensure_dirs()
    path = LIVE_DATA_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    return path


def append_and_dedupe(path: Path, new_df: pd.DataFrame, key_cols: List[str]) -> Path:
    """Append new_df to CSV at path, dedupe by key_cols, and save.

    - Creates directories if needed
    - Returns the file path
    """
    ensure_dirs()
    if path.exists():
        try:
            old = pd.read_csv(path)
        except Exception:
            old = pd.DataFrame(columns=new_df.columns)
        # Align old columns to new_df schema to enforce canonical columns
        old_aligned = old.reindex(columns=new_df.columns)
        combined = pd.concat([old_aligned, new_df], ignore_index=True)
    else:
        combined = new_df.copy()
    if key_cols:
        # Remove rows missing key values to avoid persisting incomplete legacy entries
        combined = combined.dropna(subset=key_cols)
        combined = combined.drop_duplicates(subset=key_cols, keep="last")
    # Fill NaNs in numeric columns to enforce no-NaN guarantees for production consumers
    num_cols = combined.select_dtypes(include=["number"]).columns.tolist()
    if num_cols:
        combined[num_cols] = combined[num_cols].fillna(0)
    combined.to_csv(path, index=False)
    return path


def log_ingest(source: str, new_rows: int, written_rows: int, path: Path) -> None:
    """Append a simple ingest log entry under data/live/ingest_log.csv."""
    ensure_dirs()
    log_path = LIVE_DATA_DIR / "ingest_log.csv"
    row = {
        "timestamp": pd.Timestamp.utcnow().isoformat(),
        "source": source,
        "new_rows": int(new_rows),
        "written_rows": int(written_rows),
        "target": str(path),
    }
    try:
        if log_path.exists():
            df = pd.read_csv(log_path)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])
        df.to_csv(log_path, index=False)
    except Exception:
        # Best-effort logging; ignore failures
        pass


def read_csv(name: str) -> Optional[pd.DataFrame]:
    """Read `data/live/{name}.csv` if present, else return None."""
    path = LIVE_DATA_DIR / f"{name}.csv"
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None