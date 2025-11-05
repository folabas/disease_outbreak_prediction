"""
Fill NaN values and remove empty rows/columns in outbreakiq_training_data.csv.

Outputs:
- data/processed/outbreakiq_training_data_filled.csv
- reports/missing_values_before.csv
- reports/missing_values_after.csv
- reports/fill_missing_summary.txt
"""

from pathlib import Path
import pandas as pd
import numpy as np


DATA_DIR = Path("data")
REPORTS_DIR = Path("reports")
OUTPUT_DIR = DATA_DIR / "processed"


def ensure_dirs():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_df() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "outbreakiq_training_data.csv")
    # Normalize key strings
    if "state" in df.columns:
        df["state"] = df["state"].astype(str).str.strip().str.title()
    if "disease" in df.columns:
        df["disease"] = df["disease"].astype(str).str.strip().str.title()
    # Parse date
    if "report_date" in df.columns:
        df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
    return df


def save_missing(df: pd.DataFrame, path: Path):
    df.isna().sum().sort_values(ascending=False).to_csv(path, header=["missing_count"])


def drop_empty(df: pd.DataFrame) -> pd.DataFrame:
    # Drop columns entirely empty (all NaN)
    non_empty_cols = [c for c in df.columns if not df[c].isna().all()]
    df = df[non_empty_cols]
    # Drop rows entirely empty (all NaN)
    df = df.dropna(how="all")
    return df


def fill_year_week(df: pd.DataFrame) -> pd.DataFrame:
    # Derive year/week from report_date if missing
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
    else:
        df["year"] = pd.NA
    if "week" in df.columns:
        df["week"] = pd.to_numeric(df["week"], errors="coerce")
    else:
        df["week"] = pd.NA

    has_date = df["report_date"].notna()
    df.loc[has_date & df["year"].isna(), "year"] = df.loc[has_date, "report_date"].dt.year
    df.loc[has_date & df["week"].isna(), "week"] = df.loc[has_date, "report_date"].dt.isocalendar().week.astype(int)

    # Group-wise fill remaining year/week using mode/median
    for col in ["year", "week"]:
        # Group by state+disease when available
        if {"state", "disease"}.issubset(df.columns):
            grp = df.groupby(["state", "disease"])[col]
            # use mode (most common); fallback to median if no mode
            mode_vals = grp.transform(lambda s: s.mode().iloc[0] if not s.mode().empty else s.median())
            df[col] = df[col].fillna(mode_vals)
        # Global fallback
        global_mode = df[col].mode()
        if not global_mode.empty:
            df[col] = df[col].fillna(global_mode.iloc[0])
        else:
            df[col] = df[col].fillna(df[col].median())

    # Cast to int where possible
    df["year"] = pd.to_numeric(df["year"], errors="coerce").round().astype('Int64')
    df["week"] = pd.to_numeric(df["week"], errors="coerce").round().astype('Int64')
    return df


def fill_numeric_groupwise(df: pd.DataFrame, cols):
    # Prefer state-level patterns, then global fallback
    for col in cols:
        if col not in df.columns:
            continue
        # Coerce to numeric
        df[col] = pd.to_numeric(df[col], errors="coerce")
        if "state" in df.columns:
            state_med = df.groupby("state")[col].transform("median")
            df[col] = df[col].fillna(state_med)
        # Global median fallback
        df[col] = df[col].fillna(df[col].median())
        # Final fallback
        df[col] = df[col].fillna(0)
    return df


def recompute_derived(df: pd.DataFrame) -> pd.DataFrame:
    # cases_per_100k
    if {"cases", "population"}.issubset(df.columns):
        pop_safe = df["population"].replace(0, np.nan)
        df["cases_per_100k"] = (df["cases"] / pop_safe) * 100_000
        df["cases_per_100k"] = df["cases_per_100k"].fillna(0)

    # week_sin/week_cos
    if "week" in df.columns:
        week_num = pd.to_numeric(df["week"], errors="coerce").fillna(0)
        df["week_sin"] = np.sin(2 * np.pi * week_num / 52)
        df["week_cos"] = np.cos(2 * np.pi * week_num / 52)

    # temp_anomaly: deviation from state mean temperature
    if {"temperature_2m_mean", "state"}.issubset(df.columns):
        state_mean_temp = df.groupby("state")["temperature_2m_mean"].transform("mean")
        df["temp_anomaly"] = df["temperature_2m_mean"] - state_mean_temp

    # rainfall_change: week-to-week precipitation change per state
    if {"precipitation_sum", "state", "year", "week"}.issubset(df.columns):
        df = df.sort_values(["state", "year", "week"])  # ensure order
        df["rainfall_change"] = df.groupby("state")["precipitation_sum"].diff()
        df["rainfall_change"] = df["rainfall_change"].fillna(0)

    # cases_last_week/deaths_last_week: fill remaining NaNs with 0
    for col in ["cases_last_week", "deaths_last_week"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def main():
    ensure_dirs()
    df = load_df()
    save_missing(df, REPORTS_DIR / "missing_values_before.csv")

    # Remove empty rows/columns first
    df = drop_empty(df)

    # Fill year/week from date and groupwise
    df = fill_year_week(df)

    # Fill numeric features groupwise
    numeric_cols = [
        "temperature_2m_mean",
        "precipitation_sum",
        "relative_humidity_2m_mean",
        "who_country_cases",
        "population",
        "urban_percent",
        "cases",
        "deaths",
        "cfr",
    ]
    df = fill_numeric_groupwise(df, numeric_cols)

    # Recompute derived fields deterministically
    df = recompute_derived(df)

    # Save outputs
    out_path = OUTPUT_DIR / "outbreakiq_training_data_filled.csv"
    df.to_csv(out_path, index=False)
    save_missing(df, REPORTS_DIR / "missing_values_after.csv")

    # Summary
    before = pd.read_csv(REPORTS_DIR / "missing_values_before.csv")
    after = pd.read_csv(REPORTS_DIR / "missing_values_after.csv")
    summary_lines = [
        f"Saved cleaned dataset → {out_path}",
        "\nTop missing (before):",
        before.sort_values("missing_count", ascending=False).head(15).to_string(index=False),
        "\nTop missing (after):",
        after.sort_values("missing_count", ascending=False).head(15).to_string(index=False),
    ]
    (REPORTS_DIR / "fill_missing_summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")
    print(summary_lines[0])
    print("Missing summary saved → reports/fill_missing_summary.txt")


if __name__ == "__main__":
    main()