from pathlib import Path
from typing import Literal, Optional

import pandas as pd

from ml.config import REPORTS_DIR
from ml.predict_live import predict_live
from .build_features import build_latest_features


def run_cached_mode(best_csv: Optional[Path] = None) -> Path:
    """Copy cached best-by-disease predictions to production as current live output."""
    source = best_csv or (REPORTS_DIR / "production" / "predictions_best_by_disease.csv")
    if not source.exists():
        raise FileNotFoundError(f"Cached predictions not found: {source}")
    df = pd.read_csv(source)
    out_path = REPORTS_DIR / "production" / "predictions_live.csv"
    df.to_csv(out_path, index=False)
    return out_path


def run_realtime_mode(features_df: Optional[pd.DataFrame] = None) -> Path:
    """Build features if not provided, run live predictions, and save output."""
    if features_df is None:
        features_df = build_latest_features()
    preds = predict_live(features_df)
    out_path = REPORTS_DIR / "production" / "predictions_live.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    preds.to_csv(out_path, index=False)
    return out_path


def run(mode: Literal["cached", "realtime"] = "realtime") -> Path:
    if mode == "cached":
        return run_cached_mode()
    return run_realtime_mode()