from pathlib import Path
import pandas as pd

from live_data.pipeline import run


def test_e2e_pipeline_realtime():
    out = run(mode="realtime")
    assert out.exists()
    df = pd.read_csv(out)
    assert set(["disease", "state", "year", "week"]).issubset(df.columns)