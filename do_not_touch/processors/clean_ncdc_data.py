import pandas as pd
import re

df = pd.read_csv("ncdc_outbreaks.csv")

# Ensure disease/state present; fill missing instead of dropping
df["disease"] = df["disease"].fillna("Unknown")
df["state"] = df["state"].fillna("Unknown")

# For non-alphabetic "state" values, replace with 'Unknown' instead of dropping
state_clean = df["state"].astype(str)
mask_valid_state = state_clean.str.match(r"^[A-Za-z\s\-\(\)]+$", na=False)
df["state"] = state_clean.where(mask_valid_state, "Unknown")

# Standardize disease names
df["disease"] = df["disease"].str.strip().str.title().replace({
    "Covid-19": "COVID-19",
    "Cholera2": "Cholera",
    "Measles.": "Measles"
})

# Clean whitespace/newlines
df["state"] = df["state"].str.replace(r"[\n\r\t]+", " ", regex=True).str.strip()
df["week"] = df["week"].astype(str).str.extract(r"(\d{1,2})")

# Convert numbers safely
for col in ["cases", "deaths", "cfr"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

## Keep rows even if cases are missing; we filled missing numeric values with 0

# Save clean file
df.to_csv("data/ncdc_outbreaks_clean.csv", index=False)
print(f"✅ Cleaned data saved → data/ncdc_outbreaks_clean.csv ({len(df)} rows)")

print("🦠 Diseases found:", df['disease'].unique())