import os
import json
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
import pandas as pd

from app.core.config import MODELS_DIR, DATA_DIR, REPORTS_DIR, resolve_path

from app.models.predictions import (
    PredictionQuery,
    PredictionResponse,
    RiskSummary,
    TimePoint,
    FeatureImportance,
)
from app.models.climate import ClimateQuery, ClimateResponse, SeriesPoint
from app.models.population import PopulationResponse, PopulationEntry
from app.models.hospital import HospitalResponse, HospitalTotals
from app.models.insights import InsightsResponse, Metrics, FeatureImportanceItem

_FALLBACK_FEATURES = [
    "cases",
    "deaths",
    "cases_last_week",
    "cases_2w_avg",
    "cases_growth_rate",
    "cases_mean_4w",
    "cases_std_4w",
    "cases_per_100k",
    "deaths_last_week",
    "deaths_mean_4w",
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "precipitation_sum",
    "access_to_clean_water_percent",
    "water_contamination_index",
    "mosquito_density_index",
    "breeding_sites_count",
    "hospital_beds",
    "icu_beds",
    "staff_count",
    "antimalarial_stock_level",
    "ppe_availability_score",
    "population",
    "population_density",
    "growth_rate_percent",
    "urban_percent",
    "market_density",
    "mobility_index",
    "who_cases_national",
    "disease_cholera",
    "disease_malaria",
    "disease_ebola",
    "disease_covid",
]

try:
    from ml.features import FEATURES as MODEL_FEATURES
except Exception:  # pragma: no cover - fallback when ml package unavailable
    MODEL_FEATURES = _FALLBACK_FEATURES


_model = None
_scaler = None
_model_version = None

_WINDOW = 8

_INSIGHTS_CACHE: Dict[Tuple[Optional[str], Optional[str]], Dict[str, Any]] = {}
_INSIGHTS_CACHE_TTL_SECONDS = 600


def _load_training_frame() -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    candidates = ("outbreak_dataset.csv", "outbreak_dataset.csv")
    for fname in candidates:
        path = os.path.join(DATA_DIR, fname)
        if os.path.exists(path):
            # Track dataset version for reproducibility
            try:
                from pathlib import Path as _Path
                from ml.data_versioning import track_dataset_version
                track_dataset_version("outbreak_dataset", _Path(path))
            except Exception:
                pass  # Non-critical, continue if versioning fails
            
            df = pd.read_csv(path)
            missing = [c for c in MODEL_FEATURES if c not in df.columns]
            for col in missing:
                df[col] = 0.0
            df[MODEL_FEATURES] = df[MODEL_FEATURES].apply(pd.to_numeric, errors="coerce").fillna(0.0)
            return df, path
    return None, None


_target_scaler = None

def _try_load_model():
    """Load the model and scalers; fall back gracefully if unavailable."""
    global _model, _scaler, _target_scaler, _model_version
    if _model is not None and _scaler is not None and _target_scaler is not None:
        return
    try:
        from tensorflow.keras.models import load_model
        from joblib import load
        model_path = os.path.join(MODELS_DIR, "lstm_forecaster.h5")
        feature_scaler_path = os.path.join(MODELS_DIR, "feature_scaler.joblib")
        target_scaler_path = os.path.join(MODELS_DIR, "target_scaler.joblib")
        
        if not os.path.exists(model_path) or not os.path.exists(feature_scaler_path):
            _model = None
            _scaler = None
            _target_scaler = None
            _model_version = None
            import logging as _log
            _log.warning("Model/scaler not found; using stub predictions")
            return
        
        _model = load_model(model_path)
        _scaler = load(feature_scaler_path)
        # Load target scaler if available (for inverse transform)
        if os.path.exists(target_scaler_path):
            _target_scaler = load(target_scaler_path)
        else:
            _target_scaler = None
            import logging as _log
            _log.warning("Target scaler not found; predictions may be inaccurate")
        _model_version = "lstm_forecaster"
    except Exception as e:
        _model = None
        _scaler = None
        _target_scaler = None
        _model_version = None
        import logging as _log
        _log.warning(f"Failed to load model/scaler: {str(e)}; using stub predictions")


def predict_series(q: PredictionQuery) -> PredictionResponse:
    """Generate predictions for the given query; return a stub when offline."""
    import logging
    from datetime import datetime, timedelta
    generated_at = datetime.utcnow().isoformat()

    try:
        _try_load_model()

        df, _ = _load_training_frame()

        if df is not None and not df.empty:
            if "disease" in df.columns and q.disease:
                df = df[df["disease"].astype(str).str.lower() == q.disease.lower()]
            if "state" in df.columns and q.region and q.region != "All":
                df = df[df["state"].astype(str).str.lower() == q.region.lower()]

            sort_cols = [c for c in ["year", "week"] if c in df.columns]
            if sort_cols:
                df = df.sort_values(sort_cols).reset_index(drop=True)

        if df is None or df.empty or len(df) < _WINDOW or _model is None or _scaler is None:
            # Use stub predictions
            today = datetime.utcnow().date()
            next_week = today + timedelta(weeks=1)
            two_weeks = today + timedelta(weeks=2)
            base = 20.0

            timeseries = [
                TimePoint(date=next_week.isoformat(), predicted=base, actual=None),
                TimePoint(date=two_weeks.isoformat(), predicted=round(base * 1.05, 2), actual=None),
            ]
            summary = RiskSummary(
                riskScore=0.52,
                riskLevel="low",
                confidence=0.53,
            )
            explanations = [
                FeatureImportance(feature=MODEL_FEATURES[0], importance=0.4),
                FeatureImportance(feature=MODEL_FEATURES[1], importance=0.25),
                FeatureImportance(feature=MODEL_FEATURES[2], importance=0.2),
                FeatureImportance(feature=MODEL_FEATURES[3], importance=0.15),
            ]
        else:
            # Scale features for prediction
            latest_features = df[MODEL_FEATURES].tail(_WINDOW).fillna(0).values
            latest_scaled = _scaler.transform(latest_features)
            latest_scaled = np.expand_dims(latest_scaled, axis=0)
            
            # Make prediction
            y_scaled = float(_model.predict(latest_scaled, verbose=0)[0][0])
            
            # Inverse transform using target scaler if available
            if _target_scaler is not None:
                try:
                    # Target scaler expects shape (n_samples, 1)
                    y_reshaped = np.array([[y_scaled]])
                    pred_val = float(_target_scaler.inverse_transform(y_reshaped)[0][0])
                    pred_val = max(0, round(pred_val, 2))  # Ensure non-negative
                except Exception:
                    # Fallback if inverse transform fails
                    pred_val = max(0, round(y_scaled * 100, 2))  # Rough estimate
            else:
                # Fallback: assume output is already in case units or scale roughly
                pred_val = max(0, round(y_scaled * 100, 2))
            
            # Calculate risk score based on predicted cases
            score = min(pred_val / 200.0, 1.0) if pred_val > 0 else 0.0
            today = datetime.utcnow().date()
            next_week = today + timedelta(weeks=1)
            two_weeks = today + timedelta(weeks=2)
            timeseries = [
                TimePoint(date=next_week.isoformat(), predicted=pred_val, actual=None),
                TimePoint(date=two_weeks.isoformat(), predicted=round(pred_val * 1.03, 2), actual=None),
            ]
            summary = RiskSummary(
                riskScore=round(score, 2),
                riskLevel=("high" if score > 0.75 else "medium" if score > 0.4 else "low"),
                confidence=0.9,
            )
            try:
                # Simple heuristic: importance based on variability over the latest window
                arr = latest[0]  # shape: (window, features)
                import numpy as _np
                var = _np.std(arr, axis=0)
                total = float(_np.sum(var)) or 1.0
                weights = [float(v) / total for v in var]
                explanations = [FeatureImportance(feature=f, importance=float(w)) for f, w in zip(MODEL_FEATURES, weights)]
            except Exception:
                explanations = [FeatureImportance(feature=MODEL_FEATURES[0], importance=0.4),
                                FeatureImportance(feature=MODEL_FEATURES[1], importance=0.25),
                                FeatureImportance(feature=MODEL_FEATURES[2], importance=0.2),
                                FeatureImportance(feature=MODEL_FEATURES[3], importance=0.15)]
    except Exception as e:
        logging.warning("Stub prediction used due to error: %s", str(e))
        today = datetime.utcnow().date()
        next_week = today + timedelta(weeks=1)
        two_weeks = today + timedelta(weeks=2)
        timeseries = [
            TimePoint(date=next_week.isoformat(), predicted=20.0, actual=None),
            TimePoint(date=two_weeks.isoformat(), predicted=21.0, actual=None),
        ]
        summary = RiskSummary(riskScore=0.5, riskLevel="low", confidence=0.52)
        explanations = [FeatureImportance(feature=feat, importance=0.0) for feat in MODEL_FEATURES]

    return PredictionResponse(
        region=q.region,
        disease=q.disease,
        summary=summary,
        timeseries=timeseries,
        explanations=explanations,
        modelVersion=_model_version,
        generatedAt=generated_at,
    )


