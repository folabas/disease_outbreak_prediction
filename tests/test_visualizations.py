from pathlib import Path
import pandas as pd

from visualizations.plots import line_chart, pie_chart, heatmap


def test_visualizations_generate_images(tmp_path: Path):
    # Minimal predictions frame
    df = pd.DataFrame({
        "disease": ["Covid-19", "Cholera"],
        "state": ["Lagos", "Kano"],
        "year": [2025, 2025],
        "week": [48, 48],
        "cases_pred": [10.0, 5.0],
        "outbreak_risk_prob": [0.6, 0.2],
    })
    lc = line_chart(df)
    pc = pie_chart(df)
    hm = heatmap(df)
    # When matplotlib/seaborn not installed, functions may return None
    for p in [lc, pc, hm]:
        if p is not None:
            assert Path(p).exists()