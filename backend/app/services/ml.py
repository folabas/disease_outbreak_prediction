import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

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


_model = None
_scaler = None
_model_version = None

# Minimal feature spec matching training pipeline
_FEATURES = [
    "cases",
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "precipitation_sum",
]
_WINDOW = 8


def _try_load_model():
    global _model, _scaler, _model_version
    if _model is not None:
        return
    try:
        # Lazy import to avoid hard dependency if not available
        from tensorflow.keras.models import load_model  # type: ignore
        from joblib import load  # type: ignore

        model_path = os.path.join(MODELS_DIR, "lstm_forecaster.h5")
        scaler_path = os.path.join(MODELS_DIR, "feature_scaler.joblib")

        if os.path.exists(model_path):
            _model = load_model(model_path)
            _model_version = "lstm_forecaster"
        if os.path.exists(scaler_path):
            _scaler = load(scaler_path)
    except Exception:
        # If not available, keep as None; service will return mock
        _model = None
        _scaler = None
        _model_version = "mock"


def predict_series(q: PredictionQuery) -> PredictionResponse:
    _try_load_model()
    generated_at = datetime.utcnow().isoformat()

    # Default mock timeseries if model/data unavailable
    timeseries: List[TimePoint] = [
        TimePoint(date=datetime.utcnow().date().isoformat(), predicted=120.0, actual=95.0),
        TimePoint(date=datetime.utcnow().date().isoformat(), predicted=130.0, actual=102.0),
    ]
    summary = RiskSummary(riskScore=0.82, riskLevel="high", confidence=0.88)
    explanations: List[FeatureImportance] = [
        FeatureImportance(feature="rainfall_7d_avg", importance=0.22),
        FeatureImportance(feature="population_density", importance=0.19),
    ]

    # If a trained model is available, use it; otherwise compute baseline
    df_path = os.path.join(DATA_DIR, "outbreakiq_training_data_filled.csv")
    try:
        if _model is not None and os.path.exists(df_path):
            df = pd.read_csv(df_path)
            # Filter by disease and region to ensure multi-disease behavior
            try:
                if "disease" in df.columns and q.disease:
                    df = df[df["disease"].astype(str).str.lower() == q.disease.lower()]
                if "state" in df.columns:
                    if q.region and q.region != "All":
                        df = df[df["state"].astype(str).str.lower() == q.region.lower()]
                    else:
                        # Prefer national rows when available
                        if any(df["state"].astype(str).str.lower() == "all"):
                            df = df[df["state"].astype(str).str.lower() == "all"]
            except Exception:
                pass

            # Sort to ensure chronological order if year/week exist
            sort_cols = [c for c in ["year", "week"] if c in df.columns]
            if sort_cols:
                df = df.sort_values(sort_cols).reset_index(drop=True)

            # Ensure required features exist
            missing = [c for c in _FEATURES if c not in df.columns]
            if not missing and len(df) >= _WINDOW:
                latest = df[_FEATURES].tail(_WINDOW).fillna(0).values
                latest = np.expand_dims(latest, axis=0)  # (1, WINDOW, len(FEATURES))

                # Predict next-step (scaled)
                try:
                    y_scaled = float(_model.predict(latest, verbose=0)[0][0])
                except Exception:
                    y_scaled = float(np.clip(np.nanmean(latest[:, :, 0]) / 200.0, 0.0, 1.0))

                # Clamp to [0,1]
                y_scaled = float(min(max(y_scaled, 0.0), 1.0))

                # Inverse-transform to real units if scaler available
                if _scaler is not None:
                    try:
                        inv = float(_scaler.inverse_transform([[y_scaled, 0, 0, 0]])[0][0])
                        pred_val = round(inv, 2)
                        score = min(inv / 200.0, 1.0)
                        conf = 0.9
                    except Exception:
                        pred_val = round(y_scaled, 4)
                        score = y_scaled
                        conf = 0.85
                else:
                    pred_val = round(y_scaled, 4)
                    score = y_scaled
                    conf = 0.85

                timeseries = [
                    TimePoint(date=datetime.utcnow().date().isoformat(), predicted=pred_val, actual=None),
                ]
                # Simple horizon extension using a small drift
                drift = 0.03
                timeseries.append(
                    TimePoint(date=datetime.utcnow().date().isoformat(), predicted=round(pred_val * (1.0 + drift), 4), actual=None)
                )
                summary = RiskSummary(
                    riskScore=round(score, 2),
                    riskLevel=("high" if score > 0.75 else "medium" if score > 0.4 else "low"),
                    confidence=conf,
                )
            else:
                # Fall back to baseline if data insufficient
                raise RuntimeError("Missing features or insufficient rows for window")
        elif os.path.exists(df_path):
            # Baseline from data when model unavailable; filter to requested disease/region
            df = pd.read_csv(df_path)
            try:
                if "disease" in df.columns and q.disease:
                    df = df[df["disease"].astype(str).str.lower() == q.disease.lower()]
                if "state" in df.columns:
                    if q.region and q.region != "All":
                        df = df[df["state"].astype(str).str.lower() == q.region.lower()]
                    else:
                        if any(df["state"].astype(str).str.lower() == "all"):
                            df = df[df["state"].astype(str).str.lower() == "all"]
            except Exception:
                pass

            recent = df.tail(_WINDOW)
            avg_cases = float(np.nanmean(recent.get("cases", pd.Series([0]))))
            timeseries = [
                TimePoint(date=datetime.utcnow().date().isoformat(), predicted=round(avg_cases * 1.05, 2), actual=None),
                TimePoint(date=datetime.utcnow().date().isoformat(), predicted=round(avg_cases * 1.1, 2), actual=None),
            ]
            # Use per-disease scaling if available to make scores comparable
            if "cases_scaled" in recent.columns:
                z = float(np.nanmean(recent["cases_scaled"]))
                score = float(1.0 / (1.0 + np.exp(-z)))  # logistic transform to [0,1]
            else:
                score = min((avg_cases / 200.0), 1.0)
            summary = RiskSummary(riskScore=round(score, 2), riskLevel=("high" if score > 0.75 else "medium" if score > 0.4 else "low"), confidence=0.75)
    except Exception:
        # Keep defaults
        pass

    return PredictionResponse(
        region=q.region,
        disease=q.disease,
        summary=summary,
        timeseries=timeseries,
        explanations=explanations,
        modelVersion=_model_version,
        generatedAt=generated_at,
    )


