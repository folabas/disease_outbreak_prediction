from pathlib import Path
from typing import Optional

import pandas as pd


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "reports" / "production" / "visualizations"


def _ensure_out_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def regression_r2_bar(metrics: pd.DataFrame, filename: str = "historical_regression_r2_bar.png") -> Optional[Path]:
    """Bar chart of R2 per disease grouped by model_type."""
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None
    _ensure_out_dir()
    if metrics.empty or "r2" not in metrics.columns:
        return None
    # Use disease as x-axis, color by model_type
    pivot = metrics.pivot_table(index="disease", columns="model_type", values="r2")
    pivot = pivot.sort_index()
    ax = pivot.plot(kind="bar", figsize=(10, 5))
    ax.set_ylabel("R2")
    ax.set_title("Historical Regression R2 by Disease and Model Type")
    out = OUTPUT_DIR / filename
    fig = ax.get_figure()
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def regression_error_bar(metrics: pd.DataFrame, metric: str = "rmse", filename: str = "historical_regression_error_bar.png") -> Optional[Path]:
    """Bar chart of error metric (RMSE/MAE) per disease grouped by model_type."""
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None
    _ensure_out_dir()
    if metrics.empty or metric not in metrics.columns:
        return None
    pivot = metrics.pivot_table(index="disease", columns="model_type", values=metric)
    pivot = pivot.sort_index()
    ax = pivot.plot(kind="bar", figsize=(10, 5))
    ax.set_ylabel(metric.upper())
    ax.set_title(f"Historical Regression {metric.upper()} by Disease and Model Type")
    out = OUTPUT_DIR / filename
    fig = ax.get_figure()
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def classifier_metrics_bar(alert_metrics: pd.DataFrame, filename: str = "historical_classifier_metrics_bar.png") -> Optional[Path]:
    """Bar chart of ROC AUC, PR AUC, F1 for each disease classifier (if available)."""
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None
    _ensure_out_dir()
    if alert_metrics.empty:
        return None
    cols = [c for c in ["roc_auc", "pr_auc", "f1"] if c in alert_metrics.columns]
    if not cols:
        return None
    # Melt metrics to long form: disease, metric, value
    df_long = alert_metrics.melt(id_vars=[c for c in alert_metrics.columns if c not in cols], value_vars=cols, var_name="metric", value_name="value")
    # Create bar chart grouped by disease with metric on color
    try:
        import seaborn as sns
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 5))
        sns.barplot(data=df_long, x="disease", y="value", hue="metric")
        plt.title("Historical Classifier Metrics by Disease")
        plt.ylabel("Score")
        plt.xticks(rotation=30, ha="right")
        out = OUTPUT_DIR / filename
        plt.tight_layout()
        plt.savefig(out)
        plt.close()
        return out
    except Exception:
        # Fallback without seaborn
        pivot = df_long.pivot_table(index="disease", columns="metric", values="value")
        ax = pivot.plot(kind="bar", figsize=(10, 5))
        ax.set_ylabel("Score")
        ax.set_title("Historical Classifier Metrics by Disease")
        out = OUTPUT_DIR / filename
        fig = ax.get_figure()
        fig.tight_layout()
        fig.savefig(out)
        plt.close(fig)
        return out


def metrics_heatmap(metrics: pd.DataFrame, filename: str = "historical_metrics_heatmap.png") -> Optional[Path]:
    """Heatmap of correlations among numeric historical metrics."""
    try:
        import seaborn as sns
        import matplotlib.pyplot as plt
    except Exception:
        return None
    _ensure_out_dir()
    num = metrics.select_dtypes(include="number")
    if num.empty:
        return None
    corr = num.corr()
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, cmap="coolwarm", annot=False)
    plt.title("Correlation Heatmap (Historical Metrics)")
    out = OUTPUT_DIR / filename
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out


def sample_counts_pie(metrics: pd.DataFrame, filename: str = "historical_sample_counts_pie.png") -> Optional[Path]:
    """Pie chart of total test sample counts by disease from historical metrics."""
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None
    _ensure_out_dir()
    if "n_test" not in metrics.columns:
        return None
    totals = metrics.groupby("disease")["n_test"].sum().fillna(0)
    labels = totals.index.tolist()
    values = totals.values.tolist()
    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct="%1.1f%%")
    plt.title("Test Sample Distribution by Disease")
    out = OUTPUT_DIR / filename
    plt.savefig(out)
    plt.close()
    return out