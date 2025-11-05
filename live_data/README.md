# Live Data Ingestion

This module provides automated, modular data collection for real-time prediction.

Contents:
- `fetchers/` – Source-specific fetchers (Open-Meteo, WHO, World Bank, NCDC).
- `standardize.py` – Helpers to standardize and save outputs under `data/live/`.
- `build_features.py` – Combines latest source data into model feature rows.
- `pipeline.py` – Supports cached vs realtime prediction modes.
- `run_live_cycle.py` – CLI to run a full live ingestion → prediction cycle.

Outputs:
- Standardized source files saved to `data/live/*.csv`.
- Live feature table saved to `data/live/latest_features.csv`.
- Live predictions saved to `reports/production/predictions_live.csv`.

Usage:
```bash
python -m live_data.run_live_cycle --mode realtime
# or
python -m live_data.run_live_cycle --mode cached
```

Notes:
- External scheduling (Task Scheduler/cron) should call `run_live_cycle.py` periodically.
- Fetchers have basic error handling; failures are logged and skipped without stopping the pipeline.

## Data Contracts

Schemas (selected):
- `data/live/weather_daily.csv`: `date` (YYYY-MM-DD), `state` (str), `temperature_2m_mean` (float), `relative_humidity_2m_mean` (float), `precipitation_sum` (float)
- `data/live/who_disease.csv`: `country` (str, =NGA), `disease` (str), `year` (int), `cases` (int)
- `data/live/worldbank_population.csv`: `country` (str, =NGA), `year` (int), `population` (int), `urban_percent` (float)
- `data/live/ncdc_outbreaks.csv`: `date` (YYYY-MM-DD), `state` (str), `disease` (str), `cases` (int), `deaths` (int)

Dedupe keys:
- Weather: `date + state`
- NCDC outbreaks: `date + state + disease`
- WHO annual: `year + disease + country`
- Latest features: `week_start + state + disease`

Update frequency:
- Weather: daily
- WHO: weekly/when published
- World Bank: annual snapshots
- NCDC: weekly scraping cadence

Primary output:
- `data/live/latest_features.csv` – canonical feature table used by `ml/predict_live.py`.

## Operational Notes
- Use `live_data/standardize.py` for canonical column names/types.
- Use `ml/drift.py` to compare live features against training distribution and flag drift.