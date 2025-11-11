from fastapi import APIRouter, Query
from app.models.insights import InsightsResponse
from app.services.ml import get_insights


router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/", response_model=InsightsResponse)
def get_model_insights(
    disease: str = Query("cholera"),
    region: str | None = Query(None),
):
    return get_insights(disease=disease, region=region)