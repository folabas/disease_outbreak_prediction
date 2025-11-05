from pathlib import Path
import sys
import pandas as pd

# Ensure project root is on path when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from visualizations.plots import line_chart, pie_chart, heatmap, tree_visualization, pred_vs_actual_line
from ml.config import REPORTS_DIR, MODELS_DIR


def main():
    preds_path = REPORTS_DIR / "production" / "predictions_live.csv"
    if not preds_path.exists():
        print(f"[WARN] predictions_live.csv not found at {preds_path}")
        return
    # Ensure split output directory for live visuals
    live_dir = REPORTS_DIR / "production" / "visualizations" / "live"
    live_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(preds_path)
    # Save into live/ subfolder
    line_chart(df, filename="live/cases_line.png")
    pie_chart(df, filename="live/risk_pie.png")
    heatmap(df, filename="live/features_heatmap.png")
    # Predicted vs Actual (from latest_features)
    features_path = REPORTS_DIR.parents[0] / "data" / "live" / "latest_features.csv"
    if features_path.exists():
        try:
            feats = pd.read_csv(features_path)
            pred_vs_actual_line(df, feats, filename="live/actual_vs_predicted.png")
        except Exception as e:
            print(f"[WARN] Unable to generate predicted-vs-actual chart: {e}")
    else:
        print(f"[WARN] latest_features.csv not found at {features_path}, skipping predicted-vs-actual chart")
    # Try to visualize first available model tree
    for p in MODELS_DIR.glob("*.pkl"):
        if tree_visualization(p, filename="live/tree.png"):
            break
    print("✅ Generated live visualizations in reports/production/visualizations/live/")


if __name__ == "__main__":
    main()