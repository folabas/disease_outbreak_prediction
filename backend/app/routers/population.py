from fastapi import APIRouter, Query
from app.models.population import PopulationResponse
from app.services.ml import (
    get_population,
    get_population_demographics as svc_get_population_demographics,
    get_population_density_map as svc_get_population_density_map,
)


router = APIRouter(prefix="/population", tags=["population"])


@router.get("/", response_model=PopulationResponse)
def get_population_stats(
    region: str = Query("All"),
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
):
    return get_population(region=region, startDate=startDate, endDate=endDate)


# Alias to support /population/current
@router.get("/current", response_model=PopulationResponse)
def get_population_current(
    region: str = Query("All"),
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
):
    return get_population(region=region, startDate=startDate, endDate=endDate)


@router.get("/stats/{region}", response_model=PopulationResponse)
def get_population_stats_by_region(
    region: str,
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
):
    return get_population(region=region, startDate=startDate, endDate=endDate)


# Alias to support /population/region/{region}
@router.get("/region/{region}", response_model=PopulationResponse)
def get_population_by_region(
    region: str,
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
):
    return get_population(region=region, startDate=startDate, endDate=endDate)


@router.get("/demographics/{region}")
def get_population_demographics(region: str):
    return svc_get_population_demographics(region)


@router.get("/density-map")
def get_population_density_map(region: str = Query("All")):
    return svc_get_population_density_map(region)