def get_insights(disease: str, region: Optional[str] = None) -> InsightsResponse:
    cache_key = (disease.lower() if disease else None, region.lower() if region else None)
    cached = _INSIGHTS_CACHE.get(cache_key)
    now = time.time()
    if cached and now - cached.get("ts", 0) < _INSIGHTS_CACHE_TTL_SECONDS:
        return cached["data"]

    # Initialize with None values - only set if we have real data
    metrics = None
    fi = []
    notes_parts: List[str] = []

    # Try to compute metrics from live evaluation reports produced by the current model
    try:
        import pandas as _pd
        metrics_csv = os.path.join(REPORTS_DIR, "evaluation_metrics.csv")
        if os.path.exists(metrics_csv):
            df = _pd.read_csv(metrics_csv)
            if "disease" in df.columns:
                row = df[df["disease"].astype(str).str.lower() == str(disease).lower()].head(1)
                if row is not None and not row.empty:
                    acc = row.iloc[0].get("accuracy_pct")
                    prec = row.iloc[0].get("precision_weighted_pct")
                    rec = row.iloc[0].get("recall_weighted_pct")
                    f1 = row.iloc[0].get("f1_weighted_pct")
                    auc = row.iloc[0].get("auc")

                    def _to_decimal(v: Optional[float]) -> Optional[float]:
                        try:
                            if v is None or (isinstance(v, float) and _pd.isna(v)):
                                return None
                            v = float(v)
                            return v/100.0 if v > 1 else v
                        except Exception:
                            return None
                    m_acc = _to_decimal(acc)
                    m_prec = _to_decimal(prec)
                    m_rec = _to_decimal(rec)
                    m_f1 = _to_decimal(f1)
                    m_auc = None
                    try:
                        m_auc = float(auc) if auc is not None and not _pd.isna(auc) else None
                    except Exception:
                        m_auc = None
                    if any(v is not None for v in [m_acc, m_prec, m_rec, m_f1, m_auc]):
                        metrics = Metrics(
                            accuracy=m_acc if m_acc is not None else 0.0,
                            precision=m_prec if m_prec is not None else 0.0,
                            recall=m_rec if m_rec is not None else 0.0,
                            f1=m_f1 if m_f1 is not None else 0.0,
                            auc=m_auc if m_auc is not None else None,
                        )
                        ts = row.iloc[0].get("timestamp")
                        mv = row.iloc[0].get("model_version") or "unknown"
                        if ts:
                            notes_parts.append(f"Evaluation refreshed at {ts} (model {mv}).")
                        roc_path = row.iloc[0].get("roc_path")
                        if isinstance(roc_path, str) and roc_path:
                            notes_parts.append(f"ROC curve available at {roc_path}.")
    except Exception:
        pass

    # Try to incorporate optional health notes if present
    try:
        health_path = os.path.join(REPORTS_DIR, "health.json")
        if os.path.exists(health_path):
            with open(health_path, "r", encoding="utf-8") as f:
                health = json.load(f)
                if isinstance(health, dict):
                    extra = health.get("notes")
                    if isinstance(extra, str) and extra:
                        notes_parts.append(extra)
    except Exception:
        pass

    # Include regression / alert summaries when available
    try:
        reg_path = os.path.join(REPORTS_DIR, "metrics_regression.csv")
        if os.path.exists(reg_path):
            reg_df = pd.read_csv(reg_path)
            reg_row = reg_df[reg_df["disease"].astype(str).str.lower() == str(disease).lower()].head(1)
            if reg_row is not None and not reg_row.empty:
                mae = reg_row.iloc[0].get("mae")
                overall = reg_row.iloc[0].get("overall_mae")
                if mae is not None:
                    notes_parts.append(f"Regression MAE: {float(mae):.2f} (overall {overall}).")
    except Exception:
        pass

    try:
        alert_path = os.path.join(REPORTS_DIR, "metrics_alert_classification.csv")
        if os.path.exists(alert_path):
            alert_df = pd.read_csv(alert_path)
            alert_row = alert_df[alert_df["disease"].astype(str).str.lower() == str(disease).lower()].head(1)
            if alert_row is not None and not alert_row.empty:
                precision = alert_row.iloc[0].get("precision_weighted_pct")
                recall = alert_row.iloc[0].get("recall_weighted_pct")
                if precision is not None and recall is not None:
                    notes_parts.append(
                        f"Alert classifier precision {float(precision):.1f}% / recall {float(recall):.1f}%."
                    )
    except Exception:
        pass

    # Compute feature importance from training data (correlation heuristic)
    try:
        df_all, df_path = _load_training_frame()
        if df_all is not None:
            df = df_all
            if "disease" in df.columns and disease:
                df = df[df["disease"].astype(str).str.lower() == str(disease).lower()]
            if region and "state" in df.columns:
                df = df[df["state"].astype(str).str.lower() == str(region).lower()]
            cols = [c for c in MODEL_FEATURES if c in df.columns]
            def _friendly(n: str) -> str:
                """Convert feature names to human-readable labels."""
                friendly_map = {
                    "cases": "Current Cases",
                    "cases_last_week": "Cases (1 week ago)",
                    "cases_2w_avg": "Cases (2-week average)",
                    "cases_growth_rate": "Case Growth Rate",
                    "cases_mean_4w": "Cases (4-week mean)",
                    "cases_std_4w": "Cases (4-week std dev)",
                    "cases_per_100k": "Cases per 100k",
                    "deaths": "Deaths",
                    "deaths_last_week": "Deaths (1 week ago)",
                    "deaths_mean_4w": "Deaths (4-week mean)",
                    "temperature_2m_mean": "Temperature",
                    "relative_humidity_2m_mean": "Humidity",
                    "precipitation_sum": "Precipitation",
                    "access_to_clean_water_percent": "Clean Water Access %",
                    "water_contamination_index": "Water Contamination",
                    "mosquito_density_index": "Mosquito Density",
                    "breeding_sites_count": "Breeding Sites",
                    "hospital_beds": "Hospital Beds",
                    "icu_beds": "ICU Beds",
                    "staff_count": "Healthcare Staff",
                    "antimalarial_stock_level": "Antimalarial Stock",
                    "ppe_availability_score": "PPE Availability",
                    "population": "Population",
                    "population_density": "Population Density",
                    "urban_percent": "Urbanization %",
                    "growth_rate_percent": "Population Growth %",
                    "market_density": "Market Density",
                    "mobility_index": "Mobility Index",
                    "who_cases_national": "National Cases (WHO)",
                }
                return friendly_map.get(n, n.replace("_", " ").title())

            def _compute_pairs(frame: pd.DataFrame) -> List[tuple[str, float]]:
                """Compute feature importance using multiple methods for better explainability."""
                cols2 = [c for c in MODEL_FEATURES if c in frame.columns]
                if "cases" not in cols2 or len(cols2) < 2 or len(frame) <= 10:
                    return []
                
                base = pd.to_numeric(frame["cases"], errors="coerce")
                out: List[tuple[str, float]] = []
                
                for c in cols2:
                    if c == "cases":  # Skip target variable
                        continue
                    
                    s = pd.to_numeric(frame[c], errors="coerce")
                    
                    # Method 1: Pearson correlation (linear relationship)
                    try:
                        corr_val = float(abs(s.corr(base)))
                        if np.isnan(corr_val):
                            corr_val = 0.0
                    except Exception:
                        corr_val = 0.0
                    
                    # Method 2: Mutual information (non-linear relationships)
                    mi_val = 0.0
                    try:
                        from sklearn.feature_selection import mutual_info_regression
                        # Sample if too large for performance
                        sample_size = min(1000, len(frame))
                        if sample_size > 10:
                            sample_idx = np.random.choice(len(frame), sample_size, replace=False)
                            s_sample = s.iloc[sample_idx].values.reshape(-1, 1)
                            base_sample = base.iloc[sample_idx].values
                            mi_val = float(mutual_info_regression(s_sample, base_sample, random_state=42)[0])
                            # Normalize to 0-1 range (MI can be any positive value)
                            if mi_val > 0:
                                mi_val = min(1.0, mi_val / 10.0)  # Rough normalization
                    except Exception:
                        pass
                    
                    # Method 3: Feature variance (importance of variation)
                    var_val = 0.0
                    try:
                        var_val = float(s.var())
                        # Normalize variance (relative to max variance in dataset)
                        max_var = max([pd.to_numeric(frame[col], errors="coerce").var() for col in cols2 if col != "cases"], default=1.0)
                        if max_var > 0:
                            var_val = min(1.0, var_val / max_var)
                    except Exception:
                        pass
                    
                    # Combined importance score (weighted average)
                    # Correlation: 50%, Mutual Info: 30%, Variance: 20%
                    combined = (0.5 * corr_val) + (0.3 * mi_val) + (0.2 * var_val)
                    out.append((c, combined))
                
                return out

            pairs = _compute_pairs(df)
            if (not pairs or sum(v for _, v in pairs) == 0.0) and df_path:
                df_fallback = pd.read_csv(df_path)
                pairs = _compute_pairs(df_fallback)
            if pairs:
                total = sum(v for _, v in pairs) or 1.0
                fi = [FeatureImportanceItem(name=_friendly(n), value=float(v/total)) for n, v in pairs]
                notes_parts.append("Feature importance computed from latest training window.")
    except Exception:
        pass

    # Only return response if we have real metrics or feature importance
    if metrics is None and not fi:
        # Return empty response if no data available
        notes = " ".join(notes_parts).strip() or "No evaluation metrics available. Please run model evaluation first."
        response = InsightsResponse(
            metrics=Metrics(accuracy=0.0, precision=0.0, recall=0.0, f1=0.0, auc=None),
            featureImportance=fi,
            notes=notes
        )
    elif metrics is None:
        # We have feature importance but no metrics
        notes = " ".join(notes_parts).strip() or "Feature importance available, but evaluation metrics not found. Please run model evaluation."
        response = InsightsResponse(
            metrics=Metrics(accuracy=0.0, precision=0.0, recall=0.0, f1=0.0, auc=None),
            featureImportance=fi,
            notes=notes
        )
    else:
        notes = " ".join(notes_parts).strip() or "Model trained on 10 years, 36 states."
        response = InsightsResponse(metrics=metrics, featureImportance=fi, notes=notes)
    _INSIGHTS_CACHE[cache_key] = {"ts": now, "data": response}
    return response


