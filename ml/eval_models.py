from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from .utils import load_training, ensure_reports_dir, write_json


def compute_simple_drift(df: pd.DataFrame) -> dict:
    # Compares recent 26 weeks vs historical for key features
    if df.empty:
        return {"status": "empty"}

    df = df.copy()
    df["date_order"] = df["year"] * 100 + df["week"].fillna(0)
    df = df.sort_values(["date_order"]).reset_index(drop=True)

    recent = df.tail(min(26, len(df)))
    hist = df.iloc[: max(len(df) - len(recent), 0)]

    def drift_score(col: str) -> float:
        if hist.empty or recent.empty:
            return float("nan")
        mu_h = hist[col].mean()
        mu_r = recent[col].mean()
        sd_h = hist[col].std() or 1.0
        return abs(mu_r - mu_h) / sd_h

    features = [
        "cases",
        "deaths",
        "temperature_2m_mean",
        "relative_humidity_2m_mean",
        "precipitation_sum",
        "who_cases_national",
    ]
    drift = {f"drift_{c}": drift_score(c) for c in features}
    drift.update({
        "timestamp": int(time.time()),
        "status": "ok",
        "rows": int(len(df)),
    })
    return drift


def main():
    df = load_training()
    reports_dir = ensure_reports_dir()
    drift = compute_simple_drift(df)
    write_json(reports_dir / "drift_report.json", drift)
    print(f"Drift report written to: {reports_dir / 'drift_report.json'}")


if __name__ == "__main__":
    main()