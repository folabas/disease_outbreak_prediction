from fastapi import APIRouter, Query, HTTPException
import logging
from app.models.predictions import PredictionResponse, PredictionQuery
from app.services.ml import predict_series, get_disease_alerts as svc_get_disease_alerts
from datetime import datetime
import os
import pandas as pd
from app.core.config import DATA_DIR, ALLOWED_DISEASES
from app.core.response import success
from app.core.validators import validate_region, validate_disease


router = APIRouter(prefix="/disease", tags=["disease"])


@router.get("/current/{disease}")
def get_disease_current(disease: str, region: str = Query("All")):
    logging.info("/disease/current/%s GET region=%s", disease, region)
    disease = validate_disease(disease) or disease
    region = validate_region(region) or "All"
    q = PredictionQuery(region=region, disease=disease)
    return success(predict_series(q).dict())


@router.get("/{disease}/region/{region}")
def get_disease_by_region(disease: str, region: str):
    logging.info("/disease/%s/region/%s GET", disease, region)
    disease = validate_disease(disease) or disease
    region = validate_region(region) or region
    q = PredictionQuery(region=region, disease=disease)
    return success(predict_series(q).dict())


@router.get("/historical")
def get_disease_historical(disease: str = Query("cholera"), region: str = Query("All"), window: int = Query(30)):
    logging.info("/disease/historical GET disease=%s region=%s window=%s", disease, region, window)
    # Return recent historical cases for disease/region
    disease = validate_disease(disease) or disease
    region = validate_region(region) or "All"
    df_path = os.path.join(DATA_DIR, "outbreakiq_training_data_filled.csv")
    items = []
    if os.path.exists(df_path):
        try:
            df = pd.read_csv(df_path)
            if "disease" in df.columns and disease:
                df = df[df["disease"].astype(str).str.lower() == disease.lower()]
            if "state" in df.columns:
                if region and region != "All":
                    df = df[df["state"].astype(str).str.lower() == region.lower()]
                else:
                    if any(df["state"].astype(str).str.lower() == "all"):
                        df = df[df["state"].astype(str).str.lower() == "all"]
            # Aggregate by week across states to represent region-level confirmed cases
            agg_cols = [c for c in ["year", "week", "cases"] if c in df.columns]
            if all(c in agg_cols for c in ["year", "week", "cases"]):
                df = df.groupby(["year", "week"], as_index=False)["cases"].sum()
            sort_cols = [c for c in ["year", "week"] if c in df.columns]
            if sort_cols:
                df = df.sort_values(sort_cols).reset_index(drop=True)
            tail_n = min(window, 50)
            for _, row in df.tail(tail_n).iterrows():
                date = None
                if "date" in df.columns:
                    date = str(row.get("date"))
                elif all(c in df.columns for c in ["year", "week"]):
                    date = f"{int(row.get('year'))}-W{int(row.get('week'))}"
                else:
                    date = "unknown"
                items.append({"date": date, "cases": float(row.get("cases", 0.0))})
        except Exception:
            pass
    return success({"region": region, "disease": disease, "history": items})


@router.get("/alerts")
def get_disease_alerts(disease: str = Query("cholera"), region: str = Query("All"), threshold: float = Query(0.7)):
    logging.info("/disease/alerts GET disease=%s region=%s threshold=%s", disease, region, threshold)
    disease = validate_disease(disease) or disease
    region = validate_region(region) or "All"
    return success(svc_get_disease_alerts(disease=disease, region=region, threshold=threshold))