import requests
import pandas as pd
from pathlib import Path

Path("data").mkdir(exist_ok=True)

def fetch_worldbank_indicator(indicator, country='NG', per_page=1000):
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json&per_page={per_page}"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    df = pd.json_normalize(data[1])
    df = df[['country.value', 'date', 'value']]
    df.columns = ['country', 'year', indicator]
    df['year'] = df['year'].astype(int)
    return df

# Indicators to fetch
indicators = {
    "SP.POP.TOTL": "total_population",
    "SP.URB.TOTL.IN.ZS": "urban_percent"
}

frames = []
for code, name in indicators.items():
    df = fetch_worldbank_indicator(code)
    df.rename(columns={code: name}, inplace=True)
    frames.append(df)

# Merge both
merged = frames[0].merge(frames[1], on=["country","year"], how="outer")
merged.to_csv("data/worldbank_population.csv", index=False)
print(f"✅ Saved World Bank data → data/worldbank_population.csv ({len(merged)} rows)")