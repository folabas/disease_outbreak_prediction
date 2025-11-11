#!/usr/bin/env python3
"""
rebuild_dataset.py

Builds backfilled weekly data assets for OutbreakIQ:

- data/raw/ncdc_outbreaks_clean.csv  (read from existing file if present)
- data/raw/who_disease_data.csv      (WHO GHO indicators with 'case' in name, Nigeria)
- data/raw/who_disease_data_weekly.csv (WHO disaggregated to weekly)
- data/raw/worldbank_population.csv  (World Bank SP.POP.TOTL)
- data/raw/worldbank_urban_percent.csv  (World Bank SP.URB.TOTL.IN.ZS)
- data/raw/worldbank_population_weekly.csv (broadcast per week)
- data/live/weather_weekly_by_state.csv  (Open-Meteo ERA5 weekly aggregates)

Note: This script does not build the final merged training table.
Run your feature builder afterwards (e.g., `python -m ml.build_features`).
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

import requests
import pandas as pd


# ---------- Paths ----------
ROOT = Path(__file__).resolve().parents[0]
DATA_DIR = ROOT / "data"
LIVE_DIR = DATA_DIR / "live"
RAW_DIR = DATA_DIR / "raw"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(LIVE_DIR, exist_ok=True)


# ---------- Config ----------
# Nigeria state centroids (state -> (lat, lon))
STATE_CENTROIDS: Dict[str, Tuple[float, float]] = {
    "Abia": (5.5320, 7.4868),
    "Adamawa": (9.3300, 12.3984),
    "Akwa Ibom": (4.9586, 7.9480),
    "Anambra": (6.2000, 6.7833),
    "Bauchi": (10.3100, 9.8440),
    "Bayelsa": (4.6266, 6.1973),
    "Benue": (7.3366, 8.5229),
    "Borno": (11.8333, 13.1500),
    "Cross River": (5.9544, 8.3264),
    "Delta": (5.5000, 6.1667),
    "Ebonyi": (6.2643, 8.1250),
    "Edo": (6.3100, 5.6100),
    "Ekiti": (7.6232, 5.2209),
    "Enugu": (6.4500, 7.5000),
    "Gombe": (10.2800, 11.1700),
    "Imo": (5.4865, 7.0258),
    "Jigawa": (12.1500, 9.5000),
    "Kaduna": (10.5105, 7.4165),
    "Kano": (12.0000, 8.5167),
    "Katsina": (12.9900, 7.6000),
    "Kebbi": (12.4500, 4.2000),
    "Kogi": (7.8000, 6.7333),
    "Kwara": (8.5400, 4.5500),
    "Lagos": (6.5244, 3.3792),
    "Nasarawa": (8.5000, 8.5167),
    "Niger": (9.6000, 6.5500),
    "Ogun": (7.1550, 3.3450),
    "Ondo": (7.2500, 5.2000),
    "Osun": (7.7820, 4.5417),
    "Oyo": (7.8500, 3.9333),
    "Plateau": (9.0000, 8.8889),
    "Rivers": (4.7794, 7.0456),
    "Sokoto": (13.0600, 5.2410),
    "Taraba": (8.8900, 11.1200),
    "Yobe": (12.5400, 11.7500),
    "Zamfara": (12.1200, 6.2425),
    "Abuja": (9.0765, 7.3986),
}

START_DATE = "2018-01-01"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")


# ---------- Utilities ----------
def save_csv(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"[SAVED] {path}  rows={len(df)}")
    return path


LOG_FILE = DATA_DIR / "data_fetch_log.txt"


def log(msg: str) -> None:
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{timestamp}] {msg}\n"
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    print(msg)


def get_json(url: str, params: Optional[dict] = None, timeout: int = 30, retries: int = 3, backoff: float = 1.5):
    attempt = 0
    while True:
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            attempt += 1
            log(f"[HTTP] error on {url}: {e} (attempt {attempt}/{retries})")
            if attempt >= retries:
                return None
            time.sleep(backoff ** attempt)


# ---------- NCDC ----------
def load_ncdc_local(path: Optional[Path] = None) -> Optional[pd.DataFrame]:
    files = [path] if path else [
        ROOT / "data" / "ncdc_outbreaks_clean.csv",
        ROOT / "data" / "ncdc_outbreaks.csv",
        RAW_DIR / "ncdc_outbreaks_clean.csv",
    ]
    for p in files:
        if p and p.exists():
            try:
                df = pd.read_csv(p)
                log(f"[NCDC] found local CSV: {p} rows={len(df)}")
                return df
            except Exception as e:
                log(f"[NCDC] failed to read {p}: {e}")
    log("[NCDC] No local NCDC CSV found; proceeding without it.")
    return None


# ---------- WHO (GHO) ----------
def fetch_who_indicators() -> List[dict]:
    url = "https://ghoapi.azureedge.net/api/Indicator?$format=json"
    log("[WHO] fetching indicators list ...")
    data = get_json(url, timeout=30)
    if not data:
        log("[WHO] failed to fetch indicators")
        return []
    items = data.get("value", [])
    log(f"[WHO] indicators fetched: {len(items)}")
    return items


def filter_case_indicators(indicators: List[dict]) -> List[dict]:
    out = []
    for it in indicators:
        name = str(it.get("IndicatorName") or "").lower()
        if "case" in name or "cases" in name:
            out.append(it)
    log(f"[WHO] filtered case-like indicators: {len(out)}")
    return out


def fetch_who_indicator_for_nigeria(indicator_code: str) -> pd.DataFrame:
    url = f"https://ghoapi.azureedge.net/api/{indicator_code}?$filter=SpatialDim eq 'NGA'&$format=json"
    data = get_json(url, timeout=30)
    rows: List[dict] = []
    if not data:
        log(f"[WHO] failed to fetch {indicator_code}")
        return pd.DataFrame(columns=["indicator", "year", "value"])
    for rec in data.get("value", []):
        year = rec.get("TimePeriod") or rec.get("TimeDim") or rec.get("Year") or rec.get("Time")
        val = rec.get("NumericValue") or rec.get("Value") or rec.get("Total")
        try:
            year_int = int(year)
            val_f = float(val)
        except Exception:
            continue
        rows.append({"indicator": indicator_code, "year": year_int, "value": val_f})
    return pd.DataFrame(rows)


def build_who_cases_csv(output_path: Path) -> Path:
    indicators = fetch_who_indicators()
    if not indicators:
        log("[WHO] no indicators; abort WHO fetch.")
        return output_path
    cases_inds = filter_case_indicators(indicators)
    rows: List[dict] = []
    for ind in cases_inds:
        code = ind.get("IndicatorCode") or ind.get("IndicatorId") or ind.get("Indicator")
        if not code:
            continue
        df = fetch_who_indicator_for_nigeria(code)
        if df.empty:
            continue
        name = ind.get("IndicatorName") or code
        for _, r in df.iterrows():
            rows.append({"disease_label": name, "indicator_code": code, "year": int(r["year"]), "cases": float(r["value"])})
        time.sleep(0.2)
    if not rows:
        log("[WHO] no case indicator data collected.")
        return output_path
    df_out = pd.DataFrame(rows)
    save_csv(df_out, output_path)
    return output_path


def disaggregate_who_to_weekly(annual_csv: Path, weekly_csv: Path) -> Optional[Path]:
    if not annual_csv.exists():
        log(f"[WHO] annual CSV not found: {annual_csv}")
        return None
    df = pd.read_csv(annual_csv)
    if df.empty:
        log("[WHO] annual CSV is empty; skipping weekly disaggregation")
        return None
    rows: List[dict] = []
    for _, r in df.iterrows():
        year = int(r["year"])
        total_cases = float(r["cases"]) if pd.notnull(r["cases"]) else 0.0
        per_week = total_cases / 52.0
        for w in range(1, 53):
            rows.append({
                "disease_label": r["disease_label"],
                "indicator_code": r["indicator_code"],
                "year": year,
                "week": w,
                "cases": per_week,
            })
    dfw = pd.DataFrame(rows)
    save_csv(dfw, weekly_csv)
    return weekly_csv


# ---------- World Bank ----------
def fetch_worldbank_indicator(indicator: str) -> pd.DataFrame:
    url = f"https://api.worldbank.org/v2/country/NGA/indicator/{indicator}?format=json&per_page=1000"
    log(f"[WB] fetching {indicator} ...")
    data = get_json(url, timeout=30)
    if not data or not isinstance(data, list) or len(data) < 2:
        return pd.DataFrame()
    items = data[1]
    rows: List[dict] = []
    for it in items:
        year = it.get("date")
        val = it.get("value")
        try:
            y = int(year)
        except Exception:
            continue
        if val is None:
            continue
        try:
            v = float(val)
        except Exception:
            continue
        rows.append({"year": y, "value": v})
    return pd.DataFrame(rows)


def build_worldbank_csv(pop_path: Path, urb_path: Path) -> Tuple[Path, Path]:
    pop_df = fetch_worldbank_indicator("SP.POP.TOTL")
    urb_df = fetch_worldbank_indicator("SP.URB.TOTL.IN.ZS")
    if pop_df.empty:
        log("[WB] No population data fetched.")
    else:
        save_csv(pop_df.rename(columns={"value": "population"}), pop_path)
    if urb_df.empty:
        log("[WB] No urban percent data fetched.")
    else:
        save_csv(urb_df.rename(columns={"value": "urban_percent"}), urb_path)
    return pop_path, urb_path


def broadcast_population_to_weeks(pop_csv: Path, out_csv: Path, start_year: int = 2018, end_year: Optional[int] = None):
    if not pop_csv.exists():
        log(f"[POP] population CSV not found: {pop_csv}")
        return None
    df = pd.read_csv(pop_csv)
    if df.empty:
        return None
    if end_year is None:
        end_year = datetime.utcnow().year
    rows: List[dict] = []
    for _, r in df.iterrows():
        y = int(r["year"])
        if y < start_year or y > end_year:
            continue
        pop = float(r["population"]) if pd.notnull(r["population"]) else 0.0
        for w in range(1, 53):
            rows.append({"year": y, "week": w, "population": pop})
    out = pd.DataFrame(rows)
    save_csv(out, out_csv)
    return out_csv


# ---------- Weather (Open-Meteo ERA5 archive) ----------
def fetch_open_meteo_daily(lat: float, lon: float, start_date: str, end_date: str) -> pd.DataFrame:
    base = "https://archive-api.open-meteo.com/v1/era5"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(["temperature_2m_mean", "precipitation_sum", "relative_humidity_2m_mean"]),
        "timezone": "Africa/Lagos",
    }
    j = get_json(base, params=params, timeout=60)
    if not j:
        return pd.DataFrame()
    dates = j.get("daily", {}).get("time", [])
    if not dates:
        return pd.DataFrame()
    df = pd.DataFrame({"date": dates})
    for k, arr in j.get("daily", {}).items():
        if k == "time":
            continue
        df[k] = arr
    return df


def _save_state_weather(out_dir: Path, state: str, df: pd.DataFrame) -> Path:
    state_slug = state.replace(" ", "_")
    path = out_dir / f"weather_weekly_{state_slug}.csv"
    save_csv(df, path)
    return path


def build_weather_weekly_for_states_throttled(
    out_dir: Path,
    states: Dict[str, Tuple[float, float]],
    start_date: str,
    end_date: str,
    sleep_seconds: int = 10,
    max_retries: int = 3,
    batch_size: int = 4,
) -> Path:
    # Resume support: skip states already saved as per-state files
    existing = set()
    for p in out_dir.glob("weather_weekly_*.csv"):
        name = p.stem.replace("weather_weekly_", "").replace("_", " ")
        existing.add(name)

    pending_states = [(s, coords) for s, coords in states.items() if s not in existing]
    log(f"[WEATHER] states pending: {len(pending_states)} / {len(states)}")

    batch: List[Tuple[str, Tuple[float, float]]] = []
    for state, (lat, lon) in pending_states:
        batch.append((state, (lat, lon)))
        # process when batch is full
        if len(batch) >= batch_size:
            _process_weather_batch(out_dir, batch, start_date, end_date, sleep_seconds, max_retries)
            batch = []
    # process remaining
    if batch:
        _process_weather_batch(out_dir, batch, start_date, end_date, sleep_seconds, max_retries)

    # Consolidate all per-state files (including any existing ones) into one CSV
    rows: List[pd.DataFrame] = []
    for p in out_dir.glob("weather_weekly_*.csv"):
        try:
            df = pd.read_csv(p)
            rows.append(df)
        except Exception as e:
            log(f"[WEATHER] failed to read {p}: {e}")
    if not rows:
        log("[WEATHER] no state weather data collected.")
        return out_dir / "weather_weekly_none.csv"
    df_out = pd.concat(rows, ignore_index=True)
    path = out_dir / "weather_weekly_by_state.csv"
    save_csv(df_out, path)
    return path


def _process_weather_batch(
    out_dir: Path,
    batch: List[Tuple[str, Tuple[float, float]]],
    start_date: str,
    end_date: str,
    sleep_seconds: int,
    max_retries: int,
) -> None:
    for state, (lat, lon) in batch:
        log(f"[WEATHER] fetching {state} ({lat},{lon}) ...")
        df = pd.DataFrame()
        for attempt in range(1, max_retries + 1):
            df = fetch_open_meteo_daily(lat, lon, start_date, end_date)
            if not df.empty:
                break
            log(f"[WEATHER] empty/failed for {state}, retry {attempt}/{max_retries}")
            time.sleep(sleep_seconds)
        if df.empty:
            log(f"[WEATHER] no data for {state} after {max_retries} retries")
            continue
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        iso = df["date"].dt.isocalendar()
        df["year"] = iso.year
        df["week"] = iso.week
        agg = df.groupby(["year", "week"], as_index=False).agg({
            "temperature_2m_mean": "mean",
            "relative_humidity_2m_mean": "mean",
            "precipitation_sum": "sum",
        })
        agg["state"] = state
        _save_state_weather(out_dir, state, agg)
        # throttle between states to avoid 429
        time.sleep(sleep_seconds)


# ---------- WHO mapping skeleton ----------
def write_who_mapping_skeleton(annual_csv: Path, out_csv: Path) -> Optional[Path]:
    if not annual_csv.exists():
        return None
    df = pd.read_csv(annual_csv)
    if df.empty:
        return None
    unique = df[["disease_label", "indicator_code"]].drop_duplicates().copy()
    unique["canonical_disease"] = ""
    save_csv(unique, out_csv)
    return out_csv


# ---------- Main ----------
def main():
    print("=== Rebuild dataset script (OutbreakIQ) ===")
    print("Ensure internet connectivity for WHO / WorldBank / Open-Meteo fetches.")

    # 1) NCDC: prefer local cleaned CSV
    ncdc_df = load_ncdc_local()
    if ncdc_df is not None:
        save_csv(ncdc_df, RAW_DIR / "ncdc_outbreaks_clean.csv")
    else:
        log("[INFO] No local NCDC file. You can add `data/ncdc_outbreaks_clean.csv` and re-run.")

    # 2) WHO: case-like indicators for Nigeria (annual)
    who_annual = RAW_DIR / "who_disease_data.csv"
    try:
        build_who_cases_csv(who_annual)
    except Exception as e:
        log(f"[WHO] Exception during WHO fetch: {e}")

    # 2b) WHO weekly disaggregation
    who_weekly = RAW_DIR / "who_disease_data_weekly.csv"
    try:
        disaggregate_who_to_weekly(who_annual, who_weekly)
    except Exception as e:
        log(f"[WHO] Exception during weekly disaggregation: {e}")

    # 2c) WHO mapping skeleton for manual normalization
    try:
        write_who_mapping_skeleton(who_annual, RAW_DIR / "who_indicator_mapping.csv")
    except Exception as e:
        log(f"[WHO] Exception writing mapping skeleton: {e}")

    # 3) World Bank
    pop_csv = RAW_DIR / "worldbank_population.csv"
    urb_csv = RAW_DIR / "worldbank_urban_percent.csv"
    try:
        build_worldbank_csv(pop_csv, urb_csv)
    except Exception as e:
        log(f"[WB] Exception during WB fetch: {e}")

    # Broadcast population to weekly grid for later joins
    try:
        broadcast_population_to_weeks(pop_csv, RAW_DIR / "worldbank_population_weekly.csv")
    except Exception as e:
        log(f"[POP] Exception during broadcast: {e}")

    # 4) Weather: throttled fetch for all states with resume support
    try:
        build_weather_weekly_for_states_throttled(
            LIVE_DIR,
            STATE_CENTROIDS,
            START_DATE,
            END_DATE,
            sleep_seconds=10,
            max_retries=3,
            batch_size=4,
        )
    except Exception as e:
        log(f"[WEATHER] Exception during weather fetch: {e}")

    # 5) Summary
    print("=== Finished fetching raw assets ===")
    print("Files saved under:")
    for p in [
        RAW_DIR / "ncdc_outbreaks_clean.csv",
        RAW_DIR / "who_disease_data.csv",
        RAW_DIR / "who_disease_data_weekly.csv",
        RAW_DIR / "who_indicator_mapping.csv",
        RAW_DIR / "worldbank_population.csv",
        RAW_DIR / "worldbank_urban_percent.csv",
        RAW_DIR / "worldbank_population_weekly.csv",
        LIVE_DIR / "weather_weekly_by_state.csv",
        LOG_FILE,
    ]:
        print(" -", p)
    print("")
    print("NEXT STEP: merge and build features (e.g., python -m ml.build_features)")


if __name__ == "__main__":
    main()