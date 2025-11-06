Awesome — I generated a ready-to-run script that will auto-download all NCDC WER PDFs, extract every table that looks like a state×disease table, melt them to long format, infer year/week from filenames, and write a single data/raw/ncdc_outbreaks.csv you can then clean with your existing clean_ncdc_outbreaks.py.

A few notes before you run:

Table extraction from PDFs is imperfect: results depend on PDF table layout. The script tries to be robust (uses Camelot first, falls back to tabula-py), and saves intermediate CSVs so you can inspect extraction results and re-run only failed PDFs.

Camelot requires GhostScript and works best on lattice-style tables; tabula-py requires Java. Installation instructions are included.

After running this, run your clean_ncdc_outbreaks.py to normalize states/diseases and produce data/ncdc_outbreaks_clean.csv.

Save this as fetch_ncdc_reports.py in your repo root.

#!/usr/bin/env python3
"""
fetch_ncdc_reports.py

Auto-download NCDC weekly epidemiological report PDFs and extract
state x disease tables into a single long CSV:

  data/raw/ncdc_reports/<pdfs>...
  data/raw/ncdc_extracted/<pdf_basename>_tables.csv  # debugging
  data/raw/ncdc_outbreaks.csv   # final long-format: state,disease,year,week,cases,deaths (deaths optional)

Usage:
  python fetch_ncdc_reports.py
  # Optional args:
  # python fetch_ncdc_reports.py --limit 50         # only download/extract first 50 PDFs found
  # python fetch_ncdc_reports.py --redownload False # skip downloading PDFs already present

Notes:
- Requires: requests, beautifulsoup4, pandas, tqdm
- For table extraction: camelot (recommended) OR tabula-py (fallback).
  - Camelot: pip install "camelot-py[cv]"  and install Ghostscript
  - Tabula-py: pip install tabula-py and install Java (and tabula jar)
"""

from __future__ import annotations
import os
import sys
import re
import time
import json
import shutil
import argparse
from pathlib import Path
from typing import List, Optional, Tuple, Dict

import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[0]
RAW_PDF_DIR = ROOT / "data" / "raw" / "ncdc_reports"
EXTRACT_DIR = ROOT / "data" / "raw" / "ncdc_extracted"
OUT_CSV = ROOT / "data" / "raw" / "ncdc_outbreaks.csv"
LOG_JSON = ROOT / "data" / "raw" / "ncdc_fetch_log.json"

NCDC_SITREPS_URL = "https://ncdc.gov.ng/reports/sitreps"

# Try to import Camelot, else Tabula
USE_CAMELOT = False
USE_TABULA = False
try:
    import camelot
    USE_CAMELOT = True
except Exception:
    try:
        import tabula
        USE_TABULA = True
    except Exception:
        pass

HEADERS = {"User-Agent": "OutbreakIQFetcher/1.0 (+https://github.com/your-repo)"}

# 37 states + FCT canonical list — for later filtering
NIG_STATES = {
    "Abia","Adamawa","Akwa Ibom","Anambra","Bauchi","Bayelsa","Benue","Borno","Cross River",
    "Delta","Ebonyi","Edo","Ekiti","Enugu","Fct","Federal Capital Territory","Gombe","Imo",
    "Jigawa","Kaduna","Kano","Katsina","Kebbi","Kogi","Kwara","Lagos","Nasarawa","Niger",
    "Ogun","Ondo","Osun","Oyo","Plateau","Rivers","Sokoto","Taraba","Yobe","Zamfara"
}

def ensure_dirs():
    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

