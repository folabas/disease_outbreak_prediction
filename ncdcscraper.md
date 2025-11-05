Love this — your critique is sharp and exactly on-target. I’ll do the thing you asked for: a concrete, repo-aware plan **with exact feature lists, labeling rules, evaluation metrics, file-to-file mapping, code snippets you can drop in, and test ideas** so you can move from “early-warning” to “surge-ready” quickly.

I’ll present:

1. Prioritized implementation plan (what to do, in what order)
2. Concrete feature additions (full list + why) and the code you can add to `build_features.py`
3. Surge-labeling module you can drop into `ml/labels.py` (z-score, percent-over-baseline, MAD)
4. Model upgrades (switching/adding LightGBM + calibration + uncertainty via ensembles/quantiles)
5. Evaluation additions (lead-time, top-k precision, timeliness) with code to add to `eval_models.py`
6. Drift & retrain automation skeleton (`ml/drift.py`, GitHub Actions notes)
7. Unit / integration tests to validate each step
8. Quick checklist to get this deployed

I’ll keep snippets minimal but copy-paste-ready and map each to where it belongs.

---


1. **Feature engineering (top priority)** — multi-lag, growth, rolling stats, acceleration. (Files: `ml/build_features.py`)
2. **Surge labeling (target creation)** — disease/state adaptive (z-score + percent-over-baseline + MAD). (Add `ml/labels.py`; integrate into `ml/data.py` & `train_alert.py`)
3. **Model upgrade** — LightGBM/XGBoost for alerts & regression (keep RF baseline). Add class weighting, small CV. (Files: `ml/models.py`, `ml/train_alert.py`, `ml/train_regression.py`)
4. **Evaluation changes** — lead-time, top-k precision, timeliness, false-alarm rate. (File: `ml/eval_models.py`)
5. **Uncertainty & calibration** — tree variance, quantile regression or ensemble quantiles; calibrate classifier probabilities. (Files: `ml/models.py`, `ml/eval_models.py`, `ml/predict_live.py`)
6. **Drift detection + retrain scheduler** — monitor covariate/perf drift and trigger retrain. (Add `ml/drift.py`, wire in `run_live_cycle.py` and `.github/workflows/retrain.yml`)
7. **Ops: monitoring + alert routing** — add dashboards & alert tiers. (Integration work)

Do items 1–3 first — they give the largest jump for the least complexity.

---

# 2) Feature engineering: exact list & why

**Add these features per (disease, state, year, week) row.** Put implementation in `ml/build_features.py` so `pipeline.run()` uses them.

Core additions:

* `cases_lag_1, cases_lag_2, cases_lag_3, cases_lag_4` — recent memory.
* `cases_roll_mean_2, roll_mean_4, roll_mean_8` — short-term baselines.
* `cases_roll_std_4, roll_std_8` — volatility.
* `cases_pct_change_1` = (cases - cases_lag_1) / (cases_lag_1 + 1e-6) — immediate growth.
* `cases_growth_rate_4wk` — fit linear slope on log(cases+1) over last 4 weeks.
* `cases_accel_4wk` = growth_rate_4wk - growth_rate_8wk — acceleration signal.
* `z_score_4wk` = (cases - roll_mean_4) / (roll_std_4 + eps)
* `cases_per_100k_lag_1` — if you’re using per-100k signals for alerts.
* `reporting_delay` proxy — difference between `report_date` and expected week date if available (helps nowcasting/backfill).
* Keep existing weather/demographic features (temperature_2m_mean, who_country_cases, etc.) but add **anomalies**:

  * `precip_anom_2wk` = precipitation_sum - roll_mean_precip_8
  * `temp_anom_2wk` = temperature_2m_mean - roll_mean_temp_52

**Why:** surge onset is acceleration — not absolute value. Adding lags + growth & acceleration lets model see momentum.

---

## build_features.py — drop-in additions

