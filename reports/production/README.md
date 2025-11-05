Production Reports

- predictions_best_by_disease.csv
  - Primary predictions feed. One row per (year, week [, state]) and disease.
  - Columns: model_type, disease, y_true, y_prob (classifier only), y_pred, year, week, state.
  - Covid-19 appears as both regressor_weekly_state (counts) and classifier_weekly_state (risk).

- predictions_latest_week.csv
  - Latest (year, week) snapshot across all diseases and model types.
  - Use for dashboards/alerts needing a single current view.

- metrics_regression.csv
  - Weekly state regressor metrics per disease (R2, MAE, RMSE, n_train, n_test).

- metrics_regression_weekly_from_annual.csv
  - Weekly-from-annual regressor metrics per disease.

- metrics_alert_classification.csv
  - Covid-19 classifier metrics (ROC/PR AUC, precision, recall, F1, n_train, n_test).

Notes
- Source models live in models/ (unused models are in models/unused/).
- analysis/eval_models.py regenerates predictions in reports/; after running, move
  predictions_best_by_disease.csv into reports/production/ and predictions_all_models.csv
  into reports/unused/ to keep the production surface clean.