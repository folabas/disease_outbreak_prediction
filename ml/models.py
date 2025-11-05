from typing import Dict

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

from .config import RANDOM_STATE


def build_regressor() -> RandomForestRegressor:
    """Create a reasonably strong, fast tree-based regressor.

    Tuned conservatively for small-to-medium tabular data.
    """
    return RandomForestRegressor(
        n_estimators=400,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )


def build_classifier() -> RandomForestClassifier:
    """Create a classification model with class_weight to handle imbalance."""
    return RandomForestClassifier(
        n_estimators=400,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )