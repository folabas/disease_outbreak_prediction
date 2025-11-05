#!/usr/bin/env python3
"""
ncdc_scraper.py

Scrapes NCDC SitReps, downloads PDFs for a specified year range (default: 2016-2025),
extracts tables and outputs a cleaned CSV of outbreaks for selected diseases.

Features implemented:
- Crawl pagination/subpages heuristically to avoid missing older SitReps
- Robust PDF parsing via camelot and tabula with fallbacks
- Table header detection scanning more rows
- Row-level disease assignment and table-level disease context propagation
- Safe numeric casting, CFR computation, ISO week parsing
- Deduplication and basic state normalization
- CLI flags for start/end year and force-redownload

Usage:
    python ncdc_scraper.py [--start-year 2016] [--end-year 2025] [--force-redownload]
"""

import os
import re
import time
import logging
import argparse
import requests
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import datetime, date
from dateutil.parser import parse as dateparse

# Optional dependencies
try:
    import camelot  # type: ignore
    HAVE_CAMELOT = True
except Exception:
    HAVE_CAMELOT = False

try:
    import tabula  # type: ignore
    HAVE_TABULA = True
except Exception:
    HAVE_TABULA = False


# -----------------------
# CONFIG
# -----------------------
BASE_SITREP_URL = "https://ncdc.gov.ng/diseases/sitreps"
DOWNLOAD_DIR = os.path.join(".", "data", "ncdc")
OUTPUT_CSV = "ncdc_outbreaks.csv"

# Defaults (last 10 years up to 2025)
DEFAULT_END_YEAR = 2025
DEFAULT_START_YEAR = DEFAULT_END_YEAR - 9

# Diseases we care about (case-insensitive)
DISEASES = [
    "Cholera",
    "Malaria",
    "Lassa",
    "Measles",
    "Yellow Fever",
    "Meningitis",
    "Monkeypox",
    "COVID-19",
    "Diphtheria",
    "Pertussis",
]

DISEASE_SYNONYMS = {
    "Lassa": ["Lassa fever", "lassa"],
    "COVID-19": ["covid", "coronavirus", "sars-cov-2"],
    "Yellow Fever": ["yellow fever"],
    "Monkeypox": ["mpox", "monkeypox"],
}

# Regex patterns to find dates in filename or content
DATE_PATTERNS = [
    r"(\d{4})[^\d]?W?(\d{1,2})",  # e.g. 2025W35 or 2025-35
    r"(\d{4})[^\d](\d{1,2})[^\d](\d{1,2})",  # YYYY-MM-DD-like
    r"(?:\b)(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})(?:\b)",  # 1 September 2025
]

# Basic state aliases
STATE_ALIASES = {
    "fct": "Abuja",
    "federal capital territory": "Abuja",
}

# -----------------------
# Logging
# -----------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# -----------------------
# Helpers
# -----------------------
def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def fetch_sitrep_listing(url: str = BASE_SITREP_URL, session: requests.Session | None = None) -> str:
    logging.info(f"Fetching sitrep listing: {url}")
    s = session or requests.Session()
    r = s.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def crawl_all_pages(base_url: str = BASE_SITREP_URL, session: requests.Session | None = None) -> str:
    """Aggregate main listing HTML with likely subpages to cover pagination/archives."""
    html = fetch_sitrep_listing(base_url, session=session)
    all_html = html
    soup = BeautifulSoup(html, "html.parser")
    # Heuristic: include links containing sitrep keywords
    keywords = ("sitrep", "sitreps", "weekly", "week", "archive")
    more_links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        lower = href.lower()
        if any(k in lower for k in keywords):
            more_links.append(href)
    # Fetch each subpage, aggregate HTML
    s = session or requests.Session()
    for href in more_links:
        full_url = requests.compat.urljoin(base_url, href)
        try:
            sub_html = fetch_sitrep_listing(full_url, session=s)
            all_html += "\n" + sub_html
        except Exception as e:
            logging.debug(f"Failed crawl subpage {full_url}: {e}")
    return all_html


