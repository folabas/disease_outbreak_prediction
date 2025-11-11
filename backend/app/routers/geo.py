from fastapi import APIRouter, Query
from app.services.ml import get_geo_boundaries as svc_get_geo_boundaries, get_geo_heatmap as svc_get_geo_heatmap


router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/boundaries")
def get_geo_boundaries(region: str = Query("All")):
    return svc_get_geo_boundaries(region)


@router.get("/heatmap")
def get_geo_heatmap(region: str = Query("All"), disease: str = Query("cholera")):
    return svc_get_geo_heatmap(region, disease)