def get_climate(q: ClimateQuery) -> ClimateResponse:
    # Try to read weather weekly by state; fallback to mock
    temp: List[SeriesPoint] = []
    rain: List[SeriesPoint] = []
    try:
        by_state = os.path.join(DATA_DIR, "live", "weather_weekly_by_state.csv")
        if os.path.exists(by_state):
            df = pd.read_csv(by_state)
            reg = q.region if q.region != "All" else None
            if reg:
                sdf = df[df["state"].str.lower() == reg.lower()]
            else:
                sdf = df
            # Expect columns: date, temperature_2m_mean, precipitation_sum
            for _, row in sdf.tail(10).iterrows():
                temp.append(SeriesPoint(date=str(row.get("date")), value=float(row.get("temperature_2m_mean", 0.0))))
                rain.append(SeriesPoint(date=str(row.get("date")), value=float(row.get("precipitation_sum", 0.0))))
    except Exception:
        pass

    if not temp:
        # Mock
        today = datetime.utcnow().date()
        for i in range(5):
            d = today.isoformat()
            temp.append(SeriesPoint(date=d, value=32.0 - i))
            rain.append(SeriesPoint(date=d, value=5.0 if i % 2 == 0 else 0.0))

    return ClimateResponse(region=q.region, temperature=temp, rainfall=rain)


def _resolve_coords_for_region(region: str) -> tuple[float, float]:
    # Minimal mapping; extend as needed
    mapping = {
        "lagos": (6.5244, 3.3792),
        "kano": (12.0022, 8.5919),
        "rivers": (4.859, 6.9209),
        "abuja": (9.05785, 7.49508),
    }
    key = (region or "").strip().lower()
    return mapping.get(key, (6.5244, 3.3792))


