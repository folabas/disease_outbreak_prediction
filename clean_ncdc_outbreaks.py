import pandas as pd
import numpy as np
from pathlib import Path

# Input and output paths
RAW_PRIMARY = Path("data") / "ncdc_outbreaks.csv"
RAW_FALLBACK = Path("data") / "ncdc_outbreaks_clean.csv"  # fallback if raw not found
OUT = Path("data") / "ncdc_outbreaks_clean.csv"

# Known invalid state entries to drop
DROP_STATES = {"Unknown", "National", "Total", "None", "All", "N/A", "Na"}

# State synonym normalization (e.g., FCT → Abuja)
STATE_SYNONYMS = {
    "Fct": "Abuja",
    "Federal Capital Territory": "Abuja",
    "F.C.T": "Abuja",
}

# Whitelist of valid Nigerian states (FCT standardized to Abuja)
VALID_STATES = {
    "Abia",
    "Adamawa",
    "Akwa Ibom",
    "Anambra",
    "Bauchi",
    "Bayelsa",
    "Benue",
    "Borno",
    "Cross River",
    "Delta",
    "Ebonyi",
    "Edo",
    "Ekiti",
    "Enugu",
    "Abuja",
    "Gombe",
    "Imo",
    "Jigawa",
    "Kaduna",
    "Kano",
    "Katsina",
    "Kebbi",
    "Kogi",
    "Kwara",
    "Lagos",
    "Nasarawa",
    "Niger",
    "Ogun",
    "Ondo",
    "Osun",
    "Oyo",
    "Plateau",
    "Rivers",
    "Sokoto",
    "Taraba",
    "Yobe",
    "Zamfara",
}

# Disease normalization mapping
DISEASE_MAP = {
    "Covid19": "Covid-19",
    "Covid-19-19": "Covid-19",
    "Coronavirus": "Covid-19",
    "Covid": "Covid-19",
    "Lassa": "Lassa Fever",
    "Lassafever": "Lassa Fever",
    "Monkeypox": "Mpox",
    "Mpox": "Mpox",
    "Yf": "Yellow Fever",
    "Y.F.": "Yellow Fever",
    "Cholerae": "Cholera",
}

def load_source() -> pd.DataFrame:
    src = None
    if RAW_PRIMARY.exists():
        src = RAW_PRIMARY
    elif RAW_FALLBACK.exists():
        src = RAW_FALLBACK
    else:
        raise FileNotFoundError("No NCDC source file found at data/ncdc_outbreaks.csv or data/ncdc_outbreaks_clean.csv")
    print(f"Loading {src} ...")
    # Robust read with BOM handling and bad-line skipping
    try:
        df = pd.read_csv(src, encoding="utf-8-sig", on_bad_lines="skip")
    except Exception:
        df = pd.read_csv(src, encoding="utf-8", on_bad_lines="skip")
    print("Initial shape:", df.shape)
    # Fix weird encoding artifacts (e.g., bullets, smart quotes)
    for col in df.columns:
        df[col] = (
            df[col].astype(str)
            .str.encode("latin1", errors="ignore")
            .str.decode("utf-8", errors="ignore")
        )
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df

def guess_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    possible_cols = df.columns.tolist()
    print("Columns:", possible_cols)
    rename_map = {}
    for c in possible_cols:
        lc = c.lower()
        if "state" in lc and "_code" not in lc:
            rename_map[c] = "state"
        if any(k in lc for k in ["disease", "condition", "illness"]):
            rename_map[c] = "disease"
        if "case" in lc:
            rename_map[c] = "cases"
        if "death" in lc:
            rename_map[c] = "deaths"
        if "week" in lc:
            rename_map[c] = "week"
        if "year" in lc:
            rename_map[c] = "year"
        if "date" in lc:
            rename_map[c] = "date"
    df = df.rename(columns=rename_map)
    return df

def normalize_text(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["state", "disease"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.replace(r"\s+", " ", regex=True).str.title()
    # Apply state synonyms
    if "state" in df.columns:
        df["state"] = df["state"].replace(STATE_SYNONYMS)
        df = df[~df["state"].isin(DROP_STATES)]
        # Keep only valid Nigerian states
        df = df[df["state"].isin(VALID_STATES)]
    return df

def derive_year_week(df: pd.DataFrame) -> pd.DataFrame:
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        iso = df["date"].dt.isocalendar()
        df["year"] = iso.year
        df["week"] = iso.week
    return df

def ensure_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["cases", "deaths"]:
        if col in df.columns:
            # Coerce numeric values (including floats like '1.0'), drop non-numeric
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df[~df[col].isna()]
            # Store as integers (weekly counts should be integers)
            df[col] = df[col].astype(int)
        else:
            df[col] = 0
    # Convert year/week to numeric where present
    for col in ["year", "week"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df[~df[col].isna()]
    return df

def normalize_disease(df: pd.DataFrame) -> pd.DataFrame:
    if "disease" in df.columns:
        df["disease"] = df["disease"].astype(str).str.strip()
        # Fix duplicated suffixes like Covid-19-19 before mapping
        df["disease"] = df["disease"].str.replace(r"(?i)covid[-\s]?19[-\s]?19", "Covid-19", regex=True)
        df["disease"] = df["disease"].replace(DISEASE_MAP, regex=True)
        df["disease"] = df["disease"].str.title().str.strip()
        # Final explicit fix if any remained
        df["disease"] = df["disease"].replace({"Covid-19-19": "Covid-19"})
    return df

def filter_rows(df: pd.DataFrame) -> pd.DataFrame:
    needed = ["state", "disease", "year", "week"]
    df = df.dropna(subset=[c for c in needed if c in df.columns])
    if "year" in df.columns:
        df = df[(df["year"] >= 2016) & (df["year"] <= 2026)]
    if "week" in df.columns:
        df = df[(df["week"] >= 1) & (df["week"] <= 53)]
    df = df[df["cases"] >= 0]
    df = df[df["deaths"] >= 0]
    return df

def select_and_save(df: pd.DataFrame) -> None:
    cols = ["state", "disease", "year", "week", "cases", "deaths"]
    for c in cols:
        if c not in df.columns:
            raise ValueError(f"Missing required column after cleaning: {c}")
    df = df[cols].reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Cleaned file saved: {OUT}  (rows={len(df)})")

def main():
    df = load_source()
    df = guess_and_rename_columns(df)
    df = normalize_text(df)
    df = derive_year_week(df)
    df = ensure_numeric(df)
    df = normalize_disease(df)
    df = filter_rows(df)
    select_and_save(df)

if __name__ == "__main__":
    main()