from fastapi import APIRouter, Query
from app.models.predictions import PredictionResponse, PredictionQuery
from app.services.ml import predict_series, get_disease_alerts as svc_get_disease_alerts
from datetime import datetime
import os
import pandas as pd
from app.core.config import DATA_DIR


router = APIRouter(prefix="/disease", tags=["disease"])


@router.get("/current/{disease}", response_model=PredictionResponse)
def get_disease_current(disease: str, region: str = Query("All")):
    q = PredictionQuery(region=region, disease=disease)
    return predict_series(q)


@router.get("/{disease}/region/{region}", response_model=PredictionResponse)
def get_disease_by_region(disease: str, region: str):
    q = PredictionQuery(region=region, disease=disease)
    return predict_series(q)


@router.get("/historical")
def get_disease_historical(disease: str = Query("cholera"), region: str = Query("All"), window: int = Query(30)):
    # Return recent historical cases for disease/region
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
                items.append({"date": date, "cases": float(row.get("cases", 0.0))})
        except Exception:
            pass
    return {"region": region, "disease": disease, "history": items}


@router.get("/alerts")
def get_disease_alerts(disease: str = Query("cholera"), region: str = Query("All"), threshold: float = Query(0.7)):
    return svc_get_disease_alerts(disease=disease, region=region, threshold=threshold)