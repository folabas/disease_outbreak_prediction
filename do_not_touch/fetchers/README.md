Fetchers

This directory contains standalone scripts that fetch external datasets and save them into the `data/` folder.

- `fetch_who_data.py`: Queries WHO GHO indicators for selected diseases and writes CSV.
- `fetch_worldbank_data.py`: Retrieves World Bank population and urban percentage for Nigeria.
- `fetch_openmeteo_data.py`: Pulls historical weather metrics from Open-Meteo.

Run these scripts from the project root to ensure relative paths to `data/` resolve correctly.