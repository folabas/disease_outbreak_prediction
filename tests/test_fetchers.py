import pandas as pd

from live_data.standardize import save_csv, read_csv
from live_data.build_features import build_latest_features


def test_standardize_save_and_read():
    df = pd.DataFrame({"time": ["2025-01-01"], "temperature_2m_mean": [25.0], "precipitation_sum": [5.0], "relative_humidity_2m_mean": [70.0]})
    path = save_csv(df, "weather_daily")
    assert path.exists()
    out = read_csv("weather_daily")
    assert out is not None
    assert "temperature_2m_mean" in out.columns


def test_build_latest_features():
    features = build_latest_features()
    assert not features.empty
    # Must include core keys and at least one feature
    assert set(["disease", "state", "year", "week"]).issubset(features.columns)
    assert "temperature_2m_mean" in features.columns