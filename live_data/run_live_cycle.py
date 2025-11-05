import argparse

from .fetchers.weather_openmeteo import fetch_latest_week
from .fetchers.who_api import fetch_who_disease_timeseries, fetch_who_covid_timeseries
from .fetchers.worldbank_api import fetch_worldbank_population
from .fetchers.ncdc_api import fetch_ncdc_outbreaks
from .pipeline import run


def main():
    parser = argparse.ArgumentParser(description="Run live ingestion → prediction cycle")
    parser.add_argument("--mode", choices=["cached", "realtime"], default="realtime", help="Use cached best-by-disease or run realtime models")
    parser.add_argument("--lat", type=float, default=6.5244, help="Latitude for weather fetch (default Lagos)")
    parser.add_argument("--lon", type=float, default=3.3792, help="Longitude for weather fetch (default Lagos)")
    args = parser.parse_args()

    # 1) Fetch latest sources (errors ignored, pipeline continues)
    try:
        fetch_latest_week(args.lat, args.lon)
    except Exception:
        pass
    try:
        fetch_who_disease_timeseries()
        fetch_who_covid_timeseries()
    except Exception:
        pass
    try:
        fetch_worldbank_population()
    except Exception:
        pass
    try:
        fetch_ncdc_outbreaks()
    except Exception:
        pass

    # 2) Run pipeline
    out_path = run(mode=args.mode)
    print(f"✅ Saved live predictions → {out_path}")


if __name__ == "__main__":
    main()