"""
Generate a latest-week snapshot from predictions_best_by_disease.csv.

Logic:
- Prefer the production CSV at reports/production/predictions_best_by_disease.csv.
- Fallback to reports/predictions_best_by_disease.csv if production copy is missing.
- Compute the latest (year, week) across rows and filter to that snapshot.
- Save to reports/production/predictions_latest_week.csv.
"""

from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"
PROD_DIR = REPORTS_DIR / "production"


def main():
    prod_csv = PROD_DIR / "predictions_best_by_disease.csv"
    fallback_csv = REPORTS_DIR / "predictions_best_by_disease.csv"

    if prod_csv.exists():
        src = prod_csv
    elif fallback_csv.exists():
        src = fallback_csv
        print(f"[WARN] Using fallback predictions: {src}")
    else:
        print("[ERROR] No predictions_best_by_disease.csv found in production or reports.")
        sys.exit(1)

    df = pd.read_csv(src)

    # Ensure year/week columns exist and are numeric
    if "year" not in df.columns or "week" not in df.columns:
        print("[ERROR] Source CSV missing 'year' or 'week' columns.")
        sys.exit(1)

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["week"] = pd.to_numeric(df["week"], errors="coerce")
    df = df.dropna(subset=["year", "week"]).copy()

    if df.empty:
        print("[ERROR] No valid rows with year/week to snapshot.")
        sys.exit(1)

    latest_year = int(df["year"].max())
    latest_week = int(df[df["year"] == latest_year]["week"].max())

    snap = df[(df["year"] == latest_year) & (df["week"] == latest_week)].copy()
    PROD_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = PROD_DIR / "predictions_latest_week.csv"
    snap.to_csv(out_csv, index=False)
    print(f"Saved latest-week snapshot ({latest_year}-W{latest_week}) → {out_csv}")


if __name__ == "__main__":
    main()