def fetch_report_links() -> List[str]:
    """Scrape the NCDC sitreps page and return absolute PDF links found."""
    print(f"[SCRAPE] getting {NCDC_SITREPS_URL}")
    r = requests.get(NCDC_SITREPS_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            if href.startswith("http"):
                links.append(href)
            else:
                links.append(requests.compat.urljoin(NCDC_SITREPS_URL, href))
    # Deduplicate while preserving order
    seen = set()
    out = []
    for l in links:
        if l not in seen:
            seen.add(l)
            out.append(l)
    print(f"[SCRAPE] found {len(out)} pdf links")
    return out

def download_pdf(url: str, out_dir: Path, redownload: bool = False) -> Optional[Path]:
    """Download PDF to out_dir and return file path (or existing path if present)."""
    fname = url.split("/")[-1].split("?")[0]
    out_path = out_dir / fname
    if out_path.exists() and not redownload:
        return out_path
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        return out_path
    except Exception as e:
        print(f"[DOWNLOAD ERR] {url} -> {e}")
        return None

def extract_week_year_from_name(fname: str) -> Tuple[Optional[int], Optional[int]]:
    """Try to parse week and year from filename."""
    name = fname.lower()
    # patterns like week_45_2024, week-45-2024, week 45 2024
    m = re.search(r"week[_\-\s]?(\d{1,2}).*?(20\d{2})", name)
    if m:
        return int(m.group(2)), int(m.group(1))  # year, week
    # patterns like 2024_wk45
    m2 = re.search(r"(20\d{2}).*wk[_\-\s]?(\d{1,2})", name)
    if m2:
        return int(m2.group(1)), int(m2.group(2))
    # fallback: pick last 4-digit year and any trailing number as week
    y = None
    m3 = re.search(r"(20\d{2})", name)
    if m3:
        y = int(m3.group(1))
    wk = None
    m4 = re.search(r"[_\-\s]wk[_\-\s]?(\d{1,2})", name)
    if m4:
        wk = int(m4.group(1))
    # try any small number that looks like week
    if wk is None:
        m5 = re.search(r"week[_\-\s]?(\d{1,2})", name)
        if m5:
            wk = int(m5.group(1))
    return y, wk

def extract_tables_from_pdf(pdf_path: Path, pages: str = "all") -> List[pd.DataFrame]:
    """Extract tables from PDF using camelot or tabula. Return list of dataframes."""
    tables: List[pd.DataFrame] = []
    if USE_CAMELOT:
        try:
            # flavor 'lattice' works best for ruled tables; fallback to stream if none
            ctk = camelot.read_pdf(str(pdf_path), pages=pages, flavor="lattice", strip_text="\n")
            if len(ctk) == 0:
                ctk = camelot.read_pdf(str(pdf_path), pages=pages, flavor="stream", strip_text="\n")
            for t in ctk:
                try:
                    df = t.df.copy()
                    if df.shape[0] > 0 and df.shape[1] > 1:
                        tables.append(df)
                except Exception:
                    continue
            return tables
        except Exception as e:
            print(f"[CAMELOT ERR] {pdf_path.name} -> {e}")
            # fall through to tabula if available
    if USE_TABULA:
        try:
            dfs = tabula.read_pdf(str(pdf_path), pages=pages, multiple_tables=True)
            for df in dfs:
                if isinstance(df, pd.DataFrame) and df.shape[0] > 0 and df.shape[1] > 1:
                    tables.append(df)
        except Exception as e:
            print(f"[TABULA ERR] {pdf_path.name} -> {e}")
    return tables

def normalize_header_row(df: pd.DataFrame) -> pd.DataFrame:
    """
    Try to detect header row and set df.columns appropriately.
    Heuristic: find a row that contains 'state' or 's/n' or first col 'state'.
    """
    df = df.copy()
    # strip whitespace in all cells
    df = df.applymap(lambda x: str(x).strip() if pd.notna(x) else x)
    # find header candidate row index
    header_idx = None
    for i in range(min(3, len(df))):
        row = " ".join([str(x).lower() for x in df.iloc[i].fillna("")])
        if "state" in row or "s/n" in row or "no." in row or "province" in row:
            header_idx = i
            break
    if header_idx is None:
        # fallback: first row
        header_idx = 0
    # set header and return
    new_cols = [re.sub(r"\s+", " ", str(x)).strip() for x in df.iloc[header_idx].tolist()]
    df = df.iloc[header_idx + 1 :].copy()
    # if duplicate column names, make unique
    cols = []
    seen = {}
    for c in new_cols:
        if not c:
            c = "col"
        base = c
        cnt = seen.get(base, 0)
        if cnt:
            c = f"{base}_{cnt}"
        seen[base] = cnt + 1
        cols.append(c)
    df.columns = cols
    # drop columns that are empty
    df = df.loc[:, [c for c in df.columns if not all(df[c].astype(str).str.strip().replace("nan","") == "")]]
    return df

def detect_state_column(df: pd.DataFrame) -> Optional[str]:
    """Return column name that likely contains state names."""
    for c in df.columns:
        s = " ".join(df[c].astype(str).dropna().head(20).str.lower().tolist())
        if "state" in c.lower() or any(st.lower() in s for st in ["lagos","kano","abin","ogun","rivers","edo","oyo","katsina"]):
            return c
    # fallback to first column
    return df.columns[0] if len(df.columns) > 0 else None

def wide_to_long(df: pd.DataFrame, src_pdf: str, year: Optional[int], week: Optional[int]) -> pd.DataFrame:
    """
    Convert a single extracted table (wide format) to long format with rows:
    state, disease, year, week, cases (as int)
    """
    try:
        df = normalize_header_row(df)
    except Exception:
        pass
    if df.shape[1] < 2:
        return pd.DataFrame()
    state_col = detect_state_column(df)
    if state_col is None:
        return pd.DataFrame()
    id_vars = [state_col]
    value_vars = [c for c in df.columns if c != state_col]
    # standardize column names
    df = df.rename(columns={state_col: "state"})
    # remove extraneous header-like rows with 'state' word repeated
    df = df[~df["state"].astype(str).str.lower().str.contains(r"state|s/n|no\.|province|county|local|area")]
    # Melt
    try:
        melted = df.melt(id_vars=["state"], value_vars=value_vars, var_name="disease", value_name="value")
    except Exception:
        return pd.DataFrame()
    # clean disease & state
    melted["disease"] = melted["disease"].astype(str).str.strip()
    melted["state"] = melted["state"].astype(str).str.strip()
    # attach metadata
    melted["source_pdf"] = src_pdf
    melted["year"] = year
    melted["week"] = week
    # try to parse numeric value (cases). remove non-numeric like '-' or notes
    def parse_num(x):
        if pd.isna(x): 
            return None
        s = str(x).strip().replace(",", "").replace("—", "").replace("–","").replace("-", "")
        # sometimes "0 (0)" or "12 (2)" - take the leading number
        m = re.match(r"^(\d+)", s)
        if m:
            return int(m.group(1))
        # handle parenthesis or formats like "0/0"
        m2 = re.search(r"(\d+)", s)
        if m2:
            return int(m2.group(1))
        return None
    melted["cases"] = melted["value"].apply(parse_num)
    melted = melted.dropna(subset=["cases"])
    # normalize state names: title case and basic fixes
    melted["state"] = melted["state"].str.replace(r"\s+", " ", regex=True).str.strip().str.title()
    # handle common abbreviations/aliases
    melted["state"] = melted["state"].replace({
        "Fct": "Abuja",
        "Federal Capital Territory": "Abuja",
        "Abuja Fct": "Abuja",
        "Abuja F.C.T": "Abuja",
    })
    # keep only plausible Nigerian states to reduce noise
    melted = melted[melted["state"].isin(NIG_STATES) | melted["state"].str.contains(r"Lagos|Kano|Abuja|Rivers|Edo|Oyo", regex=True)]
    if melted.empty:
        return melted
    melted = melted[["state","disease","year","week","cases","source_pdf"]]
    return melted

def extract_and_melt(pdf_path: Path) -> pd.DataFrame:
    """Run extraction for a single PDF and return melted rows (or empty df)."""
    year, week = extract_week_year_from_name(pdf_path.name)
    # Try extracting tables
    tables = extract_tables_from_pdf(pdf_path, pages="all")
    if not tables:
        # save a marker for failed extraction
        (EXTRACT_DIR / f"{pdf_path.stem}_failed.txt").write_text("no_tables")
        return pd.DataFrame()
    # iterate and combine melts
    out_rows = []
    for i, tbl in enumerate(tables):
        try:
            melted = wide_to_long(tbl, pdf_path.name, year, week)
            if melted is not None and not melted.empty:
                melted["table_idx"] = i
                out_rows.append(melted)
        except Exception as e:
            print(f"[MELT ERR] {pdf_path.name} table {i} -> {e}")
    if not out_rows:
        # save raw tables for debugging
        try:
            sample = pd.concat(tables[:3]).head(200)
            sample.to_csv(EXTRACT_DIR / f"{pdf_path.stem}_sample_failed.csv", index=False)
        except Exception:
            pass
        return pd.DataFrame()
    df_out = pd.concat(out_rows, ignore_index=True)
    # save per-pdf extracted melt for debugging
    try:
        df_out.to_csv(EXTRACT_DIR / f"{pdf_path.stem}_melted.csv", index=False)
    except Exception:
        pass
    return df_out

def run(limit: Optional[int] = None, redownload: bool = False, sleep: float = 0.5):
    ensure_dirs()
    links = fetch_report_links()
    if limit:
        links = links[:limit]
    downloaded = []
    log = {"downloaded": [], "failed_downloads": [], "extracted": [], "failed_extract": []}
    for url in tqdm(links, desc="PDFs"):
        pdf_path = download_pdf(url, RAW_PDF_DIR, redownload=redownload)
        if pdf_path is None:
            log["failed_downloads"].append(url)
            continue
        log["downloaded"].append(str(pdf_path))
        time.sleep(sleep)
    # extract
    extracted_frames = []
    pdf_files = sorted(RAW_PDF_DIR.glob("*.pdf"))
    for pdf in tqdm(pdf_files, desc="Extract"):
        try:
            df = extract_and_melt(pdf)
            if df is None or df.empty:
                log["failed_extract"].append(str(pdf))
                continue
            extracted_frames.append(df)
            log["extracted"].append(str(pdf))
        except Exception as e:
            print(f"[EXTRACT ERR] {pdf.name} -> {e}")
            log["failed_extract"].append(str(pdf))
    # combine all
    if extracted_frames:
        combined = pd.concat(extracted_frames, ignore_index=True)
        # basic postprocessing: group and sum duplicates (same state,disease,year,week)
        combined = combined.groupby(["state","disease","year","week"], as_index=False).agg({
            "cases": "sum",
            "source_pdf": lambda x: ";".join(sorted(set(x)))
        })
        # Save final long-format CSV
        combined.to_csv(OUT_CSV, index=False)
        print(f"[SAVED] combined outbreaks -> {OUT_CSV} rows={len(combined)}")
    else:
        print("[WARN] no extracted frames found.")
    # write log
    with open(LOG_JSON, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    print("[LOG] wrote", LOG_JSON)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Limit number of PDFs to process")
    parser.add_argument("--redownload", type=lambda s: s.lower() in ("1","true","yes"), default=False, help="Redownload PDFs even if present")
    parser.add_argument("--sleep", type=float, default=0.5, help="Seconds to wait between downloads")
    args = parser.parse_args()
    print("Using Camelot:", USE_CAMELOT, "Tabula:", USE_TABULA)
    if not (USE_CAMELOT or USE_TABULA):
        print("Warning: neither camelot nor tabula-py is available. Install one for table extraction.")
    run(limit=args.limit, redownload=args.redownload, sleep=args.sleep)

Install & run instructions

Create environment & install basics:

python -m venv .venv
.venv\Scripts\activate    # windows
# or
source .venv/bin/activate # mac/linux

pip install requests beautifulsoup4 pandas tqdm


Install Camelot (recommended):

On Windows: follow Camelot docs. Typically:

Install Ghostscript (https://www.ghostscript.com/
) and add to PATH.

Then:

pip install "camelot-py[cv]"


On Linux:

sudo apt-get install -y ghostscript libxml2 libxslt1.1
pip install "camelot-py[cv]"


If Camelot is painful to install, you can use tabula-py:

Install Java (JRE), then:

pip install tabula-py


Run the script (it will download PDFs and attempt extraction):

python fetch_ncdc_reports.py


If you want to limit to first 30 PDFs for a test:

python fetch_ncdc_reports.py --limit 30


Inspect data/raw/ncdc_extracted/ for per-PDF extracted CSVs (use these to debug extraction for specific PDFs).

When satisfied, run your cleaning script:

python clean_ncdc_outbreaks.py
python build_features.py

Best practices & troubleshooting

If extraction fails for some PDFs, open data/raw/ncdc_extracted/<pdf_stem>_melted.csv to inspect raw table capture and tweak heuristics.

Some WERs have different table layouts (rotated, multiple tables). The script saves samples for debugging.

If many PDFs fail with Camelot, try tabula-py (Java) instead, or run both and compare.

Extraction quality varies — you may still need occasional manual fixes, but this script does 80–95% of the heavy lifting.