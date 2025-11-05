import requests
import pandas as pd

def find_malaria_indicators():
    url = "https://ghoapi.azureedge.net/api/Indicator"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    data = r.json().get("value", [])
    malaria = [i for i in data if "malaria" in (i.get("IndicatorName") or "").lower()]
    print(f"Found {len(malaria)} malaria indicators\n")
    df = pd.DataFrame(malaria)
    return df[["IndicatorCode", "IndicatorName"]]

def test_indicator(code):
    url = f"https://ghoapi.azureedge.net/api/{code}?$filter=SpatialDim eq 'NGA'"
    r = requests.get(url, timeout=30)
    if r.status_code == 404:
        return (code, "404 Not Found")
    try:
        data = r.json().get("value", [])
    except Exception:
        data = []
    return (code, "✅ Has data" if data else "⚠️ Empty")

if __name__ == "__main__":
    df = find_malaria_indicators()
    print(df.head(20))
    # Prioritize indicators mentioning cases or reported
    top = df.copy()
    top["score"] = top["IndicatorName"].str.lower().apply(lambda s: ("case" in s) * 2 + ("reported" in s))
    top = top.sort_values(by=["score"], ascending=False)
    codes_to_test = list(top["IndicatorCode"].head(40))
    results = [test_indicator(c) for c in codes_to_test]
    print(pd.DataFrame(results, columns=["Indicator", "Status"]))