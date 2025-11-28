import sys
import os
from pathlib import Path
import pandas as pd

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from app.models.climate import ClimateQuery
from app.services.ml import get_climate

def test_fallback():
    print("Testing get_climate fallback logic...")
    
    # Query for a future date range (e.g., Nov 2025)
    # Assuming current date is Nov 2025, "Last 30 Days" would be roughly 2025-W43 to 2025-W47
    q = ClimateQuery(
        region="All",  # Changed to All to match user issue
        disease="cholera",
        startDate="2025-W43",
        endDate="2025-W47"
    )
    
    response = get_climate(q)
    
    print(f"Region: {response.region}")
    print(f"Data Points: {len(response.temperature)}")
    print(f"Summary: {response.summary}")
    
    if len(response.temperature) > 0:
        print("First Point Date:", response.temperature[0].date)
        print("Last Point Date:", response.temperature[-1].date)
        print("First Point Value:", response.temperature[0].value)
        
        # Verify dates are in 2025
        if "2025" in response.temperature[0].date:
            print("SUCCESS: Dates shifted to 2025 correctly.")
        else:
            print("FAILURE: Dates not shifted correctly.")
    else:
        print("FAILURE: No data returned.")
        # Debug: check what's in the file for 2023
        try:
            df = pd.read_csv("data/climate/climate_weekly.csv")
            print("\nDebug: 2023 Data Check")
            df_2023 = df[df["year"] == 2023]
            print(f"Total 2023 rows: {len(df_2023)}")
            print(f"Weeks available: {sorted(df_2023['week'].unique())}")
        except Exception as e:
            print(f"Debug Error: {e}")

if __name__ == "__main__":
    test_fallback()
