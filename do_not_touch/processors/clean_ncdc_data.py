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

# Remove implausible COVID-19 rows (e.g., deaths exceed cases or deaths with zero cases)
covid_mask = df["disease"].astype(str).str.contains("covid", case=False, na=False)
before_count = covid_mask.sum()
# Drop cases where deaths >= cases (only for cases > 0), and where cases <= 0 with deaths > 0
implausible = covid_mask & (
    ((df["deaths"] >= df["cases"]) & (df["cases"] > 0)) |
    ((df["cases"] <= 0) & (df["deaths"] > 0))
)
removed_count = int(implausible.sum())
if removed_count:
    df = df.loc[~implausible]
    print(
        f"⚠️ Removed {removed_count} implausible COVID-19 rows (deaths ≥ cases with cases>0, or deaths with 0 cases)."
    )
    print(
        f"   COVID rows before: {int(before_count)}, after: {int(df['disease'].str.contains('COVID', case=False, na=False).sum())}"
    )

# Save clean file
df.to_csv("data/ncdc_outbreaks_clean.csv", index=False)
print(f"✅ Cleaned data saved → data/ncdc_outbreaks_clean.csv ({len(df)} rows)")

print("🦠 Diseases found:", df['disease'].unique())