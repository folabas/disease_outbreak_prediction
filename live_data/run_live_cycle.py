from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict, Tuple, List

import pandas as pd

from ml.utils import load_training, ensure_reports_dir, next_week


# Configuration aligned with deep model training
WINDOW_SIZE = 8
FEATURES = [
    "cases",
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "precipitation_sum",
]
MODEL_PATH = Path("models/lstm_forecaster.h5")
FEATURE_SCALER_PATH = Path("models/feature_scaler.joblib")
TARGET_SCALER_PATH = Path("models/target_scaler.joblib")
GEOJSON_PATH = Path("data/geo/nigeria_states.geojson")


def _try_load_model_and_scalers():
    try:
        from tensorflow.keras.models import load_model
        model = load_model(MODEL_PATH)
    except Exception as e:
        raise RuntimeError(f"Deep model not available at {MODEL_PATH}: {e}")

    feature_scaler = None
    target_scaler = None
    try:
        from joblib import load as joblib_load
        feature_scaler = joblib_load(FEATURE_SCALER_PATH)
        target_scaler = joblib_load(TARGET_SCALER_PATH)
    except Exception:
        # Scalers optional; proceed without if missing
        pass
    return model, feature_scaler, target_scaler


def _compute_state_centroids(geojson_path: Path) -> Dict[str, Tuple[float, float]]:
    centroids: Dict[str, Tuple[float, float]] = {}
    try:
        with geojson_path.open("r", encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj.get("features", []):
            props = feat.get("properties", {})
            # Use GADM NAME_1 field for state name
            name = str(props.get("NAME_1") or props.get("name") or props.get("state") or "").strip()
            geom = feat.get("geometry", {})
            coords = []
            if geom.get("type") == "Polygon":
                for ring in geom.get("coordinates", []):
                    coords.extend(ring)
            elif geom.get("type") == "MultiPolygon":
                for poly in geom.get("coordinates", []):
                    for ring in poly:
                        coords.extend(ring)
            if name and coords:
                # Simple centroid: average lon/lat
                lon_sum = sum(c[0] for c in coords)
                lat_sum = sum(c[1] for c in coords)
                n = max(1, len(coords))
                centroids[name.lower()] = (lat_sum / n, lon_sum / n)
    except Exception:
        # If centroid computation fails, return empty and downstream will omit lat/lon
        pass
    return centroids


def run_realtime_predictions() -> Path:
    df = load_training()
    reports_dir = ensure_reports_dir()

    # Latest week per (state, disease)
    latest = df.sort_values(["disease", "state", "year", "week"]).groupby(["disease", "state"]).tail(1).copy()
    latest["pred_cases_next_week"] = latest["cases"].fillna(0)
    latest["pred_deaths_next_week"] = latest["deaths"].fillna(0)

    nxt = latest.apply(lambda r: pd.Series(next_week(int(r["year"]), int(r["week"]))), axis=1)
    nxt.columns = ["pred_year", "pred_week"]
    latest = pd.concat([latest.reset_index(drop=True), nxt], axis=1)

    out = reports_dir / "predictions_live.csv"
    cols = [
        "state", "disease", "pred_year", "pred_week", "pred_cases_next_week", "pred_deaths_next_week",
    ]
    latest[cols].to_csv(out, index=False)

    health = {
        "timestamp": int(time.time()),
        "status": "ok",
        "predictions": int(len(latest)),
        "mode": "realtime_stub",
    }
    (reports_dir / "health.json").write_text(pd.Series(health).to_json(indent=2), encoding="utf-8")
    return out


def run_deep_predictions() -> Path:
    df = load_training()
    reports_dir = ensure_reports_dir()
    model, feature_scaler, target_scaler = _try_load_model_and_scalers()
    centroids = _compute_state_centroids(GEOJSON_PATH)

    rows: List[Dict] = []
    # Iterate each (disease, state) group and predict next week if enough history
    for (disease, state), group in df.groupby(["disease", "state"]):
        group = group.sort_values(["year", "week"]).reset_index(drop=True)
        if len(group) < WINDOW_SIZE:
            continue
        seq = group[FEATURES].tail(WINDOW_SIZE).values
        # Scale features if matching
        n_features = seq.shape[1]
        if feature_scaler is not None and getattr(feature_scaler, "n_features_in_", n_features) == n_features:
            try:
                seq_scaled = feature_scaler.transform(seq.reshape(-1, n_features)).reshape(1, WINDOW_SIZE, n_features)
            except Exception:
                seq_scaled = seq.reshape(1, WINDOW_SIZE, n_features)
        else:
            seq_scaled = seq.reshape(1, WINDOW_SIZE, n_features)

        # Predict scaled value and inverse-transform if target scaler available
        try:
            pred_scaled = float(model.predict(seq_scaled, verbose=0)[0][0])
        except Exception:
            continue

        pred_cases = pred_scaled
        if target_scaler is not None:
            try:
                import numpy as np
                pred_cases = float(target_scaler.inverse_transform(np.array([[pred_scaled]]))[0][0])
            except Exception:
                pred_cases = pred_scaled
        if pred_cases < 0:
            pred_cases = 0.0

        # Next week
        year = int(group.iloc[-1]["year"]) if "year" in group.columns else 0
        week = int(group.iloc[-1]["week"]) if "week" in group.columns else 0
        pred_year, pred_week = next_week(year, week)

        lat, lon = None, None
        key = str(state).lower()
        if key in centroids:
            lat, lon = centroids[key]

        rows.append({
            "state": state,
            "disease": disease,
            "pred_year": pred_year,
            "pred_week": pred_week,
            "predicted_cases": round(float(pred_cases), 6),
            "lat": lat,
            "lon": lon,
        })

    out = reports_dir / "predictions_live.csv"
    pd.DataFrame(rows).to_csv(out, index=False)

    health = {
        "timestamp": int(time.time()),
        "status": "ok",
        "predictions": int(len(rows)),
        "mode": "deep_lstm",
    }
    (reports_dir / "health.json").write_text(pd.Series(health).to_json(indent=2), encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="deep", choices=["realtime", "deep"], help="Run predictions mode")
    args = parser.parse_args()
    if args.mode == "realtime":
        out = run_realtime_predictions()
        print(f"Predictions written to: {out}")
    elif args.mode == "deep":
        out = run_deep_predictions()
        print(f"Predictions written to: {out}")


if __name__ == "__main__":
    main()