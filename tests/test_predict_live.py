import pandas as pd

from ml.config import FEATURE_COLUMNS
from ml.predict_live import predict_live


def test_predict_live_basic():
    # Minimal synthetic feature row
    row = {c: 0.0 for c in FEATURE_COLUMNS}
    row.update({"disease": "Covid-19", "state": "Lagos", "year": 2025, "week": 48})
    df = pd.DataFrame([row])

    preds = predict_live(df)
    assert set(["disease", "state", "year", "week", "cases_pred", "outbreak_risk_prob"]).issubset(preds.columns)
    assert len(preds) == 1