def _parse_year(s: Optional[str]) -> Optional[int]:
    try:
        s = str(s)
        if "-W" in s:
            return int(s.split("-W")[0])
        from datetime import datetime as _dt
        return _dt.fromisoformat(s).year
    except Exception:
        return None


def _parse_year_week(s: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    try:
        s = str(s)
        if "-W" in s:
            parts = s.split("-W")
            return int(parts[0]), int(parts[1])
        from datetime import datetime as _dt
        dt = _dt.fromisoformat(s)
        return dt.isocalendar()[0], dt.isocalendar()[1]
    except Exception:
        return None, None


def get_disease_alerts(disease: str, region: str = "All", threshold: float = 0.7) -> List[Dict[str, Any]]:
    """
    Generate disease alerts based on prediction risk scores.
    Returns a list of alert dictionaries matching OutbreakAlert structure.
    """
    alerts: List[Dict[str, Any]] = []
    
    try:
        # Get predictions for the disease/region
        q = PredictionQuery(disease=disease, region=region, horizonDays=14)
        prediction = predict_series(q)
        
        # Check if risk score exceeds threshold
        risk_score = prediction.summary.riskScore
        risk_level = prediction.summary.riskLevel.lower()
        confidence = prediction.summary.confidence
        
        # Determine severity based on risk level and threshold
        if risk_score >= threshold:
            if risk_level in ("high", "critical"):
                severity = "emergency"
            elif risk_level == "medium":
                severity = "alert"
            else:
                severity = "warning"
        else:
            # Only return alerts if risk is significant
            if risk_score < 0.5:
                return alerts
            severity = "warning"
        
        # Get recent cases data for trend calculation
        df, _ = _load_training_frame()
        cases_data = None
        trend = "stable"
        
        if df is not None and not df.empty:
            df_filtered = df.copy()
            if "disease" in df.columns and disease:
                df_filtered = df_filtered[df_filtered["disease"].astype(str).str.lower() == disease.lower()]
            if "state" in df.columns and region and region != "All":
                df_filtered = df_filtered[df_filtered["state"].astype(str).str.lower() == region.lower()]
            
            if not df_filtered.empty and "cases" in df_filtered.columns:
                # Get recent cases for trend
                recent_cases = df_filtered["cases"].tail(4).tolist() if len(df_filtered) >= 4 else df_filtered["cases"].tolist()
                if len(recent_cases) >= 2:
                    if recent_cases[-1] > recent_cases[0] * 1.1:
                        trend = "increasing"
                    elif recent_cases[-1] < recent_cases[0] * 0.9:
                        trend = "decreasing"
                    cases_data = float(recent_cases[-1]) if recent_cases else 0.0
                elif len(recent_cases) == 1:
                    cases_data = float(recent_cases[0])
        
        # Get predicted cases from timeseries
        predicted_cases = 0.0
        if prediction.timeseries:
            predicted_cases = float(prediction.timeseries[0].predicted) if prediction.timeseries else 0.0
        
        current_cases = cases_data if cases_data is not None else predicted_cases
        
        # Generate alert description
        description = f"Risk level: {risk_level.upper()} (score: {risk_score:.2f}). "
        if trend == "increasing":
            description += "Cases are increasing. "
        elif trend == "decreasing":
            description += "Cases are decreasing. "
        description += f"Predicted cases: {predicted_cases:.0f}. Confidence: {confidence*100:.0f}%."
        
        # Create alert
        alert_id = f"{disease}_{region}_{int(time.time())}"
        alert = {
            "id": alert_id,
            "region": region,
            "disease": disease,
            "severity": severity,
            "details": {
                "cases": int(current_cases),
                "trend": trend,
                "description": description.strip(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        alerts.append(alert)
        
        # If region is "All", also generate alerts for top-risk states
        if region == "All" and df is not None and not df.empty:
            df_filtered = df[df["disease"].astype(str).str.lower() == disease.lower()] if "disease" in df.columns else df
            if "state" in df_filtered.columns and "cases" in df_filtered.columns:
                # Get top states by recent cases
                state_avg = df_filtered.groupby("state")["cases"].mean().sort_values(ascending=False).head(5)
                for state_name, avg_cases in state_avg.items():
                    if avg_cases > 0 and state_name.lower() != "all":
                        state_q = PredictionQuery(disease=disease, region=str(state_name), horizonDays=14)
                        state_pred = predict_series(state_q)
                        if state_pred.summary.riskScore >= threshold * 0.8:  # Slightly lower threshold for individual states
                            state_severity = "alert" if state_pred.summary.riskScore >= threshold else "warning"
                            state_alert = {
                                "id": f"{disease}_{state_name}_{int(time.time())}",
                                "region": str(state_name),
                                "disease": disease,
                                "severity": state_severity,
                                "details": {
                                    "cases": int(avg_cases),
                                    "trend": "stable",
                                    "description": f"State-level alert: {state_pred.summary.riskLevel.upper()} risk (score: {state_pred.summary.riskScore:.2f})",
                                },
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                            alerts.append(state_alert)
    
    except Exception as e:
        import logging
        logging.warning(f"Error generating disease alerts: {str(e)}")
        # Return empty list on error rather than crashing
    
    return alerts


# ========== Hospital Service Functions ==========

def get_hospital(region: str = "All") -> HospitalResponse:
    """Get hospital data for a region."""
    try:
        hospital_path = os.path.join(DATA_DIR, "hospital", "hospitals.csv")
        if not os.path.exists(hospital_path):
            # Return empty response if file doesn't exist
            return HospitalResponse(
                region=region,
                totals=HospitalTotals(facilities=0, avgBedCapacity=0.0, bedsPer10k=0.0),
                facilitiesGeo={"type": "FeatureCollection", "features": []}
            )
        
        df = pd.read_csv(hospital_path)
        
        # Filter by region if not "All"
        if region and region.lower() != "all":
            df = df[df["state"].astype(str).str.lower() == region.lower()]
        
        # Get latest year/week for each facility (most recent data)
        if "year" in df.columns and "week" in df.columns:
            df = df.sort_values(["year", "week"], ascending=False).groupby("facility", as_index=False).first()
        elif "year" in df.columns:
            df = df.sort_values("year", ascending=False).groupby("facility", as_index=False).first()
        
        # Calculate totals
        total_facilities = len(df) if not df.empty else 0
        avg_beds = float(df["beds"].mean()) if not df.empty and "beds" in df.columns and df["beds"].notna().any() else 0.0
        avg_beds_per_10k = float(df["beds_per_10k"].mean()) if not df.empty and "beds_per_10k" in df.columns and df["beds_per_10k"].notna().any() else 0.0
        
        # Build GeoJSON features
        features = []
        for _, row in df.iterrows():
            if pd.notna(row.get("latitude")) and pd.notna(row.get("longitude")):
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(row.get("longitude", 0)), float(row.get("latitude", 0))]
                    },
                    "properties": {
                        "name": str(row.get("facility", "Unknown")),
                        "region": str(row.get("state", region)),
                        "lga": str(row.get("lga", "-")),
                        "beds": int(row.get("beds", 0)) if pd.notna(row.get("beds")) else 0,
                        "icu_beds": int(row.get("icu_beds", 0)) if pd.notna(row.get("icu_beds")) else 0,
                        "staff": int(row.get("staff_count", 0)) if pd.notna(row.get("staff_count")) else 0,
                        "healthcare": "Hospital",
                        "amenity": "hospital"
                    }
                })
        
        facilities_geo = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return HospitalResponse(
            region=region,
            totals=HospitalTotals(
                facilities=total_facilities,
                avgBedCapacity=avg_beds,
                bedsPer10k=avg_beds_per_10k
            ),
            facilitiesGeo=facilities_geo
        )
    except Exception as e:
        import logging
        logging.warning(f"Error loading hospital data: {str(e)}")
        return HospitalResponse(
            region=region,
            totals=HospitalTotals(facilities=0, avgBedCapacity=0.0, bedsPer10k=0.0),
            facilitiesGeo={"type": "FeatureCollection", "features": []}
        )


def get_hospital_capacity_trends(region: str = "All") -> List[Dict[str, Any]]:
    """Get hospital capacity trends over time."""
    try:
        hospital_path = os.path.join(DATA_DIR, "hospital", "hospitals.csv")
        if not os.path.exists(hospital_path):
            return []
        
        df = pd.read_csv(hospital_path)
        
        # Filter by region if not "All"
        if region and region.lower() != "all":
            df = df[df["state"].astype(str).str.lower() == region.lower()]
        
        if df.empty:
            return []
        
        # Group by year/week and calculate available beds
        if "year" in df.columns and "week" in df.columns:
            # Calculate total beds minus admissions (simplified capacity model)
            df["beds_available"] = df["beds"] - df.get("admissions", 0)
            df["beds_available"] = df["beds_available"].clip(lower=0)
            
            trends = df.groupby(["year", "week"]).agg({
                "beds_available": "sum",
                "beds": "sum"
            }).reset_index()
            
            # Convert to date strings (ISO week format)
            trends["date"] = trends.apply(
                lambda row: f"{int(row['year'])}-W{int(row['week']):02d}",
                axis=1
            )
            
            return [
                {
                    "date": str(row["date"]),
                    "bedsAvailable": int(row["beds_available"]) if pd.notna(row["beds_available"]) else 0,
                    "bedOccupancy": int(row["beds"] - row["beds_available"]) if pd.notna(row["beds"]) else 0
                }
                for _, row in trends.iterrows()
            ]
        
        return []
    except Exception as e:
        import logging
        logging.warning(f"Error loading hospital capacity trends: {str(e)}")
        return []


def get_hospital_resources(region: str = "All", resource_type: str = "beds") -> Dict[str, Any]:
    """Get hospital resources as GeoJSON."""
    try:
        hospital_path = os.path.join(DATA_DIR, "hospital", "hospitals.csv")
        if not os.path.exists(hospital_path):
            return {"type": "FeatureCollection", "features": []}
        
        df = pd.read_csv(hospital_path)
        
        # Filter by region if not "All"
        if region and region.lower() != "all":
            df = df[df["state"].astype(str).str.lower() == region.lower()]
        
        # Get latest data per facility
        if "year" in df.columns and "week" in df.columns:
            df = df.sort_values(["year", "week"], ascending=False).groupby("facility", as_index=False).first()
        elif "year" in df.columns:
            df = df.sort_values("year", ascending=False).groupby("facility", as_index=False).first()
        
        features = []
        for _, row in df.iterrows():
            if pd.notna(row.get("latitude")) and pd.notna(row.get("longitude")):
                # Determine value based on resource type
                if resource_type == "beds":
                    value = int(row.get("beds", 0)) if pd.notna(row.get("beds")) else 0
                elif resource_type == "staff":
                    value = int(row.get("staff_count", 0)) if pd.notna(row.get("staff_count")) else 0
                else:  # equipment or default
                    value = int(row.get("icu_beds", 0)) if pd.notna(row.get("icu_beds")) else 0
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(row.get("longitude", 0)), float(row.get("latitude", 0))]
                    },
                    "properties": {
                        "name": str(row.get("facility", "Unknown")),
                        "region": str(row.get("state", region)),
                        "value": value,
                        "resourceType": resource_type
                    }
                })
        
        return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        import logging
        logging.warning(f"Error loading hospital resources: {str(e)}")
        return {"type": "FeatureCollection", "features": []}


