import requests
import pandas as pd
from pathlib import Path

Path("data").mkdir(exist_ok=True)

def fetch_openmeteo_historical(lat, lon, start, end):
    url = "https://archive-api.open-meteo.com/v1/era5"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": "temperature_2m_mean,precipitation_sum,relative_humidity_2m_mean",
        "timezone": "Africa/Lagos"
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()["daily"]
    df = pd.DataFrame(data)
    df.to_csv("data/weather_historical.csv", index=False)
    print(f"✅ Saved weather data → data/weather_historical.csv ({len(df)} rows)")

# Example: Lagos coordinates
if __name__ == "__main__":
    fetch_openmeteo_historical(6.5244, 3.3792, "2015-01-01", "2024-12-31")