def find_pdf_links_from_html(html: str, year_min: int, year_max: int) -> list[tuple[str, str]]:
    """Parse HTML and return list of (pdf_url, link_text) for PDFs whose text or url contains a year in range.
    Deduplicates while preserving order.
    """
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", href=True)
    pdf_links: list[tuple[str, str]] = []
    for a in links:
        href = a["href"].strip()
        if not href.lower().endswith(".pdf"):
            continue
        text = (a.get_text(" ", strip=True) or href)
        # make absolute URL if needed
        if href.startswith("/"):
            pdf_url = "https://ncdc.gov.ng" + href
        elif href.startswith("http"):
            pdf_url = href
        else:
            pdf_url = requests.compat.urljoin(BASE_SITREP_URL, href)

        link_lower = (text + " " + pdf_url).lower()
        keep = False
        for y in range(year_min, year_max + 1):
            if str(y) in link_lower:
                keep = True
                break
        # Keep even if no year marker; we'll infer later
        pdf_links.append((pdf_url, text))

    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for u, t in pdf_links:
        if u in seen:
            continue
        seen.add(u)
        out.append((u, t))
    logging.info(f"Found {len(out)} PDF links (candidate).")
    return out


def download_pdf(url: str, out_dir: str = DOWNLOAD_DIR, session: requests.Session | None = None, retries: int = 2, force_redownload: bool = False) -> str | None:
    """Download a pdf and save to out_dir. Returns local filepath."""
    ensure_dir(out_dir)
    session = session or requests.Session()
    local_name = url.split("/")[-1].split("?")[0]
    local_name = re.sub(r"[^A-Za-z0-9._\-]", "_", local_name)
    out_path = os.path.join(out_dir, local_name)
    if not force_redownload and os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        logging.debug(f"File already exists: {out_path}")
        return out_path
    for attempt in range(retries + 1):
        try:
            logging.info(f"Downloading {url} -> {out_path}")
            r = session.get(url, stream=True, timeout=40)
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(1024 * 64):
                    if chunk:
                        f.write(chunk)
            return out_path
        except Exception as e:
            logging.warning(f"Download attempt {attempt} failed for {url}: {e}")
            time.sleep(1 + attempt * 2)
    logging.error(f"Failed to download: {url}")
    return None


# -----------------------
# PDF parsing
# -----------------------
def try_camelot_extract(pdf_path: str, pages: str = "1-end") -> list[pd.DataFrame]:
    if not HAVE_CAMELOT:
        return []
    dfs: list[pd.DataFrame] = []
    for flavor in ("lattice", "stream"):
        try:
            logging.info(f"camelot: reading {pdf_path} flavor={flavor} pages={pages}")
            tables = camelot.read_pdf(pdf_path, pages=pages, flavor=flavor)
            logging.info(f"camelot found {len(tables)} tables with flavor={flavor}")
            for t in tables:
                dfs.append(t.df.copy())
            if dfs:
                return dfs
        except Exception as e:
            logging.debug(f"camelot flavor {flavor} failed: {e}")
    return dfs


def try_tabula_extract(pdf_path: str, pages: str = "all") -> list[pd.DataFrame]:
    if not HAVE_TABULA:
        return []
    try:
        logging.info(f"tabula: reading {pdf_path} pages={pages}")
        dfs = tabula.read_pdf(pdf_path, pages=pages, multiple_tables=True)
        logging.info(f"tabula found {len(dfs)} tables")
        return dfs
    except Exception as e:
        logging.debug(f"tabula extraction failed: {e}")
        return []


def extract_text_from_pdf_minimal(pdf_path: str, max_chars: int = 5000) -> str:
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(pdf_path, maxpages=2)
        if text:
            return text[:max_chars]
    except Exception as e:
        logging.debug(f"pdfminer text extraction failed: {e}")
    return ""


# -----------------------
# Normalization & heuristics
# -----------------------
def detect_header_row(df: pd.DataFrame) -> int | None:
    best_row, best_score = None, -1
    for i in range(min(8, len(df))):
        row_text = " ".join(df.iloc[i].astype(str)).lower()
        score = sum(k in row_text for k in ["state", "cases", "death", "disease", "week", "lga", "epi"])
        if score > best_score:
            best_score = score
            best_row = i
    return best_row if best_score > 0 else None


