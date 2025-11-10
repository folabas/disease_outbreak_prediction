import io
import sys
from pathlib import Path

import pandas as pd
from datetime import date

SRC = Path("data") / "ncdc_outbreaks_clean.csv"
OUT = SRC  # overwrite in place


def read_blocks(text: str):
    lines = text.splitlines()
    # Find index where the richer schema header begins
    target_header = "week,year,week_num,disease,state,cases,deaths,cfr,report_date".lower()
    idx = None
    for i, line in enumerate(lines):
        if line.strip().lower() == target_header:
            idx = i
            break
    if idx is None:
        return text, None
    first_block = "\n".join(lines[:idx])
    second_block = "\n".join(lines[idx:])
    return first_block, second_block


def to_richer_schema(df_simple: pd.DataFrame) -> pd.DataFrame:
    # Expect columns: state,disease,year,week,cases,deaths
    rename = {"state": "state", "disease": "disease", "year": "year", "week": "week", "cases": "cases", "deaths": "deaths"}
    df = df_simple.rename(columns=rename)
    # Normalize types
    for c in ["year", "week", "cases", "deaths"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["state", "disease", "year", "week"]).copy()
    df["year"] = df["year"].astype(int)
    df["week_num"] = df["week"].astype(int)
    # Compute CFR (%), guard zero cases
    df["cfr"] = (df["deaths"] / df["cases"]).replace([pd.NA, pd.NaT], 0).fillna(0)
    df["cfr"] = df["cfr"].where(df["cases"] > 0, 0) * 100
    df["cfr"] = df["cfr"].round(2)
    # Compute ISO week Monday date as report_date
    def iso_monday(y, w):
        try:
            return date(int(y), 1, 4).fromisocalendar(int(y), int(w), 1)
        except Exception:
            try:
                return date.fromisocalendar(int(y), int(w), 1)
            except Exception:
                return pd.NaT

    df["report_date"] = [iso_monday(y, w) for y, w in zip(df["year"], df["week_num"])]
    # Align disease naming: title case and fix covid specifically
    df["disease"] = df["disease"].astype(str).str.strip()
    df["disease"] = df["disease"].str.replace(r"(?i)covid[-\s]?19", "COVID-19", regex=True)
    df["disease"] = df["disease"].str.title()
    # Final column order to match richer schema
    df_rich = df[["week", "year", "week_num", "disease", "state", "cases", "deaths", "cfr", "report_date"]].copy()
    return df_rich


def load_second_block(block_text: str) -> pd.DataFrame:
    # Read with pandas from in-memory text
    df = pd.read_csv(io.StringIO(block_text))
    # Normalize numeric
    for c in ["year", "week", "week_num", "cases", "deaths", "cfr"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # Clean disease naming for consistency
    if "disease" in df.columns:
        df["disease"] = df["disease"].astype(str).str.strip()
        df["disease"] = df["disease"].str.replace(r"(?i)covid[-\s]?19", "COVID-19", regex=True)
        df["disease"] = df["disease"].str.title()
    # Ensure required columns exist
    required = ["week", "year", "week_num", "disease", "state", "cases", "deaths", "cfr", "report_date"]
    for c in required:
        if c not in df.columns:
            df[c] = pd.NA
    # Reorder
    df = df[required].copy()
    return df


def main():
    if not SRC.exists():
        print(f"Source not found: {SRC}")
        sys.exit(1)
    text = SRC.read_text(encoding="utf-8")
    first_block, second_block = read_blocks(text)
    if second_block is None:
        print("Richer schema header not found; leaving file unchanged.")
        sys.exit(0)
    # Load simple block
    df_simple = pd.read_csv(io.StringIO(first_block))
    # Convert simple to rich
    df_rich_from_simple = to_richer_schema(df_simple)
    # Load rich block
    df_rich_existing = load_second_block(second_block)
    # Combine
    df_all = pd.concat([df_rich_existing, df_rich_from_simple], ignore_index=True)
    # Drop duplicates if any
    df_all = df_all.drop_duplicates(subset=["year", "week_num", "disease", "state", "cases", "deaths"])
    # Sort for readability
    df_all = df_all.sort_values(by=["year", "week_num", "disease", "state"]).reset_index(drop=True)
    # Write out
    df_all.to_csv(OUT, index=False)
    print(f"Merged schemas. Wrote {len(df_all)} rows to {OUT}.")


if __name__ == "__main__":
    main()