Below is a focused function to compute lags, rolling stats, growth and accel. Add to your `build_latest_features` pipeline (or a new helper file `ml/features_helpers.py`) and call from `build_latest_features`.

```python
# file: ml/features_helpers.py
import numpy as np
import pandas as pd

def add_time_series_features(df: pd.DataFrame,
                             value_col: str = "cases",
                             group_cols: list = ["disease", "state"],
                             lags: list[int] = [1,2,3,4],
                             roll_windows: list[int] = [2,4,8]) -> pd.DataFrame:
    df = df.sort_values(group_cols + ["year", "week"]).copy()
    for lag in lags:
        df[f"{value_col}_lag_{lag}"] = df.groupby(group_cols)[value_col].shift(lag).fillna(0.0)
    for w in roll_windows:
        df[f"{value_col}_roll_mean_{w}"] = df.groupby(group_cols)[value_col].transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean()).fillna(0.0)
        df[f"{value_col}_roll_std_{w}"] = df.groupby(group_cols)[value_col].transform(lambda s: s.shift(1).rolling(w, min_periods=1).std()).fillna(0.0)
    # percent change (last week)
    df[f"{value_col}_pct_change_1"] = (df[value_col] - df[f"{value_col}_lag_1"]) / (df[f"{value_col}_lag_1"] + 1e-6)
    # log growth rate: slope on log1p over last 4 weeks
    def log_slope(s):
        s = s.shift(1).rolling(4, min_periods=2).apply(lambda x: np.polyfit(np.arange(len(x)), np.log1p(x), 1)[0], raw=True)
        return s.fillna(0.0)
    df[f"{value_col}_growth_rate_4wk"] = df.groupby(group_cols)[value_col].transform(log_slope).fillna(0.0)
    # acceleration: difference between recent growth rates
    df[f"{value_col}_growth_rate_8wk"] = df.groupby(group_cols)[value_col].transform(lambda s: s.shift(1).rolling(8, min_periods=2).apply(lambda x: np.polyfit(np.arange(len(x)), np.log1p(x), 1)[0], raw=True)).fillna(0.0)
    df[f"{value_col}_accel_4wk"] = df[f"{value_col}_growth_rate_4wk'] - df[f"{value_col}_growth_rate_8wk"]
    # zscore
    df[f"{value_col}_z_4wk"] = (df[value_col] - df[f"{value_col}_roll_mean_4"]) / (df[f"{value_col}_roll_std_4"].replace(0, np.nan)).fillna(0.0)
    return df
```

Small notes:

* Use `.shift(1)` in rolling stats to avoid leakage.
* Keep `min_periods=1` during early-history — but consider filtering very small histories later.

**Action:** call `add_time_series_features` inside `build_latest_features` (and in offline dataset building pipelines) so models trained on historical data have these columns.

---

# 3) Surge-labeling module: `ml/labels.py`

Goal: create reproducible surge labels used by `train_alert.py`. Combine rules and produce binary `surge_next_week`.

