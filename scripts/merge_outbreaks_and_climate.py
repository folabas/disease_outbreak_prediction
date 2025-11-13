import pandas as pd
from pathlib import Path
import re

# === PATHS ===
BASE_DIR = Path("data")
NCDC_PATH = BASE_DIR / "ncdc_outbreaks_clean.csv"
CLIMATE_DIR = BASE_DIR  # default climate directory
CLIMATE_LIVE_DIR = BASE_DIR / "live"  # optional live directory
OUTPUT_PATH = BASE_DIR / "evaluation_merged_clean.csv"

# === HELPER: Extract state name from climate filenames ===
def extract_state_name(filename: str) -> str:
    """
    Extracts the state name from a filename like:
    weather_weekly_Abia.csv → "Abia"
    """
    match = re.search(r"weather_weekly_(.+?)\.csv", filename)
    if match:
        return match.group(1).replace("_", " ")
    return None


# === STEP 1: Load climate datasets ===
def load_all_climate():
    climate_frames = []
    climate_dirs = [CLIMATE_DIR]
    if CLIMATE_LIVE_DIR.exists():
        climate_dirs.append(CLIMATE_LIVE_DIR)

    files = []
    for d in climate_dirs:
        files.extend(list(d.glob("weather_weekly_*.csv")))

    for file in files:
        state = extract_state_name(file.name)
        if not state:
            continue
        
        df = pd.read_csv(file)

        # Normalize column names
        df.columns = [c.lower().strip() for c in df.columns]

        # Ensure required columns exist
        required = ["year", "week"]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing column '{col}' in {file}")

        df["state"] = state

        climate_frames.append(df)

    if not climate_frames:
        raise RuntimeError("No climate files found!")

    climate_df = pd.concat(climate_frames, ignore_index=True)

    # Climate relevant columns
    climate_df = climate_df[
        ["state", "year", "week", "temperature_2m_mean", "relative_humidity_2m_mean", "precipitation_sum"]
    ]

    return climate_df


# === STEP 2: Load NCDC outbreak dataset ===
def load_ncdc_outbreaks():
    df = pd.read_csv(NCDC_PATH)

    df.columns = [c.lower().strip() for c in df.columns]

    required = ["state", "disease", "year", "week", "cases"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"NCDC dataset missing required column: {col}")

    return df


# === STEP 3: Merge datasets ===
def merge_datasets(ncdc_df, climate_df):
    # Ensure year/week are ints
    ncdc_df["year"] = ncdc_df["year"].astype(int)
    ncdc_df["week"] = ncdc_df["week"].astype(int)
    climate_df["year"] = climate_df["year"].astype(int)
    climate_df["week"] = climate_df["week"].astype(int)

    merged = pd.merge(
        ncdc_df,
        climate_df,
        on=["state", "year", "week"],
        how="left",
    )

    return merged


# === STEP 4: Fill missing climate values per state ===
def fill_missing(merged):
    climate_cols = [
        "temperature_2m_mean",
        "relative_humidity_2m_mean",
        "precipitation_sum",
    ]

    # Group by state for local climate continuity
    def fill_group(g):
        g[climate_cols] = g[climate_cols].ffill().bfill()  # forward/backward fill
        g[climate_cols] = g[climate_cols].fillna(g[climate_cols].median())  # fallback
        return g

    merged = merged.groupby("state", group_keys=False).apply(fill_group)

    return merged


# === MAIN ===
def main():
    print("Loading NCDC outbreak data...")
    ncdc_df = load_ncdc_outbreaks()

    print("Loading all climate data...")
    climate_df = load_all_climate()

    print("Merging datasets...")
    merged = merge_datasets(ncdc_df, climate_df)

    print("Cleaning missing values...")
    cleaned = fill_missing(merged)

    print(f"Saving output → {OUTPUT_PATH}")
    cleaned.to_csv(OUTPUT_PATH, index=False)

    print("\nDONE! Your merged evaluation dataset is ready:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()