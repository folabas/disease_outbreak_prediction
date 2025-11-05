import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data")

# ---------------------------------------------------
# 1️⃣ LOAD ALL DATASETS
# ---------------------------------------------------
print("📥 Loading datasets...")

ncdc = pd.read_csv(DATA_DIR / "ncdc_outbreaks_clean.csv")
who = pd.read_csv(DATA_DIR / "who_disease_data.csv")
pop = pd.read_csv(DATA_DIR / "worldbank_population.csv")
weather = pd.read_csv(DATA_DIR / "weather_historical.csv")

print("✅ Files loaded:")
print(f"NCDC: {ncdc.shape}, WHO: {who.shape}, POP: {pop.shape}, WEATHER: {weather.shape}")

# ---------------------------------------------------
# 2️⃣ PREPROCESS NCDC DATA
# ---------------------------------------------------
print("🧹 Cleaning NCDC data...")
ncdc["report_date"] = pd.to_datetime(ncdc["report_date"], errors="coerce")
ncdc["year"] = ncdc["report_date"].dt.year
ncdc["week"] = ncdc["report_date"].dt.isocalendar().week
ncdc["state"] = ncdc["state"].str.strip().str.title()
ncdc["disease"] = ncdc["disease"].str.strip().str.title()

# Drop any rows with missing state/disease
ncdc = ncdc.dropna(subset=["state", "disease"])
print("✅ NCDC processed:", ncdc.shape)

# ---------------------------------------------------
# 3️⃣ PREPROCESS WEATHER DATA
# ---------------------------------------------------
print("🌦 Aggregating weather data...")

weather["time"] = pd.to_datetime(weather["time"], errors="coerce")
weather["year"] = weather["time"].dt.year
weather["week"] = weather["time"].dt.isocalendar().week

# If weather data is national, replicate for all states
states = ncdc["state"].unique()
weather_weekly = (
    weather.groupby(["year", "week"])
    .agg({
        "temperature_2m_mean": "mean",
        "precipitation_sum": "sum",
        "relative_humidity_2m_mean": "mean"
    })
    .reset_index()
)

# Expand national weather to all states (so merge works by state too)
weather_weekly["key"] = 1
states_df = pd.DataFrame({"state": states})
states_df["key"] = 1
weather_weekly = weather_weekly.merge(states_df, on="key", how="left").drop(columns="key")

print("✅ Weather weekly shape:", weather_weekly.shape)

# ---------------------------------------------------
# 4️⃣ PREPROCESS WHO DATA
# ---------------------------------------------------
print("🌍 Preparing WHO disease data...")
who.rename(columns={"cases": "who_country_cases"}, inplace=True)
who["year"] = pd.to_numeric(who["year"], errors="coerce")
who["disease"] = who["disease"].str.title()

# Keep only Nigeria data if more countries exist
if "country" in who.columns:
    who = who[who["country"].str.contains("NGA|Nigeria", case=False, na=False)]

print("✅ WHO processed:", who.shape)

# ---------------------------------------------------
# 5️⃣ PREPROCESS WORLD BANK DATA
# ---------------------------------------------------
print("👥 Preparing population data...")
pop.rename(columns={
    "total_population": "population",
    "urban_percent": "urban_percent"
}, inplace=True)

# Broadcast yearly population to all states
pop["key"] = 1
states_df = pd.DataFrame({"state": states, "key": 1})
pop = pop.merge(states_df, on="key", how="left").drop(columns="key")

print("✅ Population expanded:", pop.shape)

# ---------------------------------------------------
# 6️⃣ MERGE ALL DATASETS
# ---------------------------------------------------
print("🔗 Merging all data...")

merged = (
    ncdc
    .merge(weather_weekly, on=["state", "year", "week"], how="left")
    .merge(who[["disease", "year", "who_country_cases"]], on=["disease", "year"], how="left")
    .merge(pop[["state", "year", "population", "urban_percent"]], on=["state", "year"], how="left")
)

print("✅ Merged shape:", merged.shape)

# ---------------------------------------------------
# 7️⃣ FEATURE ENGINEERING
# ---------------------------------------------------
print("🧮 Creating derived features...")

merged = merged.sort_values(["state", "disease", "year", "week"])

# Lag features
merged["cases_last_week"] = merged.groupby(["state", "disease"])["cases"].shift(1)
merged["deaths_last_week"] = merged.groupby(["state", "disease"])["deaths"].shift(1)

# Normalization
merged["cases_per_100k"] = (merged["cases"] / merged["population"]) * 100_000

# Change features
merged["rainfall_change"] = merged.groupby("state")["precipitation_sum"].diff()
merged["temp_anomaly"] = (
    merged["temperature_2m_mean"] -
    merged.groupby("state")["temperature_2m_mean"].transform("mean")
)

# Seasonality encoding
merged["week_sin"] = np.sin(2 * np.pi * merged["week"] / 52)
merged["week_cos"] = np.cos(2 * np.pi * merged["week"] / 52)

print("✅ Engineered features added")

# ---------------------------------------------------
# 8️⃣ SAVE FINAL DATASET
# ---------------------------------------------------
output_path = DATA_DIR / "outbreakiq_training_data.csv"
merged.to_csv(output_path, index=False)
print(f"🎯 Final dataset saved → {output_path}")
print("Columns:", merged.columns.tolist())
print("Rows:", len(merged))