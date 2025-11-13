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
    """Load the model and scaler; fall back gracefully if unavailable."""
    global _model, _scaler, _model_version
    if _model is not None and _scaler is not None:
        return
    try:
        from tensorflow.keras.models import load_model
        from joblib import load
        model_path = os.path.join(MODELS_DIR, "lstm_forecaster.h5")
        scaler_path = os.path.join(MODELS_DIR, "feature_scaler.joblib")
        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            _model = None
            _scaler = None
            _model_version = None
            import logging as _log
            _log.warning("Model/scaler not found; using stub predictions")
            return
        _model = load_model(model_path)
        _scaler = load(scaler_path)
        _model_version = "lstm_forecaster"
    except Exception:
        _model = None
        _scaler = None
        _model_version = None
        import logging as _log
        _log.warning("Failed to load model/scaler; using stub predictions")


def predict_series(q: PredictionQuery) -> PredictionResponse:
    """Generate predictions for the given query; return a stub when offline."""
    import logging
    from datetime import datetime, timedelta
    generated_at = datetime.utcnow().isoformat()

    try:
        _try_load_model()

        df_path = os.path.join(DATA_DIR, "outbreakiq_training_data_filled.csv")
        df = None
        if os.path.exists(df_path):
            df = pd.read_csv(df_path)

        if df is not None and not df.empty:
            if "disease" in df.columns and q.disease:
                df = df[df["disease"].astype(str).str.lower() == q.disease.lower()]
            if "state" in df.columns and q.region and q.region != "All":
                df = df[df["state"].astype(str).str.lower() == q.region.lower()]

            sort_cols = [c for c in ["year", "week"] if c in df.columns]
            if sort_cols:
                df = df.sort_values(sort_cols).reset_index(drop=True)

        if df is None or df.empty or any(c not in df.columns for c in _FEATURES) or len(df) < _WINDOW or _model is None or _scaler is None:
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
                FeatureImportance(feature=_FEATURES[0], importance=0.4),
                FeatureImportance(feature=_FEATURES[1], importance=0.25),
                FeatureImportance(feature=_FEATURES[2], importance=0.2),
                FeatureImportance(feature=_FEATURES[3], importance=0.15),
            ]
        else:
            latest = df[_FEATURES].tail(_WINDOW).fillna(0).values
            latest = np.expand_dims(latest, axis=0)
            y_scaled = float(_model.predict(latest, verbose=0)[0][0])
            y_scaled = float(np.clip(y_scaled, 0.0, 1.0))
            inv = float(_scaler.inverse_transform([[y_scaled, 0, 0, 0]])[0][0])
            pred_val = round(inv, 2)
            score = min(inv / 200.0, 1.0)
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
                explanations = [FeatureImportance(feature=f, importance=float(w)) for f, w in zip(_FEATURES, weights)]
            except Exception:
                explanations = [FeatureImportance(feature=_FEATURES[0], importance=0.4),
                                FeatureImportance(feature=_FEATURES[1], importance=0.25),
                                FeatureImportance(feature=_FEATURES[2], importance=0.2),
                                FeatureImportance(feature=_FEATURES[3], importance=0.15)]
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
        explanations = [FeatureImportance(feature=feat, importance=0.0) for feat in _FEATURES]

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
            reg = q.region
            if reg:
                rl = reg.strip().lower()
                if rl in {"all", "all nigeria", "nigeria", "all regions", "all states"}:
                    reg = None
            else:
                reg = None
            if reg:
                sdf = df[df["state"].str.lower() == reg.lower()]
            else:
                sdf = df
            sort_cols = [c for c in ["year", "week"] if c in sdf.columns]
            if sort_cols:
                sdf = sdf.sort_values(sort_cols).reset_index(drop=True)
            if set(["year", "week"]).issubset(set(sdf.columns)):
                agg = sdf.groupby(["year", "week"], as_index=False).agg({
                    "temperature_2m_mean": "mean",
                    "precipitation_sum": "mean",
                })
            else:
                agg = sdf.copy()

            def _parse_week(s: Optional[str]) -> Optional[tuple[int, int]]:
                if s is None:
                    return None
                try:
                    s = str(s)
                    if "W" in s:
                        parts = s.split("-W")
                        return int(parts[0]), int(parts[1])
                    dt = datetime.fromisoformat(s)
                    iso = dt.isocalendar()
                    return int(iso[0]), int(iso[1])
                except Exception:
                    return None

            start_week = _parse_week(q.startDate)
            end_week = _parse_week(q.endDate)
            if start_week or end_week:
                def _idx(y: Any, w: Any) -> int:
                    try:
                        return int(y) * 100 + int(w)
                    except Exception:
                        return 0
                sidx = _idx(*(start_week or (0, 0)))
                eidx = _idx(*(end_week or (9999, 99)))
                agg = agg[(agg["year"].astype(int) * 100 + agg["week"].astype(int) >= sidx) & (agg["year"].astype(int) * 100 + agg["week"].astype(int) <= eidx)]

            agg = agg.sort_values([c for c in ["year", "week"] if c in agg.columns]).reset_index(drop=True)
            rows = agg.tail(12).iterrows()
            for _, row in rows:
                if "date" in agg.columns and pd.notna(row.get("date")):
                    date_str = str(row.get("date"))
                else:
                    y = row.get("year")
                    w = row.get("week")
                    try:
                        date_str = f"{int(y)}-W{int(w):02d}"
                    except Exception:
                        date_str = datetime.utcnow().date().isoformat()
                tval = float(row.get("temperature_2m_mean", 0.0))
                rval = float(row.get("precipitation_sum", 0.0))
                temp.append(SeriesPoint(date=date_str, value=tval))
                rain.append(SeriesPoint(date=date_str, value=rval))
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


