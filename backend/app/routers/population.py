from fastapi import APIRouter, Query
from app.models.population import PopulationResponse
from app.services.ml import get_population


router = APIRouter(prefix="/population", tags=["population"])


@router.get("/", response_model=PopulationResponse)
def get_population_stats(region: str = Query("All")):
    return get_population(region)