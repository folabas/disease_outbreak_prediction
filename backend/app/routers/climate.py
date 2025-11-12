from fastapi import APIRouter, Query
from app.models.climate import ClimateQuery, ClimateResponse
from app.services.ml import get_climate, get_climate_forecast as svc_get_climate_forecast


router = APIRouter(prefix="/climate", tags=["climate"])


@router.get("/", response_model=ClimateResponse)
def get_climate_series(
    region: str = Query("All"),
    disease: str = Query("cholera", regex="^(cholera|malaria)$"),
):
    q = ClimateQuery(region=region, disease=disease)
    return get_climate(q)


@router.get("/current/{region}", response_model=ClimateResponse)
def get_current_climate(region: str, disease: str = Query("cholera", regex="^(cholera|malaria)$")):
    q = ClimateQuery(region=region, disease=disease)
    return get_climate(q)


# Alias to support /climate/region/{region}
@router.get("/region/{region}", response_model=ClimateResponse)
def get_climate_by_region(region: str, disease: str = Query("cholera", regex="^(cholera|malaria)$")):
    q = ClimateQuery(region=region, disease=disease)
    return get_climate(q)


@router.get("/historical", response_model=ClimateResponse)
def get_climate_historical(
    region: str = Query("All"),
    disease: str = Query("cholera", regex="^(cholera|malaria)$"),
):
    # For now, reuse get_climate which returns recent series; can be extended to longer history
    q = ClimateQuery(region=region, disease=disease)
    return get_climate(q)


@router.get("/forecast/{region}", response_model=ClimateResponse)
def get_climate_forecast(region: str, disease: str = Query("cholera", regex="^(cholera|malaria)$")):
    return svc_get_climate_forecast(region=region, disease=disease)