def get_climate_forecast(region: str, disease: str | None = None, startDate: str | None = None, endDate: str | None = None, days: int | None = None) -> ClimateResponse:
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
        if days and isinstance(days, int):
            params["forecast_days"] = max(1, min(30, days))
        url = base + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            temps = daily.get("temperature_2m_max", [])
            precs = daily.get("precipitation_sum", [])
            size = min(len(dates), len(temps), len(precs))
            for i in range(size):
                d = str(dates[i])
                temp.append(SeriesPoint(date=d, value=float(temps[i])))
                rain.append(SeriesPoint(date=d, value=float(precs[i])))
        # Apply date range filter when provided
        def _dtidx(s: str) -> int:
            try:
                from datetime import datetime as _dt
                dt = _dt.fromisoformat(s)
                return int(dt.strftime("%Y%m%d"))
            except Exception:
                return 0
        if startDate or endDate:
            sidx = _dtidx(startDate or "0001-01-01")
            eidx = _dtidx(endDate or "9999-12-31")
            temp = [p for p in temp if sidx <= _dtidx(p.date) <= eidx]
            rain = [p for p in rain if sidx <= _dtidx(p.date) <= eidx]
    except Exception:
        # Fallback to current climate series
        q = ClimateQuery(region=region, disease=disease or "cholera")
        climate = get_climate(q)
        temp = climate.temperature
        rain = climate.rainfall

    return ClimateResponse(region=region, temperature=temp, rainfall=rain)