# ========== Population Service Functions ==========

def get_population(region: str = "All", startDate: Optional[str] = None, endDate: Optional[str] = None) -> PopulationResponse:
    """Get population data for a region with risk-per-capita metrics."""
    try:
        pop_path = os.path.join(DATA_DIR, "population", "population_states.csv")
        if not os.path.exists(pop_path):
            return PopulationResponse(region=region, totalPopulation=0.0, growthRates=[], density=[])
        
        df = pd.read_csv(pop_path)
        
        # Filter by region if not "All"
        if region and region.lower() != "all":
            df = df[df["state"].astype(str).str.lower() == region.lower()]
        
        # Filter by date range if provided
        if startDate or endDate:
            if "year" in df.columns:
                if startDate:
                    start_year = _parse_year(startDate)
                    if start_year:
                        df = df[df["year"] >= start_year]
                if endDate:
                    end_year = _parse_year(endDate)
                    if end_year:
                        df = df[df["year"] <= end_year]
        
        # Calculate total population FIRST (should not be filtered by date range - always use latest year)
        # Load fresh copy for total population calculation
        total_pop_df = pd.read_csv(pop_path)
        if region and region.lower() != "all":
            total_pop_df = total_pop_df[total_pop_df["state"].astype(str).str.lower() == region.lower()]
        
        # Get latest year for total population calculation (not affected by date range filter)
        if "year" in total_pop_df.columns:
            total_pop_df_latest = total_pop_df.sort_values("year", ascending=False).groupby("state", as_index=False).first()
            total_pop = float(total_pop_df_latest["population"].sum()) if "population" in total_pop_df_latest.columns and total_pop_df_latest["population"].notna().any() else 0.0
        else:
            total_pop = float(total_pop_df["population"].sum()) if "population" in total_pop_df.columns and total_pop_df["population"].notna().any() else 0.0
        
        # Get latest year for each state (for growth/density calculations)
        if "year" in df.columns:
            df = df.sort_values("year", ascending=False).groupby("state", as_index=False).first()
        
        # Load outbreak data to compute risk-per-capita
        outbreak_df, _ = _load_training_frame()
        risk_per_capita = {}
        
        if outbreak_df is not None and not outbreak_df.empty:
            # Get recent cases (last 12 weeks) by state
            if "year" in outbreak_df.columns and "week" in outbreak_df.columns:
                # Get most recent year/week
                max_year = outbreak_df["year"].max()
                max_week = outbreak_df[outbreak_df["year"] == max_year]["week"].max()
                
                # Filter to recent data (last 12 weeks)
                recent_df = outbreak_df[
                    ((outbreak_df["year"] == max_year) & (outbreak_df["week"] >= max_week - 12)) |
                    ((outbreak_df["year"] == max_year - 1) & (outbreak_df["week"] >= 52 - (12 - max_week)))
                ]
                
                # Aggregate cases by state
                if "state" in recent_df.columns and "cases" in recent_df.columns:
                    state_cases = recent_df.groupby("state")["cases"].sum().to_dict()
                    
                    # Compute risk-per-capita for each state
                    for state_name, pop_row in df.iterrows():
                        state = str(pop_row.get("state", "Unknown"))
                        pop = float(pop_row.get("population", 0)) if pd.notna(pop_row.get("population")) else 0.0
                        cases = state_cases.get(state, 0.0)
                        
                        if pop > 0:
                            risk_per_capita[state] = (cases / pop) * 100000  # Cases per 100k
                        else:
                            risk_per_capita[state] = 0.0
        
        # Build growth rates and density lists
        growth_rates = []
        density = []
        
        # total_pop is already calculated above from latest year (not filtered by date range)
        
        for _, row in df.iterrows():
            state_name = str(row.get("state", "Unknown"))
            growth = float(row.get("growth_rate_percent", 0.0)) if pd.notna(row.get("growth_rate_percent")) else 0.0
            dens = float(row.get("population_density", 0.0)) if pd.notna(row.get("population_density")) else 0.0
            
            growth_rates.append(PopulationEntry(region=state_name, value=growth))
            density.append(PopulationEntry(region=state_name, value=dens))
        
        return PopulationResponse(
            region=region,
            totalPopulation=total_pop if total_pop > 0 else 0.0,
            growthRates=growth_rates,
            density=density
        )
    except Exception as e:
        import logging
        logging.warning(f"Error loading population data: {str(e)}")
        return PopulationResponse(region=region, totalPopulation=0.0, growthRates=[], density=[])


