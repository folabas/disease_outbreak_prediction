from fastapi import APIRouter, Query
from app.models.climate import ClimateQuery, ClimateResponse
from app.services.ml import get_climate


router = APIRouter(prefix="/climate", tags=["climate"])


@router.get("/", response_model=ClimateResponse)
def get_climate_series(
    region: str = Query("All"),
    disease: str = Query("cholera"),
):
    q = ClimateQuery(region=region, disease=disease)
    return get_climate(q)