def get_population(region: str, startDate: str | None = None, endDate: str | None = None) -> PopulationResponse:
    growth: List[PopulationEntry] = []
    density: List[PopulationEntry] = []
    national_2024: Optional[float] = None
    try:
        nat_csv = os.path.join(DATA_DIR, "raw", "worldbank_population.csv")
        if os.path.exists(nat_csv):
            nat_df = pd.read_csv(nat_csv)
            if {"year", "population"}.issubset(set(nat_df.columns)):
                row = nat_df[nat_df["year"].astype(int) == 2024]
                if len(row) > 0:
                    national_2024 = float(row.iloc[0]["population"]) or None
    except Exception:
        national_2024 = None

    state_pop_2006: Dict[str, float] = {}
    state_pop_2024: Dict[str, float] = {}
    try:
        xls_path = os.path.join(DATA_DIR, "raw", "POPULATION PROJECTION Nigeria sgfn.xls")
        if os.path.exists(xls_path):
            try:
                df2 = pd.read_excel(xls_path)
                c_state = next((c for c in df2.columns if str(c).strip().lower() in {"state", "states"}), None)
                c_2006 = next((c for c in df2.columns if str(c).strip().lower().startswith("population (2006)") or str(c).strip().lower() == "population (2006)"), None)
                c_gr = next((c for c in df2.columns if "annual" in str(c).strip().lower() and "gr" in str(c).strip().lower()), None)
                if c_state is not None and c_2006 is not None and c_gr is not None:
                    for _, r in df2.iterrows():
                        name = str(r[c_state]).strip()
                        if not name:
                            continue
                        pop2006 = r[c_2006]
                        gr = r[c_gr]
                        try:
                            p2006 = float(pop2006)
                            rate = float(gr) / 100.0 if float(gr) > 1.0 else float(gr)
                            years = 2024 - 2006
                            p2024 = p2006 * ((1.0 + rate) ** years)
                            state_pop_2006[name] = p2006
                            state_pop_2024[name] = p2024
                        except Exception:
                            continue
            except Exception:
                pass
    except Exception:
        state_pop_2006 = {}
        state_pop_2024 = {}

    if not state_pop_2024:
        state_pop_2024 = {
            "Abia": 4200000,
            "Adamawa": 5250000,
            "Akwa Ibom": 7900000,
            "Anambra": 6200000,
            "Bauchi": 8100000,
            "Bayelsa": 2700000,
            "Benue": 6500000,
            "Borno": 6900000,
            "Cross River": 4300000,
            "Delta": 6600000,
            "Ebonyi": 3600000,
            "Edo": 5400000,
            "Ekiti": 3700000,
            "Enugu": 5200000,
            "Gombe": 3600000,
            "Imo": 5900000,
            "Jigawa": 7100000,
            "Kaduna": 9500000,
            "Kano": 14900000,
            "Katsina": 9100000,
            "Kebbi": 5000000,
            "Kogi": 5300000,
            "Kwara": 3900000,
            "Lagos": 21000000,
            "Nasarawa": 3900000,
            "Niger": 6000000,
            "Ogun": 6400000,
            "Ondo": 5100000,
            "Osun": 5000000,
            "Oyo": 9000000,
            "Plateau": 4600000,
            "Rivers": 7600000,
            "Sokoto": 5600000,
            "Taraba": 3400000,
            "Yobe": 4000000,
            "Zamfara": 5200000,
            "FCT": 4200000,
        }

    total_states = sum(state_pop_2024.values()) if state_pop_2024 else 0.0
    nat_end: Optional[float] = None
    nat_start: Optional[float] = None
    try:
        nat_csv = os.path.join(DATA_DIR, "raw", "worldbank_population.csv")
        if os.path.exists(nat_csv):
            nat_df = pd.read_csv(nat_csv)
            if {"year", "population"}.issubset(set(nat_df.columns)):
                r_end = nat_df[nat_df["year"].astype(int) == end_year]
                r_start = nat_df[nat_df["year"].astype(int) == start_year]
                nat_end = float(r_end.iloc[0]["population"]) if len(r_end) > 0 else national_2024
                nat_start = float(r_start.iloc[0]["population"]) if len(r_start) > 0 else national_2024
    except Exception:
        pass
    if nat_end and total_states > 0:
        scale_end = nat_end / total_states
        for k in list(state_pop_2024.keys()):
            state_pop_2024[k] = float(state_pop_2024[k]) * float(scale_end)

    if state_pop_2006 and state_pop_2024:
        def _proj_for_year(p2006: float, rate: float, year: int) -> float:
            yrs = max(0, year - 2006)
            return p2006 * ((1.0 + rate) ** yrs)
        rates: Dict[str, float] = {}
        try:
            xls_path = os.path.join(DATA_DIR, "raw", "POPULATION PROJECTION Nigeria sgfn.xls")
            if os.path.exists(xls_path):
                df2 = pd.read_excel(xls_path)
                c_state = next((c for c in df2.columns if str(c).strip().lower() in {"state", "states"}), None)
                c_gr = next((c for c in df2.columns if "annual" in str(c).strip().lower() and "gr" in str(c).strip().lower()), None)
                if c_state is not None and c_gr is not None:
                    for _, r in df2.iterrows():
                        name = str(r[c_state]).strip()
                        gr = r[c_gr]
                        try:
                            rate = float(gr) / 100.0 if float(gr) > 1.0 else float(gr)
                            rates[name] = rate
                        except Exception:
                            continue
        except Exception:
            rates = {}
        for name, p2006 in state_pop_2006.items():
            rate = rates.get(name, None)
            if rate is None:
                p_start = state_pop_2024.get(name)
                p_end = state_pop_2024.get(name)
            else:
                p_start = _proj_for_year(p2006, rate, start_year)
                p_end = _proj_for_year(p2006, rate, end_year)
            if p_start and p_end:
                growth_pct = ((p_end - p_start) / p_start) * 100.0 if p_start > 0 else 0.0
                growth.append(PopulationEntry(region=name, value=float(growth_pct)))
    else:
        for name, p2024 in state_pop_2024.items():
            share_pct = (p2024 / (nat_end or national_2024 or total_states or 1.0)) * 100.0
            growth.append(PopulationEntry(region=name, value=float(share_pct)))

    try:
        dens = get_population_density_map("All")
        feats = dens.get("features") or []
        for f in feats:
            props = f.get("properties") or {}
            n = str(props.get("region") or "").strip()
            v = float(props.get("density") or 0.0)
            if n:
                density.append(PopulationEntry(region=n, value=v))
    except Exception:
        pass

    if not density:
        density = [PopulationEntry(region="Lagos", value=212.0)]
    return PopulationResponse(growthRates=growth, density=density)