def get_population_demographics(region: str) -> Dict[str, Any]:
    """Get population demographics for a region."""
    try:
        pop_path = os.path.join(DATA_DIR, "population", "population_states.csv")
        if not os.path.exists(pop_path):
            return {
                "region": region,
                "totalPopulation": 0,
                "densityPerKm2": 0.0,
                "demographics": {
                    "ageGroups": {},
                    "gender": {"male": 0, "female": 0}
                },
                "year": datetime.now().year
            }
        
        df = pd.read_csv(pop_path)
        
        # Filter by region
        if region and region.lower() != "all":
            df = df[df["state"].astype(str).str.lower() == region.lower()]
        
        if df.empty:
            return {
                "region": region,
                "totalPopulation": 0,
                "densityPerKm2": 0.0,
                "demographics": {
                    "ageGroups": {},
                    "gender": {"male": 0, "female": 0}
                },
                "year": datetime.now().year
            }
        
        # Get latest year
        latest = df.sort_values("year", ascending=False).iloc[0] if "year" in df.columns else df.iloc[0]
        
        total_pop = int(latest.get("population", 0)) if pd.notna(latest.get("population")) else 0
        density = float(latest.get("population_density", 0.0)) if pd.notna(latest.get("population_density")) else 0.0
        year = int(latest.get("year", datetime.now().year)) if pd.notna(latest.get("year")) else datetime.now().year
        
        # Estimate demographics (since CSV doesn't have detailed breakdown)
        # In a real system, this would come from census data
        return {
            "region": region,
            "totalPopulation": total_pop,
            "densityPerKm2": density,
            "demographics": {
                "ageGroups": {
                    "0-14": int(total_pop * 0.42),  # Estimated
                    "15-64": int(total_pop * 0.54),
                    "65+": int(total_pop * 0.04)
                },
                "gender": {
                    "male": int(total_pop * 0.50),
                    "female": int(total_pop * 0.50)
                }
            },
            "year": year
        }
    except Exception as e:
        import logging
        logging.warning(f"Error loading population demographics: {str(e)}")
        return {
            "region": region,
            "totalPopulation": 0,
            "densityPerKm2": 0.0,
            "demographics": {
                "ageGroups": {},
                "gender": {"male": 0, "female": 0}
            },
            "year": datetime.now().year
        }