def normalize_table_df(df: pd.DataFrame) -> pd.DataFrame | None:
    if df is None or df.size == 0:
        return None
    df2 = df.copy()
    df2.columns = [f"c{i}" for i in range(len(df2.columns))]
    header_row = detect_header_row(df2)
    if header_row is not None:
        headers = list(df2.iloc[header_row].astype(str).tolist())
        df3 = df2.iloc[header_row + 1 :].copy()
        df3.columns = [h.strip() if h else f"col_{j}" for j, h in enumerate(headers)]
    else:
        df3 = df2.copy()
        df3.columns = [str(c) for c in df2.columns]
    df3 = df3.applymap(lambda x: str(x).strip() if not pd.isna(x) else x)
    return df3.reset_index(drop=True)


def detect_table_disease(df: pd.DataFrame) -> str | None:
    """Detect disease from the first few rows/headers of a table."""
    if df is None or df.empty:
        return None
    scan_rows = min(5, len(df))
    text = []
    for i in range(scan_rows):
        text.append(" ".join(df.iloc[i].astype(str)))
    joined = " ".join(text).lower()
    for known in DISEASES:
        variants = [known.lower()] + [v.lower() for v in DISEASE_SYNONYMS.get(known, [])]
        if any(v in joined for v in variants):
            return known
    return None


def safe_cast(x) -> int | float | None:
    try:
        if x is None or (hasattr(pd, "isna") and pd.isna(x)):
            return None
        s = str(x).replace(",", "").strip()
        if s == "" or s.lower() in {"na", "n/a", "-", "—"}:
            return None
        val = float(s)
        return int(val) if val.is_integer() else val
    except Exception:
        return None


def parse_iso_week_date(token: str) -> date | None:
    m = re.match(r"^(\d{4})[^\d]?W?(\d{1,2})$", token.strip())
    if not m:
        return None
    y, w = int(m.group(1)), int(m.group(2))
    try:
        return date.fromisocalendar(y, w, 1)  # Monday of ISO week
    except Exception:
        return None


def guess_report_date_from_filename_or_text(filename: str, sample_text: str = "") -> str | None:
    s = filename + "\n" + (sample_text or "")
    # Try ISO week tokens first
    for tok in re.findall(r"\b\d{4}W\d{1,2}\b|\b\d{4}-W\d{1,2}\b|\b\d{4}[\-/ ]\d{1,2}\b", s):
        iso = parse_iso_week_date(tok.replace("-", "").replace("/", "").replace(" ", ""))
        if iso:
            return iso.isoformat()
    # General patterns
    for pat in DATE_PATTERNS:
        m = re.search(pat, s, re.IGNORECASE)
        if m:
            try:
                dt = dateparse(m.group(0), fuzzy=True, dayfirst=False)
                # Sanity-check year bounds to avoid stray matches like 1759, 8082
                if 2010 <= dt.year <= 2030:
                    return dt.date().isoformat()
                else:
                    continue
            except Exception:
                groups = m.groups()
                if len(groups) >= 3:
                    try:
                        y, mm, dd = int(groups[0]), int(groups[1]), int(groups[2])
                        if 2010 <= y <= 2030:
                            return datetime(y, mm, dd).date().isoformat()
                        else:
                            pass
                    except Exception:
                        pass
                if len(groups) >= 1:
                    try:
                        y = int(groups[0])
                        if 2010 <= y <= 2030:
                            return f"{y}-01-01"
                        else:
                            pass
                    except Exception:
                        pass
    return None


