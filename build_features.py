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

    # Inputs - Use existing merged datasets (all features already included)
    # Try to find outbreak data - use outbreak_dataset.csv if available, otherwise try merged datasets
    ncdc_path = data_dir / "outbreak_dataset.csv"
    if not ncdc_path.exists():
        ncdc_path = data_dir / "final_merged_datasets.csv"

    # Output
    out_path = data_dir / "outbreak_dataset.csv"

    # Load core dataset - already contains all merged features
    if not ncdc_path.exists():
        log(f"[WARNING] {ncdc_path} not found, trying fallback datasets...")
        # Try fallback datasets
        for fallback in [data_dir / "final_merged_datasets.csv"]:
            if fallback.exists():
                ncdc_path = fallback
                log(f"[INFO] Using fallback dataset: {fallback}")
                break
        else:
            raise FileNotFoundError(f"No outbreak dataset found. Expected one of: outbreak_dataset.csv or final_merged_datasets.csv in {data_dir}")
    
    # Load the merged dataset (already contains all features: climate, WHO, population, WASH, etc.)
    feat = load_csv(ncdc_path, required_cols=["state", "disease", "year", "week", "cases", "deaths"]).copy()

    # Ensure types
    for c in ["year", "week"]:
        feat[c] = pd.to_numeric(feat[c], errors="coerce")
    for c in ["cases", "deaths"]:
        feat[c] = pd.to_numeric(feat[c], errors="coerce").fillna(0)
    feat = feat.dropna(subset=["state", "disease", "year", "week"])

    # Note: The merged dataset already contains:
    # - Climate features (temperature_2m_mean, relative_humidity_2m_mean, precipitation_sum)
    # - WHO cases (who_cases_national) if present
    # - Population features (population, population_density, urban_percent, growth_rate_percent)
    # - WASH features (access_to_clean_water_percent, etc.)
    # So we don't need to merge external files anymore

    # Feature enrichment: lags, rolling stats, normalization
    # Ensure sort order for stable group operations
    feat = feat.sort_values(["disease", "state", "year", "week"]).reset_index(drop=True)
    grp = feat.groupby(["disease", "state"], sort=False)

    # Enhanced Feature Engineering: Lags, Rolling Stats, Date Features
    
    # === Lag Features (legacy set) ===
    if "cases_last_week" not in feat.columns:
        feat["cases_last_week"] = grp["cases"].shift(1)
    if "cases_2w_avg" not in feat.columns:
        feat["cases_2w_avg"] = (grp["cases"].shift(1) + grp["cases"].shift(2)) / 2.0

    if "deaths_last_week" not in feat.columns:
        feat["deaths_last_week"] = grp["deaths"].shift(1)

    # === Rolling Statistics (legacy set) ===
    if "cases_mean_4w" not in feat.columns:
        feat["cases_mean_4w"] = grp["cases"].rolling(window=4, min_periods=1).mean().reset_index(level=[0, 1], drop=True)
    if "cases_std_4w" not in feat.columns:
        feat["cases_std_4w"] = grp["cases"].rolling(window=4, min_periods=1).std().reset_index(level=[0, 1], drop=True)
    if "deaths_mean_4w" not in feat.columns:
        feat["deaths_mean_4w"] = grp["deaths"].rolling(window=4, min_periods=1).mean().reset_index(level=[0, 1], drop=True)

    # === Growth and Rate Features ===
    if "cases_growth_rate" not in feat.columns:
        lag1 = feat["cases_last_week"].copy() if "cases_last_week" in feat.columns else grp["cases"].shift(1)
        feat["cases_growth_rate"] = ((feat["cases"] - lag1) / lag1.where(lag1 > 0)).fillna(0.0)

    # === Normalization Features ===
    if "cases_per_100k" not in feat.columns and "population" in feat.columns:
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