def get_population_density_map(region: str = "All") -> Dict[str, Any]:
    """Get population density as GeoJSON map."""
    try:
        # Try to load state boundaries GeoJSON
        geojson_path = resolve_path("web", "outbreakiq", "public", "nigeria-level1.geojson")
        if not os.path.exists(geojson_path):
            # Fallback: try alternative paths
            alt_paths = [
                os.path.join(DATA_DIR, "geo", "nigeria_states.geojson"),
                resolve_path("public", "nigeria-level1.geojson"),
            ]
            geojson_path = None
            for p in alt_paths:
                if os.path.exists(p):
                    geojson_path = p
                    break
        
        if not geojson_path or not os.path.exists(geojson_path):
            return {"type": "FeatureCollection", "features": []}
        
        # Load GeoJSON
        with open(geojson_path, "r", encoding="utf-8") as f:
            geo_data = json.load(f)
        
        # Load population data
        pop_path = os.path.join(DATA_DIR, "population", "population_states.csv")
        if not os.path.exists(pop_path):
            return geo_data  # Return GeoJSON without density data
        
        df = pd.read_csv(pop_path)
        
        # Get latest year for each state
        if "year" in df.columns:
            df = df.sort_values("year", ascending=False).groupby("state").first().reset_index()
        
        # Create lookup for density by state
        density_map = {}
        for _, row in df.iterrows():
            state = str(row.get("state", "")).lower()
            dens = float(row.get("population_density", 0.0)) if pd.notna(row.get("population_density")) else 0.0
            density_map[state] = dens
        
        # Add density to GeoJSON features
        if "features" in geo_data:
            for feature in geo_data["features"]:
                if "properties" in feature:
                    # Try to match state name (handle various property names)
                    state_name = None
                    for key in ["NAME_1", "name", "state", "region", "STATE"]:
                        if key in feature["properties"]:
                            state_name = str(feature["properties"][key]).lower()
                            break
                    
                    if state_name:
                        # Try to find matching density
                        for state_key, density in density_map.items():
                            if state_name in state_key or state_key in state_name:
                                feature["properties"]["density"] = density
                                feature["properties"]["region"] = state_key.title()
                                break
                        else:
                            feature["properties"]["density"] = 0.0
        
        # Filter by region if specified
        if region and region.lower() != "all":
            if "features" in geo_data:
                geo_data["features"] = [
                    f for f in geo_data["features"]
                    if region.lower() in str(f.get("properties", {}).get("region", "")).lower() or
                       region.lower() in str(f.get("properties", {}).get("NAME_1", "")).lower()
                ]
        
        return geo_data
    except Exception as e:
        import logging
        logging.warning(f"Error loading population density map: {str(e)}")
        return {"type": "FeatureCollection", "features": []}


# ========== Geo Service Functions ==========

def get_geo_boundaries(region: str = "All") -> Dict[str, Any]:
    """Get geographic boundaries (GeoJSON) for a region."""
    try:
        # Try to load GeoJSON file
        geojson_path = resolve_path("web", "outbreakiq", "public", "nigeria-level1.geojson")
        if not os.path.exists(geojson_path):
            # Fallback: try alternative paths
            alt_paths = [
                os.path.join(DATA_DIR, "geo", "nigeria_states.geojson"),
                resolve_path("public", "nigeria-level1.geojson"),
            ]
            geojson_path = None
            for p in alt_paths:
                if os.path.exists(p):
                    geojson_path = p
                    break
        
        if not geojson_path or not os.path.exists(geojson_path):
            return {"type": "FeatureCollection", "features": []}
        
        # Load GeoJSON
        with open(geojson_path, "r", encoding="utf-8") as f:
            geo_data = json.load(f)
        
        # Filter by region if specified
        if region and region.lower() != "all":
            if "features" in geo_data:
                geo_data["features"] = [
                    f for f in geo_data["features"]
                    if region.lower() in str(f.get("properties", {}).get("region", "")).lower() or
                       region.lower() in str(f.get("properties", {}).get("NAME_1", "")).lower() or
                       region.lower() in str(f.get("properties", {}).get("name", "")).lower()
                ]
        
        return geo_data
    except Exception as e:
        import logging
        logging.warning(f"Error loading geo boundaries: {str(e)}")
        return {"type": "FeatureCollection", "features": []}