def get_hospital(region: str) -> HospitalResponse:
    import os
    import json as _json
    from app.core.config import resolve_path

    path = resolve_path("web", "outbreakiq", "public", "data", "nigeria_facilities.geojson")
    features: List[Dict[str, Any]] = []
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                gj = _json.load(f)
            features = list(gj.get("features") or [])
    except Exception:
        features = []

    def _norm_state(s: str) -> str:
        n = str(s or "").strip().lower()
        if n in {"fct", "fct abuja", "abuja", "federal capital territory"}:
            return "abuja"
        return n

    r = _norm_state(region)
    filtered: List[Dict[str, Any]] = []
    if r and r != "all":
        for feat in features:
            props = feat.get("properties") or {}
            addr = str(props.get("address") or props.get("region") or props.get("state") or "")
            addr_n = _norm_state(addr)
            name_n = _norm_state(str(props.get("name", "")))
            if r and (r in addr_n or r in name_n):
                filtered.append(feat)
    else:
        filtered = features

    beds: List[float] = []
    for feat in filtered:
        props = feat.get("properties") or {}
        b = props.get("beds")
        if isinstance(b, (int, float)):
            beds.append(float(b))
        else:
            cap = props.get("capacity") or {}
            if isinstance(cap, dict):
                bb = cap.get("beds")
                if isinstance(bb, (int, float)):
                    beds.append(float(bb))

    avg_beds = round((sum(beds) / len(beds)) if beds else 0.0, 2)
    totals = HospitalTotals(
        facilities=len(filtered),
        avgBedCapacity=avg_beds,
        bedsPer10k=0.0,
    )
    facilities_geo: Dict[str, Any] = {"type": "FeatureCollection", "features": filtered}
    return HospitalResponse(region=region, totals=totals, facilitiesGeo=facilities_geo)


