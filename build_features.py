from pathlib import Path
from typing import List

import pandas as pd


def load_csv(path: Path, required_cols: List[str] = None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    df = pd.read_csv(path)
    if required_cols:
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"{path.name} missing columns: {missing}")
    return df


def main():
    root = Path(__file__).parent
    data_dir = root / "data"
    raw_dir = data_dir / "raw"
    live_dir = data_dir / "live"

    # Inputs
    ncdc_path = data_dir / "ncdc_outbreaks_clean.csv"
    weather_path = live_dir / "weather_weekly_by_state.csv"
    who_weekly_path = raw_dir / "who_disease_data_weekly.csv"
    who_map_path = raw_dir / "who_indicator_mapping.csv"
    wb_pop_weekly_path = raw_dir / "worldbank_population_weekly.csv"
    wb_urban_path = raw_dir / "worldbank_urban_percent.csv"

    # Output
    out_path = data_dir / "outbreakiq_training_data_filled.csv"

    # Load core datasets
    ncdc = load_csv(ncdc_path, required_cols=["state", "disease", "year", "week", "cases", "deaths"])\
        .copy()

    # Ensure types
    for c in ["year", "week"]:
        ncdc[c] = pd.to_numeric(ncdc[c], errors="coerce")
    for c in ["cases", "deaths"]:
        ncdc[c] = pd.to_numeric(ncdc[c], errors="coerce").fillna(0)
    ncdc = ncdc.dropna(subset=["state", "disease", "year", "week"])

    weather = load_csv(weather_path).copy()
    # Try to align weather columns: expect at least state/year/week
    # If date column exists, derive year/week
    if "date" in weather.columns and ("year" not in weather.columns or "week" not in weather.columns):
        dt = pd.to_datetime(weather["date"], errors="coerce")
        weather["year"] = dt.dt.isocalendar().year
        weather["week"] = dt.dt.isocalendar().week
    # Keep only needed keys and numeric features
    key_cols = [c for c in ["state", "year", "week"] if c in weather.columns]
    if len(key_cols) < 3:
        raise ValueError("Weather file must contain 'state', 'year', and 'week' columns")
    feature_cols = [c for c in weather.columns if c not in key_cols and pd.api.types.is_numeric_dtype(weather[c])]
    weather = weather[key_cols + feature_cols]

    who_weekly = load_csv(who_weekly_path, required_cols=["disease_label", "indicator_code", "year", "week", "cases"]).copy()
    who_map = load_csv(who_map_path, required_cols=["disease_label", "indicator_code", "canonical_disease"]).copy()
    # Join to mapping and aggregate by canonical_disease/week
    who_join = who_weekly.merge(who_map, on=["disease_label", "indicator_code"], how="left")
    who_join["canonical_disease"] = who_join["canonical_disease"].fillna("")
    who_join = who_join[who_join["canonical_disease"] != ""]
    who_join["cases"] = pd.to_numeric(who_join["cases"], errors="coerce").fillna(0)
    who_agg = (
        who_join.groupby(["canonical_disease", "year", "week"], as_index=False)["cases"].sum()
        .rename(columns={"canonical_disease": "disease", "cases": "who_cases_national"})
    )

    wb_pop_w = load_csv(wb_pop_weekly_path, required_cols=["year", "week", "population"]).copy()
    wb_pop_w["population"] = pd.to_numeric(wb_pop_w["population"], errors="coerce")

    # Optional urban percent (annual), align by year
    wb_urban = None
    if wb_urban_path.exists():
        wb_urban = load_csv(wb_urban_path)
        # Try to locate year and value columns
        year_col = "year" if "year" in wb_urban.columns else None
        if not year_col:
            # best-effort: pick first int-like column name or 'Year'
            for c in wb_urban.columns:
                if c.lower() == "year":
                    year_col = c
                    break
        value_cols = [c for c in wb_urban.columns if c != year_col and pd.api.types.is_numeric_dtype(wb_urban[c])]
        if year_col and value_cols:
            wb_urban = wb_urban[[year_col, value_cols[0]]].rename(columns={year_col: "year", value_cols[0]: "urban_percent"})
        else:
            wb_urban = None

    # Build training table: start from NCDC labels and enrich with features
    base = ncdc.copy()
    # Merge weather by state/year/week
    feat = base.merge(weather, on=["state", "year", "week"], how="left")
    # Merge WHO national weekly by disease/week
    feat = feat.merge(who_agg, on=["disease", "year", "week"], how="left")
    # Merge population weekly
    feat = feat.merge(wb_pop_w, on=["year", "week"], how="left")
    # Merge urban percent by year (optional)
    if wb_urban is not None:
        feat = feat.merge(wb_urban, on=["year"], how="left")

    # Feature enrichment: lags, rolling stats, normalization
    # Ensure sort order for stable group operations
    feat = feat.sort_values(["disease", "state", "year", "week"]).reset_index(drop=True)
    grp = feat.groupby(["disease", "state"], sort=False)

    # Lags and rolling stats for cases/deaths
    feat["cases_last_week"] = grp["cases"].shift(1)
    feat["cases_2w_avg"] = (grp["cases"].shift(1) + grp["cases"].shift(2)) / 2.0
    feat["deaths_last_week"] = grp["deaths"].shift(1)
    # Rolling windows use min_periods=1 to avoid excessive NaNs at series start
    feat["cases_mean_4w"] = grp["cases"].rolling(window=4, min_periods=1).mean().reset_index(level=[0, 1], drop=True)
    feat["cases_std_4w"] = grp["cases"].rolling(window=4, min_periods=1).std().reset_index(level=[0, 1], drop=True)
    feat["deaths_mean_4w"] = grp["deaths"].rolling(window=4, min_periods=1).mean().reset_index(level=[0, 1], drop=True)

    # Growth rate relative to last week (safe division)
    lag1 = feat["cases_last_week"].copy()
    feat["cases_growth_rate"] = ((feat["cases"] - lag1) / lag1.where(lag1 > 0)).fillna(0.0)

    # Per-100k normalization using population
    pop = feat["population"].replace(0, pd.NA)
    feat["cases_per_100k"] = ((feat["cases"] * 100000) / pop).fillna(0.0)

    # Fill missing feature values with reasonable defaults
    numeric_cols = [c for c in feat.columns if pd.api.types.is_numeric_dtype(feat[c])]
    feat[numeric_cols] = feat[numeric_cols].fillna(0)

    # Save
    out_path.parent.mkdir(parents=True, exist_ok=True)
    feat.to_csv(out_path, index=False)

    # Simple summary
    print(f"[SAVED] {out_path} rows={len(feat)} cols={len(feat.columns)}")
    by_disease = feat.groupby("disease")["cases"].sum().sort_values(ascending=False)
    print("[SUMMARY] Total NCDC cases by disease (top 10):")
    print(by_disease.head(10))


if __name__ == "__main__":
    main()