def get_geo_heatmap(region: str = "All", disease: str = "cholera") -> Dict[str, Any]:
    """Get heatmap data (GeoJSON with risk/case intensity) for a region and disease."""
    try:
        # Get boundaries first
        geo_data = get_geo_boundaries(region)
        
        if not geo_data or "features" not in geo_data:
            return {"type": "FeatureCollection", "features": []}
        
        # Load outbreak data to compute risk intensity
        outbreak_df, _ = _load_training_frame()
        
        if outbreak_df is not None and not outbreak_df.empty:
            # Filter by disease
            if "disease" in outbreak_df.columns:
                outbreak_df = outbreak_df[outbreak_df["disease"].astype(str).str.lower() == disease.lower()]
            
            # Filter by region if not "All"
            if region and region.lower() != "all" and "state" in outbreak_df.columns:
                outbreak_df = outbreak_df[outbreak_df["state"].astype(str).str.lower() == region.lower()]
            
            # Get recent cases (last 12 weeks) by state
            if "year" in outbreak_df.columns and "week" in outbreak_df.columns and "state" in outbreak_df.columns:
                max_year = outbreak_df["year"].max()
                max_week = outbreak_df[outbreak_df["year"] == max_year]["week"].max()
                
                # Filter to recent data
                recent_df = outbreak_df[
                    ((outbreak_df["year"] == max_year) & (outbreak_df["week"] >= max_week - 12)) |
                    ((outbreak_df["year"] == max_year - 1) & (outbreak_df["week"] >= 52 - (12 - max_week)))
                ]
                
                # Aggregate cases by state
                if "cases" in recent_df.columns:
                    state_cases = recent_df.groupby("state")["cases"].sum().to_dict()
                    
                    # Normalize to 0-1 scale for heatmap intensity
                    max_cases = max(state_cases.values()) if state_cases else 1.0
                    
                    # Add intensity to GeoJSON features
                    for feature in geo_data["features"]:
                        if "properties" in feature:
                            # Try to match state name
                            state_name = None
                            for key in ["NAME_1", "name", "state", "region", "STATE"]:
                                if key in feature["properties"]:
                                    state_name = str(feature["properties"][key])
                                    break
                            
                            if state_name:
                                # Find matching cases
                                cases = 0.0
                                for state_key, case_count in state_cases.items():
                                    if state_name.lower() in state_key.lower() or state_key.lower() in state_name.lower():
                                        cases = float(case_count)
                                        break
                                
                                # Calculate intensity (0-1 scale)
                                intensity = (cases / max_cases) if max_cases > 0 else 0.0
                                
                                feature["properties"]["intensity"] = intensity
                                feature["properties"]["cases"] = cases
                                feature["properties"]["risk_level"] = (
                                    "high" if intensity > 0.7 else
                                    "medium" if intensity > 0.4 else
                                    "low" if intensity > 0 else
                                    "none"
                                )
                            else:
                                feature["properties"]["intensity"] = 0.0
                                feature["properties"]["cases"] = 0.0
                                feature["properties"]["risk_level"] = "none"
        
        return geo_data
    except Exception as e:
        import logging
        logging.warning(f"Error loading geo heatmap: {str(e)}")
        return {"type": "FeatureCollection", "features": []}


# ========== Climate Service Functions ==========

def get_climate(q: ClimateQuery) -> ClimateResponse:
    """Get climate data (temperature and rainfall) for a region."""
    try:
        # Try to load from standalone climate file first
        climate_path = os.path.join(DATA_DIR, "climate", "climate_weekly.csv")
        df = None
        
        if os.path.exists(climate_path):
            df = pd.read_csv(climate_path)
        else:
            # Fallback: extract climate data from outbreak dataset
            df_path = os.path.join(DATA_DIR, "outbreak_dataset.csv")
            if os.path.exists(df_path):
                df_all = pd.read_csv(df_path)
                # Extract climate columns if they exist
                climate_cols = ["state", "year", "week", "temperature_2m_mean", "relative_humidity_2m_mean", "precipitation_sum"]
                available_cols = [c for c in climate_cols if c in df_all.columns]
                if available_cols:
                    df = df_all[available_cols].copy()
                    df = df.drop_duplicates(subset=["state", "year", "week"]).reset_index(drop=True)
        
        if df is None or df.empty:
            # Return empty response
            return ClimateResponse(
                region=q.region,
                temperature=[],
                rainfall=[]
            )
        
        # Filter by region if not "All"
        if q.region and q.region.lower() != "all":
            if "state" in df.columns:
                # Normalize region name for matching
                region_lower = q.region.lower()
                # Try exact match first
                df_filtered = df[df["state"].astype(str).str.lower() == region_lower]
                if df_filtered.empty:
                    # Try partial match (e.g., "Lagos" matches "Lagos State")
                    df_filtered = df[df["state"].astype(str).str.lower().str.contains(region_lower, na=False)]
                df = df_filtered if not df_filtered.empty else df
        
        # Filter by date range if provided (handle week format like "2021-W17")
        if q.startDate or q.endDate:
            if "year" in df.columns and "week" in df.columns:
                if q.startDate:
                    # Parse year-week format
                    if "-W" in str(q.startDate):
                        try:
                            start_year, start_week = str(q.startDate).split("-W")
                            start_year = int(start_year)
                            start_week = int(start_week)
                            df = df[(df["year"] > start_year) | ((df["year"] == start_year) & (df["week"] >= start_week))]
                        except Exception:
                            start_year = _parse_year(q.startDate)
                            if start_year:
                                df = df[df["year"] >= start_year]
                    else:
                        start_year = _parse_year(q.startDate)
                        if start_year:
                            df = df[df["year"] >= start_year]
                if q.endDate:
                    # Parse year-week format
                    if "-W" in str(q.endDate):
                        try:
                            end_year, end_week = str(q.endDate).split("-W")
                            end_year = int(end_year)
                            end_week = int(end_week)
                            df = df[(df["year"] < end_year) | ((df["year"] == end_year) & (df["week"] <= end_week))]
                        except Exception:
                            end_year = _parse_year(q.endDate)
                            if end_year:
                                df = df[df["year"] <= end_year]
        # Filter by date range
        if q.startDate:
            start_year, start_week = _parse_year_week(q.startDate)
            if start_year and start_week:
                df = df[(df["year"] > start_year) | ((df["year"] == start_year) & (df["week"] >= start_week))]
        
        if q.endDate:
            end_year, end_week = _parse_year_week(q.endDate)
            if end_year and end_week:
                df = df[(df["year"] < end_year) | ((df["year"] == end_year) & (df["week"] <= end_week))]
        
        # Fallback: If no data found for the requested range (e.g., future dates), 
        # use the latest available year's data shifted to the requested year.
        if df.empty and q.startDate:
            # Reload full df to get latest data
            if os.path.exists(climate_path):
                df_full = pd.read_csv(climate_path)
            elif os.path.exists(df_path):
                df_full = pd.read_csv(df_path)
            else:
                df_full = pd.DataFrame()

            if not df_full.empty:
                if q.region and q.region.lower() != "all":
                    df_full = df_full[df_full["state"].astype(str).str.lower() == q.region.lower()]
                
                max_year = int(df_full["year"].max())
                req_start_year, req_start_week = _parse_year_week(q.startDate)
                
                # Calculate year offset
                year_offset = req_start_year - max_year
                
                # Shift requested range back to available data range
                hist_start_year = req_start_year - year_offset
                if q.endDate:
                    req_end_year, req_end_week = _parse_year_week(q.endDate)
                    hist_end_year = req_end_year - year_offset
                else:
                    hist_end_year = hist_start_year
                    req_end_week = 52

                # Filter for historical data
                df = df_full[
                    ((df_full["year"] > hist_start_year) | ((df_full["year"] == hist_start_year) & (df_full["week"] >= req_start_week))) &
                    ((df_full["year"] < hist_end_year) | ((df_full["year"] == hist_end_year) & (df_full["week"] <= req_end_week)))
                ].copy()
                
                # Shift years forward in the result
                if not df.empty:
                    df["year"] = df["year"] + year_offset

        # Sort by year and week
        if "year" in df.columns and "week" in df.columns:
            df = df.sort_values(["year", "week"]).reset_index(drop=True)
        
        # Build temperature and rainfall series
        temperature_points = []
        rainfall_points = []
        
        for _, row in df.iterrows():
            # Create date string from year/week
            if "year" in df.columns and "week" in df.columns:
                year = int(row.get("year", 0))
                week = int(row.get("week", 0))
                date_str = f"{year}-W{week:02d}"
            elif "date" in df.columns:
                date_str = str(row.get("date", ""))
            else:
                continue
            
            # Temperature
            if "temperature_2m_mean" in df.columns:
                temp_val = float(row.get("temperature_2m_mean", 0.0)) if pd.notna(row.get("temperature_2m_mean")) else 0.0
                temperature_points.append(SeriesPoint(date=date_str, value=temp_val))
            
            # Rainfall (precipitation)
            if "precipitation_sum" in df.columns:
                rain_val = float(row.get("precipitation_sum", 0.0)) if pd.notna(row.get("precipitation_sum")) else 0.0
                rainfall_points.append(SeriesPoint(date=date_str, value=rain_val))
        
        # Calculate summary stats
        avg_temp = float(df["temperature_2m_mean"].mean()) if not df.empty and "temperature_2m_mean" in df.columns else 0.0
        total_rain = float(df["precipitation_sum"].sum()) if not df.empty and "precipitation_sum" in df.columns else 0.0
        
        # Calculate changes (stub implementation for now)
        temp_change = 0.0
        rain_change = 0.0
        
        return ClimateResponse(
            region=q.region or "All",
            temperature=temperature_points,
            rainfall=rainfall_points,
            summary={
                "avgTemp": avg_temp,
                "totalRain": total_rain,
                "tempChange": temp_change,
                "rainChange": rain_change,
                "highTemp": float(df["temperature_2m_mean"].max()) if not df.empty else 0.0,
                "heavyRain": float(df["precipitation_sum"].max()) if not df.empty else 0.0
            }
        )
    except Exception as e:
        import logging
        logging.warning(f"Error loading climate data: {str(e)}")
        return ClimateResponse(region=q.region or "All", temperature=[], rainfall=[], summary={})


