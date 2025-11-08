from fastapi import APIRouter, Query
from app.models.predictions import PredictionQuery, PredictionResponse
from app.services.ml import predict_series


router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/", response_model=PredictionResponse)
def get_predictions(
    region: str = Query("All"),
    disease: str = Query("cholera"),
    window: int = Query(14, ge=1, le=180),
):
    q = PredictionQuery(region=region, disease=disease, window=window)
    return predict_series(q)