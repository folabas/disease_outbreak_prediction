from __future__ import annotations

# Canonical master feature list (aligned with the dataset and existing model)
FEATURES = [
    # Epidemiological
    "cases",
    "deaths",
    "cases_last_week",
    "cases_2w_avg",
    "cases_growth_rate",
    "cases_mean_4w",
    "cases_std_4w",
    "cases_per_100k",
    "deaths_last_week",
    "deaths_mean_4w",

    # Climate
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "precipitation_sum",

    # WASH (available fields only)
    "access_to_clean_water_percent",
    "water_contamination_index",

    # Vector ecology
    "mosquito_density_index",
    "breeding_sites_count",

    # Health system
    "hospital_beds",
    "icu_beds",
    "staff_count",
    "antimalarial_stock_level",
    "ppe_availability_score",

    # Demographics / mobility
    "population",
    "population_density",
    "growth_rate_percent",
    "urban_percent",
    "market_density",
    "mobility_index",

    # National signals
    "who_cases_national",

    # Disease one-hot (ensure preprocessing creates these columns)
    "disease_cholera",
    "disease_malaria",
    "disease_ebola",
    "disease_covid",
]

TARGET = "cases"
DISEASE_COLUMNS = [c for c in FEATURES if c.startswith("disease_")]
NON_DISEASE_FEATURES = [c for c in FEATURES if c not in DISEASE_COLUMNS]
