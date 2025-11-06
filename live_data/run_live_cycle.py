from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from ml.utils import load_training, ensure_reports_dir, next_week


def run_realtime_predictions() -> Path:
    df = load_training()
    reports_dir = ensure_reports_dir()

    # Latest week per (state, disease)
    latest = df.sort_values(["disease", "state", "year", "week"]).groupby(["disease", "state"]).tail(1).copy()
    latest["pred_cases_next_week"] = latest["cases"].fillna(0)
    latest["pred_deaths_next_week"] = latest["deaths"].fillna(0)

    nxt = latest.apply(lambda r: pd.Series(next_week(int(r["year"]), int(r["week"]))), axis=1)
    nxt.columns = ["pred_year", "pred_week"]
    latest = pd.concat([latest.reset_index(drop=True), nxt], axis=1)

    out = reports_dir / "predictions_live.csv"
    cols = [
        "state", "disease", "pred_year", "pred_week", "pred_cases_next_week", "pred_deaths_next_week",
    ]
    latest[cols].to_csv(out, index=False)

    health = {
        "timestamp": int(time.time()),
        "status": "ok",
        "predictions": int(len(latest)),
    }
    (reports_dir / "health.json").write_text(pd.Series(health).to_json(indent=2), encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="realtime", choices=["realtime"], help="Run realtime predictions")
    args = parser.parse_args()
    if args.mode == "realtime":
        out = run_realtime_predictions()
        print(f"Predictions written to: {out}")


if __name__ == "__main__":
    main()