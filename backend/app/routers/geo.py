from fastapi import APIRouter, Query
import logging
from app.core.response import success
from app.core.validators import validate_region, validate_disease
from app.services.ml import get_geo_boundaries as svc_get_geo_boundaries, get_geo_heatmap as svc_get_geo_heatmap


router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/boundaries")
def get_geo_boundaries(region: str = Query("All")):
    logging.info("/geo/boundaries GET region=%s", region)
    region = validate_region(region) or "All"
    data = svc_get_geo_boundaries(region)
    return success(data)


@router.get("/heatmap")
def get_geo_heatmap(region: str = Query("All"), disease: str = Query("cholera", regex="^(cholera|malaria)$")):
    logging.info("/geo/heatmap GET region=%s disease=%s", region, disease)
    region = validate_region(region) or "All"
    disease = validate_disease(disease) or disease
    data = svc_get_geo_heatmap(region, disease)
    return success(data)