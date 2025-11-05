from pathlib import Path


# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "outbreakiq_training_data_filled.csv"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"


# Modeling
FORECAST_HORIZON_WEEKS = 1  # one-week ahead forecasting

# Alert labeling strategy: 'static' or 'quantile'
ALERT_LABEL_STRATEGY = "static"
STATIC_OUTBREAK_THRESHOLD_PER_100K = 5.0  # threshold for cases_per_100k next week
QUANTILE_THRESHOLD = 0.8  # 80th percentile per disease-state


# Seed for reproducibility
RANDOM_STATE = 42


# Nigeria states list for cleaning (ensure realistic state names only)
NIGERIA_STATES = {
    "Abia","Adamawa","Akwa Ibom","Anambra","Bauchi","Bayelsa","Benue","Borno",
    "Cross River","Delta","Ebonyi","Edo","Ekiti","Enugu","Gombe","Imo","Jigawa",
    "Kaduna","Kano","Katsina","Kebbi","Kogi","Kwara","Lagos","Nasarawa","Niger",
    "Ogun","Ondo","Osun","Oyo","Plateau","Rivers","Sokoto","Taraba","Yobe","Zamfara",
    "Abuja"
}


# Feature columns used by models
FEATURE_COLUMNS = [
    "temperature_2m_mean",
    "precipitation_sum",
    "relative_humidity_2m_mean",
    "who_country_cases",
    "population",
    "urban_percent",
    "cases_last_week",
    "deaths_last_week",
    "cases_per_100k",
    "rainfall_change",
    "temp_anomaly",
    "week_sin",
    "week_cos",
    "year",
]


# Target column for regression
TARGET_COLUMN = "cases"