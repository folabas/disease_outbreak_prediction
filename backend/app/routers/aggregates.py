from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Query, HTTPException
import os
import pandas as pd

from app.core.config import DATA_DIR, ALLOWED_DISEASES
from app.services.ml import PredictionQuery, predict_series
from app.core.response import success
from app.core.validators import validate_region


router = APIRouter()


@router.get("/charts/predicted-actual")
def get_predicted_vs_actual(
    disease: str = Query("cholera"),
    region: str = Query("All"),
    window: int = Query(30, ge=1, le=365),
) -> Dict[str, Any]:
    """
    Merge historical actual cases with predicted series for charting.
    Returns a unified timeseries array with keys: date, actual (optional), predicted (optional),
    and a flag `live_only` when no historical data is present.
    """
    if disease not in ALLOWED_DISEASES:
        raise HTTPException(status_code=400, detail=f"Unsupported disease: {disease}")

    # Validate region string
    region = validate_region(region) or "All"
    # Fetch predictions via ML service
    q = PredictionQuery(region=region, disease=disease, window=window)
    pred = predict_series(q)

    # Try to load historical actuals
    df_path = os.path.join(DATA_DIR, "outbreakiq_training_data_filled.csv")
    actuals: List[Dict[str, Any]] = []
    live_only = False
    try:
        if os.path.exists(df_path):
            df = pd.read_csv(df_path)
            if "disease" in df.columns and disease:
                df = df[df["disease"].astype(str).str.lower() == disease.lower()]
            if "state" in df.columns:
                if region and region != "All":
                    df = df[df["state"].astype(str).str.lower() == region.lower()]
                else:
                    if any(df["state"].astype(str).str.lower() == "all"):
                        df = df[df["state"].astype(str).str.lower() == "all"]

            sort_cols = [c for c in ["year", "week"] if c in df.columns]
            if sort_cols:
                df = df.sort_values(sort_cols).reset_index(drop=True)
            for _, row in df.tail(min(window, 50)).iterrows():
                date = None
                if "date" in df.columns:
                    date = str(row.get("date"))
                elif all(c in df.columns for c in ["year", "week"]):
                    date = f"{int(row.get('year'))}-W{int(row.get('week'))}"
                else:
                    date = "unknown"
                try:
                    cases = float(row.get("cases", 0.0))
                except Exception:
                    cases = 0.0
                actuals.append({"date": date, "actual": cases})
        else:
            live_only = True
    except Exception:
        live_only = True

    # Build merged series: prepend actuals, then predicted points
    series: List[Dict[str, Any]] = []
    series.extend(actuals)
    for tp in pred.timeseries or []:
        series.append({"date": tp.date, "predicted": tp.predicted, "actual": tp.actual})

    return success({
        "region": region,
        "disease": disease,
        "series": series,
        "live_only": live_only,
    })