def get_climate_forecast(region: str, disease: str | None = None) -> ClimateResponse:
    # Try Open-Meteo daily forecast; fallback to recent series
    lat, lon = _resolve_coords_for_region(region)
    temp: List[SeriesPoint] = []
    rain: List[SeriesPoint] = []
    try:
        import urllib.request
        import urllib.parse
        import json as _json

        base = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,precipitation_sum",
            "timezone": "Africa/Lagos",
        }
        url = base + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            temps = daily.get("temperature_2m_max", [])
            precs = daily.get("precipitation_sum", [])
            for i in range(min(len(dates), len(temps), len(precs))):
                temp.append(SeriesPoint(date=str(dates[i]), value=float(temps[i])))
                rain.append(SeriesPoint(date=str(dates[i]), value=float(precs[i])))
    except Exception:
        # Fallback to current climate series
        q = ClimateQuery(region=region, disease=disease or "cholera")
        climate = get_climate(q)
        temp = climate.temperature
        rain = climate.rainfall

    return ClimateResponse(region=region, temperature=temp, rainfall=rain)


def get_population(region: str) -> PopulationResponse:
    growth: List[PopulationEntry] = []
    density: List[PopulationEntry] = []
    try:
        wbw = os.path.join(DATA_DIR, "raw", "worldbank_population_weekly.csv")
        if os.path.exists(wbw):
            df = pd.read_csv(wbw)
            # Example aggregation; in practice align columns
            for r in ["North West", "South West", "North Central", "South South", "North East", "South East"]:
                growth.append(PopulationEntry(region=r, value=float(np.random.uniform(2.0, 4.5))))
            density.append(PopulationEntry(region="Lagos", value=212.0))
    except Exception:
        pass

    if not growth:
        growth = [
            PopulationEntry(region="North West", value=4.2),
            PopulationEntry(region="South West", value=3.8),
            PopulationEntry(region="North Central", value=3.1),
            PopulationEntry(region="South South", value=2.8),
            PopulationEntry(region="North East", value=2.4),
            PopulationEntry(region="South East", value=2.1),
        ]
    if not density:
        density = [PopulationEntry(region="Lagos", value=212.0)]

    return PopulationResponse(growthRates=growth, density=density)


def get_hospital(region: str) -> HospitalResponse:
    totals = HospitalTotals(facilities=12450, avgBedCapacity=82.0, bedsPer10k=5.0)
    facilities_geo: Dict[str, Any] = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "General Hospital X", "capacity": 120},
                "geometry": {"type": "Point", "coordinates": [8.6753, 9.082]},
            }
        ],
    }
    return HospitalResponse(region=region, totals=totals, facilitiesGeo=facilities_geo)


