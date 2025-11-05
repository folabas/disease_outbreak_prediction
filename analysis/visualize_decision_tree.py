"""
Train a simple Decision Tree on outbreakiq_training_data.csv and visualize it.

Outputs:
- reports/decision_tree_regressor.png
- reports/decision_tree_feature_importances.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor, plot_tree


DATA_DIR = Path("data")
REPORTS_DIR = Path("reports")


def ensure_dirs():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "outbreakiq_training_data.csv")
    return df


def prepare_data(df: pd.DataFrame):
    # Target: predict weekly cases
    df = df.copy()
    df = df.dropna(subset=["cases"])  # require target

    # Numeric features only, exclude leakage and target
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    exclude = {"cases", "cases_per_100k"}  # avoid direct leakage of target
    features = [c for c in numeric_cols if c not in exclude]

    X = df[features].copy()
    y = df["cases"].astype(float)

    # Impute missing numeric features with median
    X = X.apply(lambda col: col.fillna(col.median()))

    # Some columns may still be NaN if entirely missing; fill any remaining with 0
    X = X.fillna(0)

    return X, y, features


def train_tree(X, y, max_depth=4, random_state=42):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    model = DecisionTreeRegressor(max_depth=max_depth, random_state=random_state)
    model.fit(X_train, y_train)
    r2_train = model.score(X_train, y_train)
    r2_test = model.score(X_test, y_test)
    print(f"DecisionTreeRegressor R^2 — train: {r2_train:.3f}, test: {r2_test:.3f}")
    return model


def save_tree_plot(model: DecisionTreeRegressor, feature_names):
    fig, ax = plt.subplots(figsize=(14, 10))
    plot_tree(
        model,
        feature_names=feature_names,
        filled=True,
        rounded=True,
        fontsize=8,
        ax=ax,
    )
    fig.tight_layout()
    out_path = REPORTS_DIR / "decision_tree_regressor.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved tree visualization → {out_path}")


def save_feature_importances(model: DecisionTreeRegressor, feature_names):
    imp = pd.DataFrame({
        "feature": feature_names,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)
    out_path = REPORTS_DIR / "decision_tree_feature_importances.csv"
    imp.to_csv(out_path, index=False)
    print(f"Saved feature importances → {out_path}")


def main():
    ensure_dirs()
    df = load_dataset()
    X, y, features = prepare_data(df)
    model = train_tree(X, y, max_depth=4, random_state=42)
    save_tree_plot(model, features)
    save_feature_importances(model, features)


if __name__ == "__main__":
    main()