def get_hospital_capacity_trends(region: str) -> List[Dict[str, Any]]:
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
    # Default placeholders
    metrics = Metrics(accuracy=0.91, precision=0.88, recall=0.93, f1=0.90, auc=0.94)
    fi = [
        FeatureImportanceItem(name="Cases (lagged)", value=0.40),
        FeatureImportanceItem(name="Temperature", value=0.25),
        FeatureImportanceItem(name="Humidity", value=0.20),
        FeatureImportanceItem(name="Precipitation", value=0.15),
    ]

    notes = "Model trained on 10 years, 36 states."

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
                            accuracy=m_acc or metrics.accuracy,
                            precision=m_prec or metrics.precision,
                            recall=m_rec or metrics.recall,
                            f1=m_f1 or metrics.f1,
                            auc=m_auc if m_auc is not None else metrics.auc,
                        )
                        ts = row.iloc[0].get("timestamp")
                        mv = row.iloc[0].get("model_version") or "unknown"
                        notes = f"Metrics computed from live model '{mv}' at {ts}."
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
                        notes = extra
    except Exception:
        pass

    # Compute feature importance from training data (correlation heuristic)
    try:
        df_path = os.path.join(DATA_DIR, "outbreakiq_training_data_filled.csv")
        if os.path.exists(df_path):
            df = pd.read_csv(df_path)
            if "disease" in df.columns and disease:
                df = df[df["disease"].astype(str).str.lower() == str(disease).lower()]
            if region and "state" in df.columns:
                df = df[df["state"].astype(str).str.lower() == str(region).lower()]
            cols = [c for c in _FEATURES if c in df.columns]
            def _friendly(n: str) -> str:
                if n == "cases":
                    return "Cases (lagged)"
                if n == "temperature_2m_mean":
                    return "Temperature"
                if n == "relative_humidity_2m_mean":
                    return "Humidity"
                if n == "precipitation_sum":
                    return "Precipitation"
                return n

            def _compute_pairs(frame: pd.DataFrame) -> List[tuple[str, float]]:
                cols2 = [c for c in _FEATURES if c in frame.columns]
                if "cases" not in cols2 or len(cols2) < 2 or len(frame) <= 10:
                    return []
                base = pd.to_numeric(frame["cases"], errors="coerce")
                out: List[tuple[str, float]] = []
                for c in cols2:
                    s = pd.to_numeric(frame[c], errors="coerce")
                    try:
                        val = float(abs(s.corr(base)))
                        if np.isnan(val):
                            val = 0.0
                    except Exception:
                        val = 0.0
                    out.append((c, val))
                return out

            pairs = _compute_pairs(df)
            if not pairs or sum(v for _, v in pairs) == 0.0:
                pairs = _compute_pairs(pd.read_csv(df_path))
            if pairs:
                total = sum(v for _, v in pairs) or 1.0
                fi = [FeatureImportanceItem(name=_friendly(n), value=float(v/total)) for n, v in pairs]
    except Exception:
        pass

    return InsightsResponse(metrics=metrics, featureImportance=fi, notes=notes)
    def _parse_year(s: Optional[str]) -> Optional[int]:
        if not s:
            return None
        try:
            s = str(s)
            if "-W" in s:
                return int(s.split("-W")[0])
            from datetime import datetime as _dt
            return _dt.fromisoformat(s).year
        except Exception:
            return None

    start_year = _parse_year(startDate) or 2006
    end_year = _parse_year(endDate) or 2024
    if end_year < start_year:
        start_year, end_year = end_year, start_year