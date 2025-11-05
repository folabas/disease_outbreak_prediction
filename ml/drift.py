from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .config import PROJECT_ROOT, FEATURE_COLUMNS, REPORTS_DIR


def compute_drift(
    train_df: pd.DataFrame,
    live_df: pd.DataFrame,
    columns: List[str],
    threshold_std: float = 0.2,
) -> Dict[str, Dict[str, float]]:
    """Compute simple mean/std drift signal per column.

    Returns per-column metrics: train_mean, live_mean, train_std, abs_diff, ratio_std, drift_flag.
    drift_flag is 1.0 if abs_diff > threshold_std * train_std, else 0.0.
    """
    results: Dict[str, Dict[str, float]] = {}
    for col in columns:
        if col not in train_df.columns or col not in live_df.columns:
            continue
        t = pd.to_numeric(train_df[col], errors="coerce").dropna()
        l = pd.to_numeric(live_df[col], errors="coerce").dropna()
        if len(t) == 0 or len(l) == 0:
            continue
        t_mean, l_mean = float(t.mean()), float(l.mean())
        t_std = float(t.std(ddof=1)) if len(t) > 1 else 0.0
        abs_diff = abs(l_mean - t_mean)
        thresh = threshold_std * (t_std if t_std > 0 else 1.0)
        drift = 1.0 if abs_diff > thresh else 0.0
        results[col] = {
            "train_mean": t_mean,
            "live_mean": l_mean,
            "train_std": t_std,
            "abs_diff": abs_diff,
            "threshold": thresh,
            "drift_flag": drift,
        }
    return results


def _default_paths() -> Tuple[Path, Path, Path]:
    train_path = PROJECT_ROOT / "data" / "outbreakiq_training_data_filled.csv"
    live_path = PROJECT_ROOT / "data" / "live" / "latest_features.csv"
    report_path = REPORTS_DIR / "production" / "drift_report.json"
    return train_path, live_path, report_path


def main():
    train_path, live_path, report_path = _default_paths()
    train_df = pd.read_csv(train_path)
    live_df = pd.read_csv(live_path)

    # Choose numeric features subset
    numeric_cols = [c for c in FEATURE_COLUMNS if c in train_df.columns]
    results = compute_drift(train_df, live_df, numeric_cols, threshold_std=0.2)

    # Persist report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2))

    # Print summary
    drifted = [c for c, m in results.items() if m.get("drift_flag", 0.0) == 1.0]
    if drifted:
        print("[WARN] Drift detected in:", ", ".join(drifted))
    else:
        print("[OK] No drift flags raised at 0.2 std threshold")


if __name__ == "__main__":
    main()