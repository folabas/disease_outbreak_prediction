"""
Exploratory analysis for outbreakiq_training_data.csv

Outputs:
- reports/missing_values.csv
- reports/correlation_matrix.csv
- reports/correlation_heatmap.png
- reports/weekly_trends/<disease>/<state>.png (per-state weekly trends)
- reports/weekly_trends/<disease>/_national.png (national weekly trends by disease)
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


DATA_DIR = Path("data")
REPORTS_DIR = Path("reports")


def ensure_dirs():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "weekly_trends").mkdir(parents=True, exist_ok=True)


def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "outbreakiq_training_data.csv")
    # Parse dates when present
    if "report_date" in df.columns:
        df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
    return df


def summarize_missing(df: pd.DataFrame) -> pd.Series:
    missing = df.isna().sum().sort_values(ascending=False)
    missing.to_csv(REPORTS_DIR / "missing_values.csv", header=["missing_count"])
    print("Missing values (top 20):\n", missing.head(20))
    return missing


def correlations(df: pd.DataFrame) -> pd.DataFrame:
    # Select relevant numeric columns for weather x cases
    cols = [
        "cases",
        "cases_per_100k",
        "temperature_2m_mean",
        "precipitation_sum",
        "relative_humidity_2m_mean",
        "rainfall_change",
        "temp_anomaly",
    ]
    cols = [c for c in cols if c in df.columns]
    corr = df[cols].corr(method="pearson")
    corr.to_csv(REPORTS_DIR / "correlation_matrix.csv")
    print("Correlation matrix between weather & cases:\n", corr)
    return corr


def plot_correlation_heatmap(corr: pd.DataFrame, out_path: Path):
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(corr.index)))
    ax.set_yticklabels(corr.index)
    # Annotate cells
    for i in range(corr.shape[0]):
        for j in range(corr.shape[1]):
            val = corr.values[i, j]
            ax.text(j, i, f"{val:.2f}", va="center", ha="center", fontsize=8, color="black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Pearson r")
    ax.set_title("Correlation: Weather vs Cases")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def week_key(df: pd.DataFrame) -> pd.Series:
    # Numeric key for plotting consistent time order: YYYY*100 + WW
    y = pd.to_numeric(df["year"], errors="coerce")
    w = pd.to_numeric(df["week"], errors="coerce")
    return y.astype(int) * 100 + w.astype(int)


def plot_weekly_trends(df: pd.DataFrame):
    diseases = df["disease"].dropna().unique().tolist()
    for disease in diseases:
        disease_dir = REPORTS_DIR / "weekly_trends" / disease
        disease_dir.mkdir(parents=True, exist_ok=True)
        ddf = df[df["disease"] == disease].copy()
        # Coerce and drop missing year/week
        ddf["year"] = pd.to_numeric(ddf["year"], errors="coerce")
        ddf["week"] = pd.to_numeric(ddf["week"], errors="coerce")
        ddf["cases"] = pd.to_numeric(ddf["cases"], errors="coerce")
        ddf = ddf.dropna(subset=["year", "week"])  # essential for plotting
        ddf["year"] = ddf["year"].astype(int)
        ddf["week"] = ddf["week"].astype(int)
        # National aggregation (sum over states)
        nat = (
            ddf.groupby(["year", "week"], as_index=False)["cases"].sum().sort_values(["year", "week"])
        )
        fig, ax = plt.subplots(figsize=(10, 4))
        x = nat["year"].astype(int) * 100 + nat["week"].astype(int)
        ax.plot(x, nat["cases"], label="National cases", color="#1f77b4")
        ax.set_title(f"Weekly trends — {disease} (National)")
        ax.set_xlabel("YearWeek")
        ax.set_ylabel("Cases")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(disease_dir / "_national.png", dpi=150)
        plt.close(fig)

        # Per-state plots
        states = ddf["state"].dropna().unique().tolist()
        for state in states:
            sdf = ddf[ddf["state"] == state].sort_values(["year", "week"]).copy()
            if len(sdf) < 4:
                continue  # skip very sparse series
            fig, ax = plt.subplots(figsize=(10, 4))
            x = week_key(sdf)
            ax.plot(x, sdf["cases"], label="Cases", color="#2ca02c")
            if "cases_per_100k" in sdf.columns:
                ax2 = ax.twinx()
                ax2.plot(x, sdf["cases_per_100k"], label="Cases per 100k", color="#d62728", alpha=0.7)
                ax2.set_ylabel("Cases per 100k")
            ax.set_title(f"Weekly trends — {disease} — {state}")
            ax.set_xlabel("YearWeek")
            ax.set_ylabel("Cases")
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            fig.savefig(disease_dir / f"{state}.png", dpi=150)
            plt.close(fig)


def main():
    ensure_dirs()
    df = load_dataset()

    print("\n=== Checking missing values ===")
    summarize_missing(df)

    print("\n=== Computing correlations ===")
    corr = correlations(df)
    plot_correlation_heatmap(corr, REPORTS_DIR / "correlation_heatmap.png")
    print(f"Saved correlation heatmap → {REPORTS_DIR / 'correlation_heatmap.png'}")

    print("\n=== Plotting weekly trends ===")
    plot_weekly_trends(df)
    print(f"Saved weekly trends → {REPORTS_DIR / 'weekly_trends'}")


if __name__ == "__main__":
    main()