```python
# file: ml/labels.py
import numpy as np
import pandas as pd

def label_surge_next_week(df: pd.DataFrame,
                          group_cols: list = ["disease", "state"],
                          value_col: str = "cases_per_100k",
                          z_thresh: float = 2.0,
                          pct_thresh: float = 1.5) -> pd.DataFrame:
    """
    Label if next week's cases_per_100k qualifies as a surge by any rule:
      - next_week z-score over rolling window > z_thresh
      - OR next_week > pct_thresh * rolling_mean_4wk
    """
    df = df.copy()
    df = df.sort_values(group_cols + ["year", "week"]).reset_index(drop=True)

    # compute next week's value per group
    df["next_val"] = df.groupby(group_cols)[value_col].shift(-1)

    # rolling mean/std (lookback 4 weeks, excluding current week)
    df["roll_mean_4"] = df.groupby(group_cols)[value_col].transform(lambda s: s.shift(1).rolling(4, min_periods=1).mean())
    df["roll_std_4"] = df.groupby(group_cols)[value_col].transform(lambda s: s.shift(1).rolling(4, min_periods=1).std()).fillna(0.0)

    # zscore of next week
    df["next_z"] = (df["next_val"] - df["roll_mean_4"]) / (df["roll_std_4"] + 1e-6)

    # percent over baseline
    df["next_pct_over_baseline"] = df["next_val"] / (df["roll_mean_4"].replace({0: np.nan}) + 1e-6)

    # MAD option (robust)
    def mad_threshold(s):
        s_shift = s.shift(1).dropna()
        if len(s_shift) < 3:
            return s_shift.mean() if len(s_shift) > 0 else 0.0
        med = np.median(s_shift)
        mad = np.median(np.abs(s_shift - med))
        return (med, mad)
    # apply rules
    df["surge_next_week"] = (
        (df["next_z"] >= z_thresh) |
        (df["next_pct_over_baseline"] >= pct_thresh)
    ).astype(int)

    df = df.dropna(subset=["next_val"]).copy()
    return df
```

**Integration:**

* Replace or augment `label_outbreak_next_week()` in `train_alert.py` to call `label_surge_next_week`.
* Keep a flag to allow static thresh for backward compatibility.

**Why combined rules:** z-score captures deviation in low-variance contexts; percent-over-baseline catches multiplicative fast growth.

---

# 4) Model upgrades & uncertainty

### a) Models: add LightGBM as a quick lift

Edit `ml/models.py` to provide LightGBM builders. (If LightGBM not installed, keep RF fallback.)

```python
# file: ml/models.py (additions)
from lightgbm import LGBMRegressor, LGBMClassifier

def build_lgbm_regressor():
    return LGBMRegressor(
        n_estimators=1000,
        learning_rate=0.05,
        num_leaves=31,
        objective='regression',
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

def build_lgbm_classifier():
    return LGBMClassifier(
        n_estimators=1000,
        learning_rate=0.05,
        num_leaves=31,
        objective='binary',
        class_weight='balanced',
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
```

**Use strategy:** Keep existing RandomForest functions; in `train_*` add an environment switch, e.g. `MODEL_BACKEND = os.getenv("OUTBREAKIQ_MODEL", "rf")`. That way you can A/B compare.

### b) Uncertainty

* For regression: use **ensemble variance** (for RandomForest) — `preds_per_tree` variance gives a basic CI. For LightGBM, train multiple models on bootstrap samples (ensemble) and estimate percentiles. Or use LightGBM quantile objective (LGBMRegressor with `objective='quantile'` for 0.1/0.5/0.9).
* For classifier calibration: use `sklearn.calibration.CalibratedClassifierCV` (with `method='isotonic'` / `'sigmoid'`) on validation set.

**Output format:** `predictions_live.csv` add columns: `y_pred`, `y_pred_lower`, `y_pred_upper`, `prob`, `prob_calibrated`.

---

# 5) Evaluation additions — lead-time, top-k precision, timeliness

Add these to `ml/eval_models.py`. Key metrics:

* **Top-k precision** per disease: sort upcoming-week predictions by probability/risk score; compute precision among top k% (e.g., top 5% of weeks predicted as highest risk).
* **Timeliness (lead-time)**: For each surge event (label positive at t), check first week the model flagged it (prob>=threshold) earlier than t and compute weeks of lead. Average across events.
* **False alarm rate**: #false positives / total negatives.

### Snippet: top-k precision + lead-time