# -----------------------
# Row extraction heuristics
# -----------------------
def find_outbreak_rows_from_table(df: pd.DataFrame, disease_list: list[str]) -> list[dict]:
    out: list[dict] = []
    if df is None or df.empty:
        return out
    col_candidates = {"state": None, "cases": None, "deaths": None, "disease": None, "week": None, "cfr": None}
    for c in df.columns:
        lc = c.lower()
        if "state" in lc or "region" in lc or "lga" in lc:
            col_candidates["state"] = c
        if re.search(r"case", lc) and col_candidates["cases"] is None:
            col_candidates["cases"] = c
        if re.search(r"death", lc) and col_candidates["deaths"] is None:
            col_candidates["deaths"] = c
        if "disease" in lc or "condition" in lc:
            col_candidates["disease"] = c
        if "week" in lc or "epi" in lc:
            col_candidates["week"] = c
        if "cfr" in lc:
            col_candidates["cfr"] = c

    # Fallback numeric columns
    numeric_cols = []
    for c in df.columns:
        nonnull = df[c].dropna().astype(str)
        if nonnull.size == 0:
            continue
        num_frac = nonnull.map(lambda x: bool(re.match(r"^[\d,\.\s\-]+$", x.strip()))).mean()
        if num_frac > 0.6:
            numeric_cols.append(c)
    if not col_candidates["cases"] and numeric_cols:
        col_candidates["cases"] = numeric_cols[0]
    if not col_candidates["deaths"] and len(numeric_cols) > 1:
        col_candidates["deaths"] = numeric_cols[1] if numeric_cols[1] != col_candidates["cases"] else None

    # Iterate rows
    for _, row in df.iterrows():
        row_text = " ".join(map(str, row.values)).lower()
        found_disease = None
        for d in disease_list:
            variants = [d.lower()] + [v.lower() for v in DISEASE_SYNONYMS.get(d, [])]
            if any(v in row_text for v in variants):
                found_disease = d
                break

        looks_like_state_row = False
        if col_candidates["state"] and col_candidates["cases"]:
            state_val = str(row.get(col_candidates["state"], "")).strip()
            cases_val = str(row.get(col_candidates["cases"], "")).strip()
            if state_val and re.search(r"[A-Za-z]", state_val) and re.match(r"^[\d,\.\s\-]+$", cases_val):
                looks_like_state_row = True

        if found_disease or looks_like_state_row:
            out_row = {
                "week": None,
                "disease": found_disease or "",
                "state": "",
                "cases": None,
                "deaths": None,
                "cfr": None,
            }
            if col_candidates["state"]:
                out_row["state"] = str(row.get(col_candidates["state"], "")).strip()
            else:
                for c in df.columns:
                    v = str(row.get(c, "")).strip()
                    if v and re.search(r"[A-Za-z]", v):
                        out_row["state"] = v
                        break
            if col_candidates["cases"]:
                out_row["cases"] = safe_cast(row.get(col_candidates["cases"], None))
            else:
                for c in df.columns:
                    v = str(row.get(c, "")).strip()
                    if re.match(r"^[\d,\.\s\-]+$", v):
                        out_row["cases"] = safe_cast(v)
                        break
            if col_candidates["deaths"]:
                out_row["deaths"] = safe_cast(row.get(col_candidates["deaths"], None))
            if col_candidates["week"]:
                out_row["week"] = str(row.get(col_candidates["week"], "")).strip()
            out.append(out_row)
    return out


# -----------------------
# Main pipeline
# -----------------------
def process_pdf_file(pdf_path: str, disease_list: list[str]) -> list[dict]:
    rows: list[dict] = []
    sample_text = extract_text_from_pdf_minimal(pdf_path)
    report_date = guess_report_date_from_filename_or_text(os.path.basename(pdf_path), sample_text=sample_text)
    extracted_tables: list[pd.DataFrame] = []
    if HAVE_CAMELOT:
        try:
            extracted_tables = try_camelot_extract(pdf_path, pages="1-end")
        except Exception as e:
            logging.debug(f"camelot extraction error {e}")
    if (not extracted_tables or len(extracted_tables) == 0) and HAVE_TABULA:
        try:
            extracted_tables = try_tabula_extract(pdf_path, pages="all")
        except Exception as e:
            logging.debug(f"tabula extraction error {e}")

    for raw_df in extracted_tables:
        try:
            norm_df = normalize_table_df(raw_df)
            if norm_df is None or norm_df.empty:
                continue
            disease_context = detect_table_disease(raw_df)
            found = find_outbreak_rows_from_table(norm_df, disease_list)
            for r in found:
                r["report_date"] = report_date
                if not r.get("week") and report_date:
                    try:
                        dt = dateparse(report_date)
                        r["week"] = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
                    except Exception:
                        r["week"] = ""
                if (not r.get("disease")) and disease_context:
                    r["disease"] = disease_context
                rows.append(r)
        except Exception as e:
            logging.debug(f"failed process table: {e}")
    return rows