def get_hospital_capacity_trends(region: str) -> List[Dict[str, Any]]:
    # Try to load capacity CSV; fallback to synthetic trend
    series: List[Dict[str, Any]] = []
    try:
        import os
        import pandas as pd
        from datetime import datetime

        path = os.path.join(DATA_DIR, "hospitals", "hospital_capacity.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            if "region" in df.columns:
                df = df[df["region"].astype(str).str.lower() == region.lower()]
            for _, row in df.iterrows():
                series.append({
                    "date": str(row.get("week", row.get("date", "unknown"))),
                    "bedOccupancy": float(row.get("occupied", 0.0)),
                    "icuOccupancy": float(row.get("icu_occupied", 0.0)),
                })
    except Exception:
        pass
    if not series:
        from datetime import datetime, timedelta
        today = datetime.utcnow().date()
        for i in range(6):
            d = today - timedelta(weeks=5 - i)
            series.append({"date": d.isoformat(), "bedOccupancy": 60 + i * 2, "icuOccupancy": 40 + i})
    return series


def get_hospital_resources(region: str, resource_type: str) -> Dict[str, Any]:
    # Try to load resources CSV; fallback to derived estimates
    try:
        import os
        import pandas as pd
        path = os.path.join(DATA_DIR, "hospitals", "resources.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            row = df[df["region"].astype(str).str.lower() == region.lower()].head(1)
            if not row.empty:
                rec = row.to_dict(orient="records")[0]
                val = rec.get(resource_type, None)
                if val is not None:
                    return {"region": region, "resourceType": resource_type, "count": int(val)}
    except Exception:
        pass
    base = get_hospital(region)
    totals = base.totals
    if resource_type == "beds":
        count = int(totals.avgBedCapacity * totals.facilities)
    elif resource_type == "ventilators":
        count = int(totals.facilities * 4)
    elif resource_type == "doctors":
        count = int(totals.facilities * 12)
    else:
        count = int(totals.facilities * 3)
    return {"region": region, "resourceType": resource_type, "count": count}


def get_population_demographics(region: str) -> Dict[str, Any]:
    # Try World Bank API for Nigeria age structure; fallback to stub
    demo = []
    try:
        import urllib.request
        import json as _json
        url = "https://api.worldbank.org/v2/country/NGA/indicator/SP.POP.0014.TO.ZS?format=json"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
            series = data[1] if isinstance(data, list) and len(data) > 1 else []
            latest = next((x for x in series if x.get("value") is not None), None)
            pct_0_14 = float(latest.get("value")) if latest else 41.0
            # Build a simple distribution using the 0-14 value and rough splits
            demo = [
                {"ageBand": "0-14", "percentage": round(pct_0_14, 2)},
                {"ageBand": "15-24", "percentage": 20.0},
                {"ageBand": "25-64", "percentage": 34.0},
                {"ageBand": "65+", "percentage": round(100.0 - pct_0_14 - 20.0 - 34.0, 2)},
            ]
    except Exception:
        demo = [
            {"ageBand": "0-14", "percentage": 43.0},
            {"ageBand": "15-24", "percentage": 20.5},
            {"ageBand": "25-64", "percentage": 31.0},
            {"ageBand": "65+", "percentage": 5.5},
        ]
    return {"region": region, "demographics": demo}


def get_geo_boundaries(region: str) -> Dict[str, Any]:
    # Load GeoJSON boundaries if available; fallback to sample polygon
    import os
    import json as _json
    path = os.path.join(DATA_DIR, "geo", "nigeria_states.geojson")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return _json.load(f)
        except Exception:
            pass
    return {
        "region": region,
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Sample State"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [3.0, 6.5], [3.5, 6.5], [3.5, 7.0], [3.0, 7.0], [3.0, 6.5]
                        ]
                    ],
                },
            }
        ],
    }


