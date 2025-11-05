import requests
import pandas as pd
from pathlib import Path
import time
from utils.who_codes import WHO_INDICATORS

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def get_cleaned_diseases(clean_path=DATA_DIR / "ncdc_outbreaks_clean.csv"):
    try:
        df = pd.read_csv(clean_path)
        diseases = sorted(pd.Series(df.get("disease", [])).dropna().unique())
        return diseases
    except Exception:
        return []

def fetch_who_indicator(disease, indicator, country="NGA"):
    url = f"https://ghoapi.azureedge.net/api/{indicator}?$filter=SpatialDim eq '{country}'"
    print(f"⏳ Fetching {disease} ({indicator}) from WHO...")
    r = requests.get(url, timeout=30)
    if r.status_code == 404:
        print(f"⚠️ {disease}: 404 Not Found (indicator may not exist)")
        return pd.DataFrame()
    r.raise_for_status()
    data = r.json().get("value", [])
    if not data:
        print(f"⚠️ {disease}: No data found in WHO GHO API")
        return pd.DataFrame()
    df = pd.DataFrame(data)
    needed = ["IndicatorCode", "TimeDim", "Value", "SpatialDim"]
    df = df[[c for c in needed if c in df.columns]]
    df.rename(columns={
        "IndicatorCode": "indicator",
        "TimeDim": "year",
        "Value": "cases",
        "SpatialDim": "country",
    }, inplace=True)
    df["disease"] = disease
    # Coerce year/cases
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["cases"] = pd.to_numeric(df["cases"], errors="coerce")
    return df

def find_indicator_code(disease_keyword: str) -> str | None:
    try:
        url = f"https://ghoapi.azureedge.net/api/Indicator?$filter=contains(IndicatorName,'{disease_keyword}')"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json().get("value", [])
        if not data:
            return None
        # Prefer indicators that mention cases or reported
        # Fallback to first result
        def score(item):
            name = (item.get("IndicatorName") or "").lower()
            s = 0
            if "case" in name:
                s += 2
            if "reported" in name:
                s += 1
            if disease_keyword.lower() in name:
                s += 1
            return s
        best = sorted(data, key=score, reverse=True)[0]
        return best.get("IndicatorCode")
    except Exception:
        return None

def main():
    cleaned_diseases = set(get_cleaned_diseases())
    # Use only indicators present in cleaned list; default to all if none detected
    selected = {d: i for d, i in WHO_INDICATORS.items() if not cleaned_diseases or d in cleaned_diseases}
    if not selected:
        print("⚠️ No matching diseases found; using full WHO indicator set.")
        selected = WHO_INDICATORS

    frames = []
    for disease, indicator in selected.items():
        try:
            df = fetch_who_indicator(disease, indicator)
            if df.empty:
                # Attempt dynamic discovery if the static indicator fails
                guess_code = find_indicator_code(disease)
                if guess_code:
                    alt_df = fetch_who_indicator(disease, guess_code)
                    if not alt_df.empty:
                        frames.append(alt_df)
                        time.sleep(1)
                        continue
            else:
                frames.append(df)
            time.sleep(1)
        except Exception as e:
            print(f"❌ Error fetching {disease}: {e}")

    if frames:
        all_df = pd.concat(frames, ignore_index=True)
        out_path = DATA_DIR / "who_disease_data.csv"
        all_df.to_csv(out_path, index=False)
        print(f"\n✅ Saved WHO data → {out_path} ({len(all_df)} rows)")
    else:
        print("\n⚠️ No data was fetched. Check indicator mappings or API availability.")

if __name__ == "__main__":
    main()