```python
# add to ml/eval_models.py
import numpy as np
import pandas as pd

def precision_at_top_k(pred_df, disease, model_type='classifier_weekly_state', k_percent=0.05, prob_col='y_prob'):
    df = pred_df[(pred_df['disease']==disease) & (pred_df['model_type']==model_type)].copy()
    if df.empty:
        return np.nan
    k = max(1, int(len(df) * k_percent))
    df_sorted = df.sort_values(prob_col, ascending=False).head(k)
    # assume y_true column exists with 0/1
    return df_sorted['y_true'].mean()

def compute_lead_time(pred_df, disease, threshold=0.5):
    # pred_df must contain year, week, disease, y_true, y_prob, and maybe a timestamp ordering
    df = pred_df[pred_df['disease']==disease].sort_values(['year','week']).copy()
    # find true surge weeks
    true_weeks = df[df['y_true']==1][['year','week']].values.tolist()
    lead_times = []
    for (y,w) in true_weeks:
        # find first week prior (or same week) where y_prob >= threshold
        mask_prior = (df['year'] < y) | ((df['year']==y) & (df['week'] <= w))
        prior_rows = df[mask_prior]
        hits = prior_rows[prior_rows['y_prob'] >= threshold]
        if not hits.empty:
            first = hits.iloc[0]
            # compute weeks difference (approx): convert year-week to ordinal (year*52+week)
            t_true = y*52 + w
            t_first = int(first['year']*52 + first['week'])
            lead_times.append(t_true - t_first)
    return np.mean(lead_times) if lead_times else np.nan
```

**Add to `main()`** final reporting: compute and write these metrics into `reports/production/metrics_surges.csv`.

**Important:** define week-to-ordinal with ISO week handling when year/week crosses; above is approximation — use proper conversion for production.

---

# 6) Drift detection & retraining skeleton (`ml/drift.py`)

Objective: detect covariate shifts & performance drops and log trigger.

Simple approach: compare recent 4-week feature distribution to historical (past 52 weeks) using Kolmogorov–Smirnov or population-statistics.

```python
# file: ml/drift.py
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

def detect_covariate_drift(historical_df: pd.DataFrame, recent_df: pd.DataFrame, feature_cols: list, alpha: float = 0.01):
    drifted = {}
    for c in feature_cols:
        if c not in historical_df.columns or c not in recent_df.columns:
            continue
        try:
            stat, p = ks_2samp(historical_df[c].dropna(), recent_df[c].dropna())
            drifted[c] = {"stat": float(stat), "p_value": float(p), "drift": p < alpha}
        except Exception:
            drifted[c] = {"stat": None, "p_value": None, "drift": False}
    return drifted

def should_retrain(drift_report: dict, perf_metrics: dict, perf_drop_threshold: float = 0.1):
    # perf_metrics: {"mae_recent":..., "mae_hist":...}
    retrain_reasons = []
    for f,v in drift_report.items():
        if v.get("drift"):
            retrain_reasons.append(f"covariate_drift_{f}")
    if perf_metrics.get("mae_recent") and perf_metrics.get("mae_hist"):
        drop = (perf_metrics["mae_recent"] - perf_metrics["mae_hist"]) / (perf_metrics["mae_hist"] + 1e-9)
        if drop > perf_drop_threshold:
            retrain_reasons.append("performance_degraded")
    return retrain_reasons
```

**Integration:**

* Run weekly in `run_live_cycle.py` after ingestion and before `run(mode='realtime')`.
* If `should_retrain` returns non-empty, schedule retrain (or auto-run `train_*` scripts) and notify.

**Logging:** put drift results in `reports/production/drift_report.json` and ingest log.

---

# 7) Retrain GitHub workflow (sketch)

Add `.github/workflows/retrain.yml` run weekly:

```yaml
name: Weekly retrain
on:
  schedule:
    - cron: '0 6 * * MON'
jobs:
  retrain:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Fetch live files (if needed)
        run: python -m ml.run_live_cycle --mode cached
      - name: Train regressors
        run: python -m ml.train_regression
      - name: Train alerts
        run: python -m ml.train_alert
      - name: Evaluate
        run: python -m ml.eval_models
      - name: Upload reports
        run: |
          # push reports to artifact storage or commit to repo (if desired)
```

**Safety:** add a manual approval step if auto-deploying models to production.