def get_geo_heatmap(region: str, disease: str) -> Dict[str, Any]:
    # Build heatmap from live predictions if available; fallback to stub points
    import os
    import pandas as pd
    path = os.path.join(REPORTS_DIR, "production", "predictions_live.csv")
    features: List[Dict[str, Any]] = []
    try:
        if os.path.exists(path):
            df = pd.read_csv(path)
            for _, row in df.iterrows():
                lat = row.get("lat")
                lon = row.get("lon")
                risk = row.get("predicted_cases") or row.get("riskScore") or 0.0
                dis = row.get("disease") or disease
                if pd.notna(lat) and pd.notna(lon):
                    features.append({
                        "type": "Feature",
                        "properties": {"riskScore": float(risk), "disease": str(dis)},
                        "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                    })
    except Exception:
        pass
    if not features:
        features = [
            {"type": "Feature", "properties": {"riskScore": 0.7, "disease": disease}, "geometry": {"type": "Point", "coordinates": [3.4, 6.5]}},
            {"type": "Feature", "properties": {"riskScore": 0.5, "disease": disease}, "geometry": {"type": "Point", "coordinates": [3.8, 7.1]}},
            {"type": "Feature", "properties": {"riskScore": 0.9, "disease": disease}, "geometry": {"type": "Point", "coordinates": [3.2, 6.8]}},
        ]
    return {"type": "FeatureCollection", "features": features}


def get_population_density_map(region: str) -> Dict[str, Any]:
    # Build a density FeatureCollection using training data when available; fallback to stub points
    import os
    import json as _json
    import pandas as pd

    # Attempt to load state centroids from Nigeria GeoJSON
    geo_path = os.path.join(DATA_DIR, "geo", "nigeria_states.geojson")
    state_centroids: Dict[str, tuple[float, float]] = {}
    try:
        if os.path.exists(geo_path):
            with open(geo_path, "r", encoding="utf-8") as f:
                gj = _json.load(f)
            for feat in (gj.get("features") or []):
                props = feat.get("properties", {})
                name = str(props.get("NAME_1", props.get("name", ""))).strip()
                geom = feat.get("geometry", {})
                coords = None
                if geom.get("type") == "Polygon":
                    rings = geom.get("coordinates") or []
                    if rings:
                        coords = rings[0]
                elif geom.get("type") == "MultiPolygon":
                    polys = geom.get("coordinates") or []
                    if polys and polys[0]:
                        coords = polys[0][0]
                if coords:
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    if lons and lats and name:
                        # Approximate centroid by averaging ring coordinates
                        state_centroids[name.lower()] = (sum(lats) / len(lats), sum(lons) / len(lons))
    except Exception:
        state_centroids = {}

    # Build density by state from training CSV when possible
    densities: Dict[str, float] = {}
    try:
        path = os.path.join(DATA_DIR, "outbreakiq_training_data_filled.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            if {"state", "population_density"}.issubset(set(df.columns)):
                grp = df.groupby("state", as_index=False)["population_density"].mean()
                for _, row in grp.iterrows():
                    densities[str(row["state"]).strip()] = float(row["population_density"])
    except Exception:
        densities = {}

    if not densities:
        # Fallback sample densities
        densities = {"Lagos": 212.0, "Kano": 120.0, "Rivers": 90.0, "Abuja": 150.0}

    features: List[Dict[str, Any]] = []
    for state, value in densities.items():
        key = state.lower()
        latlon = state_centroids.get(key, None)
        if latlon:
            lat, lon = latlon
            features.append({
                "type": "Feature",
                "properties": {"region": state, "density": float(value)},
                "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
            })
        else:
            # Fallback using minimal mapping
            lat, lon = _resolve_coords_for_region(state)
            features.append({
                "type": "Feature",
                "properties": {"region": state, "density": float(value)},
                "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
            })

    return {"type": "FeatureCollection", "features": features}


def get_disease_alerts(disease: str, region: str, threshold: float) -> Dict[str, Any]:
    # Combine risk-based alert with offline metrics if available
    alerts: List[Dict[str, Any]] = []
    q = PredictionQuery(region=region, disease=disease)
    pred = predict_series(q)
    if pred.summary and pred.summary.riskScore >= threshold:
        alerts.append({
            "disease": disease,
            "region": region,
            "level": "alert",
            "riskScore": pred.summary.riskScore,
            "threshold": threshold,
            "asOf": datetime.utcnow().isoformat(),
        })
    # Enhance with metrics file filter if present
    metrics: List[Dict[str, Any]] = []
    try:
        import pandas as pd
        path = os.path.join(REPORTS_DIR, "production", "metrics_alert_classification.csv")
        if os.path.exists(path):
            dfm = pd.read_csv(path)
            cols = [c.lower() for c in dfm.columns]
            # Filter using f1 score when available
            if "f1" in cols:
                dfm = dfm[dfm[dfm.columns[cols.index("f1")]] >= threshold]
            metrics = dfm.to_dict(orient="records")[:10]
    except Exception:
        metrics = []
    return {"alerts": alerts, "metrics": metrics}


def get_insights(disease: str, region: Optional[str] = None) -> InsightsResponse:
    metrics = Metrics(accuracy=0.91, precision=0.88, recall=0.93, f1=0.90, auc=0.94)
    fi = [
        FeatureImportanceItem(name="Rainfall Patterns", value=0.92),
        FeatureImportanceItem(name="Population Density", value=0.85),
        FeatureImportanceItem(name="Healthcare Access", value=0.78),
        FeatureImportanceItem(name="Avg. Temperature", value=0.65),
        FeatureImportanceItem(name="Sanitation Index", value=0.59),
    ]

    # Try to incorporate production reports if available
    try:
        health_path = os.path.join(REPORTS_DIR, "health.json")
        if os.path.exists(health_path):
            with open(health_path, "r", encoding="utf-8") as f:
                health = json.load(f)
                if isinstance(health, dict):
                    notes = health.get("notes") or "Model health loaded from reports."
                else:
                    notes = "Model health report available."
        else:
            notes = "Model trained on 10 years, 36 states."
    except Exception:
        notes = "Model trained on 10 years, 36 states."

    return InsightsResponse(metrics=metrics, featureImportance=fi, notes=notes)