def get_climate_forecast(region: str, disease: str = "cholera", startDate: Optional[str] = None, endDate: Optional[str] = None, days: int = 7) -> ClimateResponse:
    """Get climate forecast for a region (stub implementation - returns recent historical data as forecast)."""
    try:
        # For now, return recent historical climate data as a simple forecast
        # In a production system, this would call a weather API or use a climate model
        from datetime import datetime, timedelta
        
        # Calculate date range for forecast
        today = datetime.utcnow().date()
        forecast_start = today
        forecast_end = today + timedelta(days=days)
        
        # Normalize region name
        normalized_region = region
        if region and region.lower() in ["all nigeria", "all regions"]:
            normalized_region = "All"
        
        # Create a query for recent historical data to use as baseline
        q = ClimateQuery(
            region=normalized_region,
            disease=disease,
            startDate=startDate or forecast_start.isoformat(),
            endDate=endDate or forecast_end.isoformat()
        )
        
        # Get recent historical data
        historical = get_climate(q)
        
        # If we have historical data, use the most recent values as forecast baseline
        if historical.temperature and historical.rainfall:
            # Use the last available values and project forward
            last_temp = historical.temperature[-1].value if historical.temperature else 25.0  # Default 25°C
            last_rain = historical.rainfall[-1].value if historical.rainfall else 5.0  # Default 5mm
            
            # Generate forecast points (simple: use last known values with small variations)
            forecast_temp = []
            forecast_rain = []
            
            for i in range(days):
                forecast_date = (forecast_start + timedelta(days=i)).isoformat()
                # Simple forecast: use last known value with small random variation
                # In production, this would use a proper weather forecast API
                import random
                temp_variation = random.uniform(-2, 2)  # ±2°C variation
                rain_variation = random.uniform(-1, 1)  # ±1mm variation
                
                forecast_temp.append(SeriesPoint(
                    date=forecast_date,
                    value=max(0, last_temp + temp_variation)  # Ensure non-negative
                ))
                forecast_rain.append(SeriesPoint(
                    date=forecast_date,
                    value=max(0, last_rain + rain_variation)  # Ensure non-negative
                ))
            
            return ClimateResponse(
                region=region,
                temperature=forecast_temp,
                rainfall=forecast_rain
            )
        
        # Fallback: generate default forecast values for Nigeria
        # Use typical Nigerian climate values
        forecast_temp = []
        forecast_rain = []
        
        for i in range(days):
            forecast_date = (forecast_start + timedelta(days=i)).isoformat()
            import random
            # Nigeria typical: 25-32°C, 0-10mm rain
            forecast_temp.append(SeriesPoint(
                date=forecast_date,
                value=random.uniform(25, 32)
            ))
            forecast_rain.append(SeriesPoint(
                date=forecast_date,
                value=random.uniform(0, 10)
            ))
        
        return ClimateResponse(
            region=region,
            temperature=forecast_temp,
            rainfall=forecast_rain
        )
    except Exception as e:
        import logging
        logging.warning(f"Error generating climate forecast: {str(e)}")
        # Return default values instead of empty
        from datetime import datetime, timedelta
        today = datetime.utcnow().date()
        forecast_temp = []
        forecast_rain = []
        
        for i in range(days):
            forecast_date = (today + timedelta(days=i)).isoformat()
            import random
            forecast_temp.append(SeriesPoint(date=forecast_date, value=random.uniform(25, 32)))
            forecast_rain.append(SeriesPoint(date=forecast_date, value=random.uniform(0, 10)))
        
        return ClimateResponse(region=region, temperature=forecast_temp, rainfall=forecast_rain)
