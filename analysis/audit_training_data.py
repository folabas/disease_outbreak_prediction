import sys
from pathlib import Path

import pandas as pd

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from ml.config import DATA_PATH


def main():
    df = pd.read_csv(DATA_PATH)
    core_cols = ["disease", "state", "year", "week", "cases"]
    missing_cols = [c for c in core_cols if c not in df.columns]
    if missing_cols:
        print({"error": f"missing_columns: {missing_cols}"})
        return

    # Basic cleanliness
    df = df.dropna(subset=core_cols)
    df["week"] = pd.to_numeric(df["week"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["cases"] = pd.to_numeric(df["cases"], errors="coerce")
    df = df.dropna(subset=["week", "year", "cases"]) 

    diseases = sorted(df["disease"].unique().tolist())
    report = []
    for d in diseases:
        ddf = df[df["disease"] == d].copy()
        report.append({
            "disease": d,
            "rows": int(len(ddf)),
            "unique_states": int(ddf["state"].nunique()),
            "years": f"{int(ddf['year'].min())}-{int(ddf['year'].max())}",
            "weeks": f"{int(ddf['week'].min())}-{int(ddf['week'].max())}",
        })

    for r in report:
        print(r)


if __name__ == "__main__":
    main()