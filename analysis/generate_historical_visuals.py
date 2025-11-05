from pathlib import Path
import sys
import pandas as pd

# Ensure project root for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from ml.config import REPORTS_DIR, MODELS_DIR
from visualizations.historical import (
    regression_r2_bar,
    regression_error_bar,
    classifier_metrics_bar,
    metrics_heatmap,
    sample_counts_pie,
)
from visualizations.plots import tree_visualization


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def main():
    reg_weekly = _read_csv(REPORTS_DIR / "production" / "metrics_regression.csv")
    if not reg_weekly.empty and "model_type" not in reg_weekly.columns:
        reg_weekly["model_type"] = "regressor_weekly_state"
    reg_weekly_from_annual = _read_csv(REPORTS_DIR / "production" / "metrics_regression_weekly_from_annual.csv")
    if not reg_weekly_from_annual.empty and "model_type" not in reg_weekly_from_annual.columns:
        reg_weekly_from_annual["model_type"] = "regressor_weekly_from_annual"
    alert_cls = _read_csv(REPORTS_DIR / "production" / "metrics_alert_classification.csv")

    # Combine regression metrics
    reg_all = pd.DataFrame()
    if not reg_weekly.empty:
        reg_all = pd.concat([reg_all, reg_weekly], ignore_index=True)
    if not reg_weekly_from_annual.empty:
        reg_all = pd.concat([reg_all, reg_weekly_from_annual], ignore_index=True)

    # Ensure split output directory for historical visuals
    hist_dir = REPORTS_DIR / "production" / "visualizations" / "historical"
    hist_dir.mkdir(parents=True, exist_ok=True)

    # Historical visualizations
    if not reg_all.empty:
        regression_r2_bar(reg_all, filename="historical/historical_regression_r2_bar.png")
        regression_error_bar(reg_all, metric="rmse", filename="historical/historical_regression_error_bar.png")
        metrics_heatmap(reg_all, filename="historical/historical_metrics_heatmap.png")
        sample_counts_pie(reg_all, filename="historical/historical_sample_counts_pie.png")

    if not alert_cls.empty:
        classifier_metrics_bar(alert_cls, filename="historical/historical_classifier_metrics_bar.png")

    # Tree visualization from any available model
    for p in MODELS_DIR.glob("*.pkl"):
        if tree_visualization(p, filename="historical/historical_tree.png"):
            break

    print("✅ Generated historical visualizations in reports/production/visualizations/historical/")


if __name__ == "__main__":
    main()