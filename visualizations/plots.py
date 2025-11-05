from pathlib import Path
from typing import Optional

import pandas as pd


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "reports" / "production" / "visualizations"


def _ensure_out_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def line_chart(preds: pd.DataFrame, filename: str = "cases_line.png") -> Optional[Path]:
    """Generate a simple line chart of predicted cases by disease/week.

    Returns the path to the saved file, or None if matplotlib is unavailable.
    """
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None
    _ensure_out_dir()
    plt.figure(figsize=(10, 5))
    for dis, g in preds.groupby("disease"):
        g_sorted = g.sort_values(["year", "week"])
        plt.plot(range(len(g_sorted)), g_sorted["cases_pred"], label=dis)
    plt.legend()
    plt.title("Predicted Weekly Cases")
    plt.xlabel("Time Index")
    plt.ylabel("Cases (pred)")
    out = OUTPUT_DIR / filename
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out


def pie_chart(preds: pd.DataFrame, filename: str = "risk_pie.png") -> Optional[Path]:
    """Generate a pie chart of mean outbreak risk probability by disease."""
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None
    _ensure_out_dir()
    means = preds.groupby("disease")["outbreak_risk_prob"].mean().fillna(0.0)
    labels = means.index.tolist()
    values = means.values.tolist()
    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct="%1.1f%%")
    plt.title("Mean Outbreak Risk by Disease")
    out = OUTPUT_DIR / filename
    plt.savefig(out)
    plt.close()
    return out


def heatmap(preds: pd.DataFrame, filename: str = "features_heatmap.png") -> Optional[Path]:
    """Generate a heatmap of correlations among numeric columns in predictions."""
    try:
        import seaborn as sns
        import matplotlib.pyplot as plt
    except Exception:
        return None
    _ensure_out_dir()
    num = preds.select_dtypes(include="number")
    corr = num.corr()
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, cmap="coolwarm", annot=False)
    plt.title("Correlation Heatmap (Predictions)")
    out = OUTPUT_DIR / filename
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out


def tree_visualization(model_path: Path, filename: str = "tree.png") -> Optional[Path]:
    """Visualize a single tree from a scikit-learn RandomForest model, if possible.

    Falls back to a message when dependencies are unavailable.
    """
    try:
        from joblib import load
        from sklearn.tree import plot_tree
        import matplotlib.pyplot as plt
    except Exception:
        return None


def pred_vs_actual_line(
    preds: pd.DataFrame,
    features: pd.DataFrame,
    filename: str = "live/actual_vs_predicted.png",
) -> Optional[Path]:
    """Plot aggregate predicted vs live actual (cases_last_week) over time per disease.

    - Merges predictions with latest_features on (disease, state, year, week).
    - Aggregates by (disease, year, week) summing predicted cases and actual last-week cases.
    - Produces a line chart with two series per disease: Predicted vs Actual.

    Returns saved path or None if plotting libraries are unavailable or inputs invalid.
    """
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None

    _ensure_out_dir()

    # Basic column checks
    req_pred_cols = {"disease", "state", "year", "week", "cases_pred"}
    req_feat_cols = {"disease", "state", "year", "week", "cases_last_week"}
    if not req_pred_cols.issubset(set(preds.columns)):
        return None
    if not req_feat_cols.issubset(set(features.columns)):
        return None

    # Some live predictions may have year==0; allow merge on disease/state/week and prefer matching year
    merge_keys = ["disease", "state", "year", "week"]
    merged = preds.merge(features[merge_keys + ["cases_last_week"]], on=merge_keys, how="left")

    # If many rows have missing actuals due to year mismatch, try relaxed merge on (disease,state,week)
    if merged["cases_last_week"].isna().mean() > 0.5:
        relaxed = preds.merge(
            features[["disease", "state", "week", "cases_last_week"]],
            on=["disease", "state", "week"],
            how="left",
            suffixes=("", "_relaxed"),
        )
        merged["cases_last_week"] = merged["cases_last_week"].fillna(relaxed["cases_last_week"])

    # Horizon fix: align actuals to the forecast week by shifting last-week counts forward
    merged = merged.sort_values(["disease", "state", "year", "week"]).copy()
    merged["actual_shifted"] = merged.groupby(["disease", "state"])['cases_last_week'].shift(-1)
    merged = merged.dropna(subset=["actual_shifted"]).copy()

    # Aggregate per disease-week across states after alignment
    agg = (
        merged.groupby(["disease", "year", "week"])[["cases_pred", "actual_shifted"]]
        .sum()
        .reset_index()
        .sort_values(["disease", "year", "week"])  # ensure proper ordering
    )

    if agg.empty:
        return None

    # Plot: two lines per disease
    plt.figure(figsize=(12, 6))
    diseases = agg["disease"].unique().tolist()
    for dis in diseases:
        g = agg[agg["disease"] == dis].copy()
        # Create calendar labels and corresponding index per disease
        g["year_week"] = g["year"].astype(int).astype(str) + "-W" + g["week"].astype(int).astype(str)
        g["t"] = range(len(g))
        plt.plot(g["t"], g["cases_pred"], label=f"{dis} – Predicted")
        plt.plot(g["t"], g["actual_shifted"], label=f"{dis} – Actual (aligned)")
        # Improve readability: use year-week labels on x-axis
        plt.xticks(g["t"], g["year_week"], rotation=30, ha="right")

    plt.legend(ncol=2)
    plt.title("Predicted vs Live Actuals (Aggregated by Week)")
    plt.xlabel("Calendar Week (per disease)")
    plt.ylabel("Cases")
    # Quick metrics box for displayed window across all diseases
    try:
        y_true = agg["actual_shifted"].values
        y_pred = agg["cases_pred"].values
        mae = float(pd.Series(y_pred - y_true).abs().mean())
        denom = float(pd.Series(y_true - pd.Series(y_true).mean()).pow(2).sum())
        r2 = float(1.0 - (pd.Series(y_pred - y_true).pow(2).sum() / denom)) if denom > 0 else float("nan")
        text = f"MAE: {mae:.1f}\nR²: {r2:.2f}"
        plt.gcf().text(0.02, 0.85, text, bbox=dict(facecolor='white', alpha=0.7), fontsize=9)
    except Exception:
        pass

    out = OUTPUT_DIR / filename
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out
    _ensure_out_dir()
    try:
        model = load(model_path)
        estimator = getattr(model, "estimators_", None)
        if estimator and len(estimator) > 0:
            tree = estimator[0]
            plt.figure(figsize=(12, 8))
            plot_tree(tree, filled=True, max_depth=3, fontsize=8)
            out = OUTPUT_DIR / filename
            plt.tight_layout()
            plt.savefig(out)
            plt.close()
            return out
        return None
    except Exception:
        return None