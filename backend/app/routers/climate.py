from fastapi import APIRouter, Query
from app.models.climate import ClimateQuery, ClimateResponse
from app.services.ml import get_climate, get_climate_forecast as svc_get_climate_forecast


router = APIRouter(prefix="/climate", tags=["climate"])


@router.get("/", response_model=ClimateResponse)
def get_climate_series(
    region: str = Query("All"),
    disease: str = Query("cholera"),
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
):
    from app.core.validators import validate_disease
    disease = validate_disease(disease) or disease
    q = ClimateQuery(region=region, disease=disease, startDate=startDate, endDate=endDate)
    return get_climate(q)


@router.get("/current/{region}", response_model=ClimateResponse)
def get_current_climate(
    region: str,
    disease: str = Query("cholera"),
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
):
    from app.core.validators import validate_disease
    disease = validate_disease(disease) or disease
    q = ClimateQuery(region=region, disease=disease, startDate=startDate, endDate=endDate)
    return get_climate(q)


# Alias to support /climate/region/{region}
@router.get("/region/{region}", response_model=ClimateResponse)
def get_climate_by_region(
    region: str,
    disease: str = Query("cholera"),
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
):
    from app.core.validators import validate_disease
    disease = validate_disease(disease) or disease
    q = ClimateQuery(region=region, disease=disease, startDate=startDate, endDate=endDate)
    return get_climate(q)


@router.get("/historical", response_model=ClimateResponse)
def get_climate_historical(
    region: str = Query("All"),
    disease: str = Query("cholera"),
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
):
    from app.core.validators import validate_disease
    disease = validate_disease(disease) or disease
    q = ClimateQuery(region=region, disease=disease, startDate=startDate, endDate=endDate)
    return get_climate(q)


@router.get("/forecast/{region}", response_model=ClimateResponse)
def get_climate_forecast(
    region: str,
    disease: str = Query("cholera"),
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
    days: int = Query(7, ge=1, le=30),
):
    from app.core.validators import validate_disease
    disease = validate_disease(disease) or disease
    return svc_get_climate_forecast(region=region, disease=disease, startDate=startDate, endDate=endDate, days=days)