from fastapi import APIRouter, Query
import logging
from app.models.insights import InsightsResponse
from app.core.response import success
from app.services.ml import get_insights
import os
import pandas as pd
from app.core.config import DATA_DIR


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/insights", response_model=InsightsResponse)
def get_analytics_insights(disease: str = Query("cholera", regex="^(cholera|malaria)$"), region: str | None = Query(None)):
    logging.info("/analytics/insights GET disease=%s region=%s", disease, region)
    return success(get_insights(disease=disease, region=region).dict())


@router.get("/hotspots")
def get_hotspots(disease: str = Query("cholera", regex="^(cholera|malaria)$"), top_n: int = Query(5, ge=1, le=20)):
    logging.info("/analytics/hotspots GET disease=%s top_n=%s", disease, top_n)
    # Compute top regions by average recent cases from training data
    df_path = os.path.join(DATA_DIR, "outbreakiq_training_data_filled.csv")
    hotspots = []
    if os.path.exists(df_path):
        try:
            df = pd.read_csv(df_path)
            if "disease" in df.columns and disease:
                df = df[df["disease"].astype(str).str.lower() == disease.lower()]
            if "state" in df.columns and "cases" in df.columns:
                grp = df.groupby("state", as_index=False)["cases"].mean()
                grp = grp.sort_values("cases", ascending=False)
                for _, row in grp.head(top_n).iterrows():
                    hotspots.append({"region": str(row["state"]), "score": float(row["cases"])})
        except Exception:
            pass
    # Fallback stub
    if not hotspots:
        hotspots = [
            {"region": "Lagos", "score": 0.9},
            {"region": "Kano", "score": 0.8},
            {"region": "Rivers", "score": 0.7},
        ]
    return success({"disease": disease, "hotspots": hotspots})