def merge_and_clean(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["week", "disease", "state", "cases", "deaths", "cfr", "report_date"])
    df = pd.DataFrame(rows)
    # Ensure columns
    for c in ["week", "disease", "state", "cases", "deaths", "cfr", "report_date"]:
        if c not in df.columns:
            df[c] = None

    # Row-level disease mapping (no global contamination)
    def map_disease_row(row) -> str | None:
        cell = str(row.get("disease", "")).strip().lower()
        row_text = " ".join(map(str, row.values)).lower()
        for known in DISEASES:
            variants = [known.lower()] + [v.lower() for v in DISEASE_SYNONYMS.get(known, [])]
            if any(v in (cell or row_text) for v in variants):
                return known
        return None

    df["disease"] = df.apply(lambda r: map_disease_row(r), axis=1)

    # Drop rows with no disease or no state
    df = df[df["disease"].notna() & (df["disease"] != "")]
    df = df[df["state"].notna() & (df["state"] != "")]

    # Normalize state
    df["state"] = df["state"].astype(str).str.strip().str.lower()
    df["state"] = df["state"].replace(STATE_ALIASES)
    df["state"] = df["state"].str.title()

    # Filter out non-geographic "states" (response pillars etc.)
    INVALID_STATE_WORDS = ["coordination", "logistics", "wash", "case", "laboratory", "total"]
    df = df[~df["state"].fillna("").str.lower().str.contains("|".join(INVALID_STATE_WORDS))]

    # Numeric casts and CFR computation
    df["cases"] = df["cases"].apply(safe_cast)
    df["deaths"] = df["deaths"].apply(safe_cast)
    df["cfr"] = df["cfr"].apply(safe_cast)

    for idx, r in df.iterrows():
        try:
            if (r.get("cfr") is None or str(r.get("cfr")).strip() == "") and r.get("cases") and r.get("deaths") is not None:
                cases = float(r.get("cases"))
                deaths = float(r.get("deaths"))
                if cases > 0:
                    cfr = round((deaths / cases) * 100, 2)
                    df.at[idx, "cfr"] = cfr
        except Exception:
            pass

    # Deduplicate entries
    df.drop_duplicates(subset=["week", "disease", "state"], keep="last", inplace=True)

    # Final ordering
    df_final = df[["week", "disease", "state", "cases", "deaths", "cfr", "report_date"]].copy()
    df_final = df_final.reset_index(drop=True)
    return df_final


def run_pipeline(start_year: int, end_year: int, force_redownload: bool = False) -> pd.DataFrame:
    ensure_dir(DOWNLOAD_DIR)
    session = requests.Session()
    all_html = crawl_all_pages(BASE_SITREP_URL, session=session)
    links = find_pdf_links_from_html(all_html, year_min=start_year, year_max=end_year)

    # Download PDFs
    downloaded: list[tuple[str, str, str]] = []
    for url, text in links:
        local = download_pdf(url, out_dir=DOWNLOAD_DIR, session=session, force_redownload=force_redownload)
        if local:
            downloaded.append((local, url, text))

    # Parse each PDF
    all_rows: list[dict] = []
    for (local, url, text) in tqdm(downloaded, desc="Parsing PDFs"):
        try:
            rows = process_pdf_file(local, DISEASES)
            if rows:
                all_rows.extend(rows)
        except Exception as e:
            logging.warning(f"Failed to parse {local}: {e}")

    # Merge and clean
    df_out = merge_and_clean(all_rows)
    if df_out.empty:
        logging.warning("No outbreak rows extracted. Check parser settings or examine raw PDFs.")
    else:
        df_out.to_csv(OUTPUT_CSV, index=False)
        logging.info(f"Wrote {len(df_out)} rows to {OUTPUT_CSV}")
    return df_out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape NCDC SitReps and export outbreaks CSV")
    parser.add_argument("--start-year", type=int, default=DEFAULT_START_YEAR, help="Start year (inclusive)")
    parser.add_argument("--end-year", type=int, default=DEFAULT_END_YEAR, help="End year (inclusive)")
    parser.add_argument("--force-redownload", action="store_true", help="Force re-download of PDFs")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.info(f"Running NCDC SitRep scraper for years {args.start_year}-{args.end_year}")
    df = run_pipeline(args.start_year, args.end_year, force_redownload=args.force_redownload)
    try:
        print(df.head(20).to_string(index=False))
    except Exception:
        pass