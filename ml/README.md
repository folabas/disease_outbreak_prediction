# ML Pipeline

This folder contains a modular machine learning pipeline for OutbreakIQ. It trains:

- Per-disease one-week-ahead regressors to forecast weekly case counts.
- Per-disease alert classifiers to predict whether next week will cross an outbreak threshold.

## Structure

- `config.py` – central configuration (paths, features, thresholds).
- `data.py` – dataset loading, cleaning, time-based splitting, feature selection.
- `models.py` – model builders (RandomForest for regression/classification).
- `train_regression.py` – trains and evaluates per-disease regressors.
- `train_alert.py` – labels outbreaks and trains per-disease classifiers.

## Usage

From project root:

```bash
python ml/train_regression.py
python ml/train_alert.py
```

Artifacts:
- Models saved under `models/` as `outbreakiq_regressor_{disease}.pkl` and `outbreakiq_classifier_{disease}.pkl`.
- Metrics saved under `reports/` (`metrics_regression.csv/json`, `metrics_alert_classification.csv/json`).

## Input/Output Contracts

Input features (see `config.FEATURE_COLUMNS`):
- Numeric: `temperature_2m_mean`, `precipitation_sum`, `relative_humidity_2m_mean`, `who_country_cases`, `population`, `urban_percent`, `cases_last_week`, `deaths_last_week`, `cases_per_100k`, `rainfall_change`, `temp_anomaly`, `week_sin`, `week_cos`, `year`.
- Keys: `state`, `disease`, `week_start` (in upstream tables).

Model outputs:
- Regression: `cases_pred` per disease/state/week.
- Alert classification: `outbreak_risk_prob` (via `predict_proba`) and thresholded `outbreak_next_week`.

Naming conventions:
- `models/outbreakiq_regressor_{disease}.pkl`
- `models/outbreakiq_classifier_{disease}.pkl`
- Weekly variants: `models/outbreakiq_regressor_weekly_country_{disease}.pkl`, `models/outbreakiq_regressor_weekly_from_annual_{disease}.pkl`

## Experiment Tracking & Registry

- Tracking uses MLflow when available; falls back to `models/registry.json`.
- Each training run logs params, metrics (`r2/mae/rmse` or `roc_auc/pr_auc/precision/recall/f1`), dataset path + hash, and the model artifact.
- Enable time-series hyperparameter tuning via `OUTBREAKIQ_TUNING=1` environment variable.

Inspect logs:
- MLflow UI: `mlflow ui` (if configured) or read `models/registry.json`.
- Drift: `python ml/drift.py` writes `reports/production/drift_report.json`.

## Retrain & Deploy

- Manual: run the training scripts as above.
- CI: weekly retraining workflow under `.github/workflows/retrain.yml` uploads models and reports as artifacts.
- Promotion: select best-performing models per disease and copy to production use; future work may add automated promotion.

## Notes

- The pipeline filters to valid Nigeria states and sorts by time to avoid leakage.
- Alert labeling uses a static threshold of `cases_per_100k >= 5`. Switch to quantile strategy in `config.py` if desired.
- RandomForest models are chosen for robustness on tabular data. You can swap to XGBoost/LightGBM if you prefer.