---

# 8) Tests to add (unit & integration)

**Unit tests:**

* `tests/test_features.py`

  * Input small synthetic timeseries per disease-state; assert lags & roll means are computed and shifted correctly (no leakage).
* `tests/test_labels.py`

  * Synthetic series where week 5 is 3× baseline; assert `surge_next_week` is 1 for week 4 (since label is future week).
* `tests/test_drift.py`

  * Create historical normal distribution and recent shifted distribution; confirm `detect_covariate_drift` signals drift.

**Integration tests:**

* `tests/test_pipeline_realtime.py`

  * Use a small sample dataset, run `build_latest_features()` then `predict_live()` and assert output columns exist (`y_pred`, `y_prob`).
* `tests/test_eval_metrics.py`

  * Build a sample preds DataFrame with few surges and predicted probabilities; test `precision_at_top_k` and `compute_lead_time`.

**Example pytest for features:**

```python
def test_lags_and_rolls(tmp_path):
    from ml.features_helpers import add_time_series_features
    df = pd.DataFrame({
        'disease':['A']*6,
        'state':['S']*6,
        'year':[2023]*6,
        'week':[1,2,3,4,5,6],
        'cases':[0,1,2,5,10,20]
    })
    out = add_time_series_features(df)
    assert 'cases_lag_1' in out.columns
    assert out.loc[out['week']==6,'cases_lag_1'].iloc[0] == 10
    assert out.loc[out['week']==5,'cases_roll_mean_4'].iloc[0] > 0
```

---

# 9) Small changes to training & eval files (where to update)

* `ml/build_features.py`: call new `add_time_series_features()` and include new feature names in `FEATURE_COLUMNS` or use dynamic feature discovery during training.
* `ml/data.py`: add `get_surges()` helper or integrate `labels.label_surge_next_week`.
* `ml/train_alert.py`: use new labels, add LightGBM option, use calibration (`CalibratedClassifierCV`) and compute `y_prob` properly. Save calibration object if used.
* `ml/train_regression.py`: optionally train LightGBM quantile regressors (or bootstrap ensemble) for CI.
* `ml/eval_models.py`: compute and save `metrics_surges.csv` (top-k, lead-time, false-alarm).
* `ml/predict_live.py`: append `y_pred_lower`, `y_pred_upper`, `y_prob_calibrated`, `surge_score`.

---

# 10) Quick checklist to deploy these changes safely

1. Add new feature helper + unit tests → run tests.
2. Add surge labeling + unit tests → run tests.
3. Add LightGBM option + integration test on small dataset.
4. Add evaluation metrics to `eval_models.py` and visualize via `generate_historical_visuals.py`.
5. Add `ml/drift.py` and run weekly drift checks locally to observe behaviors.
6. Add GitHub Actions retrain workflow (start with `dry-run`) and manual approval before production deploy.
7. Monitor model outputs for 4 weeks: deploy but don’t auto-notify users until stable. Tune thresholds and calibration.

---

# 11) Example minimal change you can drop in now

If you want a single immediate improvement with minimal code churn: **add 1–4 week lags + 4-week rolling mean/std + percent change** to `ml/build_features.py`, retrain RF (same code), and update `train_alert.py` to use `label_surge_next_week` (z-score + 1.5× baseline). That alone will materially increase early detection.

---

# 12) Would you like me to… (pick one)

* A) **Create the exact patch** (diff/PR style) implementing the `features_helpers.py` and `labels.py` and update a small number of functions in `build_features.py` and `train_alert.py`? — I’ll produce ready-to-apply code.
* B) **Write the new evaluation functions** and add them into `eval_models.py` (lead-time & top-k) and produce a sample `reports/production/metrics_surges.csv` schema.
* C) **Draft the GitHub Actions retrain workflow** with a safe manual approval gate and artifact publishing instructions.

Pick A, B, or C (or “all three”) and I’ll generate the full code for that choice immediately.
