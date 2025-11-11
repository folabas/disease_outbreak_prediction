from fastapi import APIRouter, Query
from app.models.hospital import HospitalResponse
from app.services.ml import (
    get_hospital,
    get_hospital_capacity_trends as svc_get_hospital_capacity_trends,
    get_hospital_resources as svc_get_hospital_resources,
)
from datetime import datetime, timedelta


router = APIRouter(prefix="/hospitals", tags=["hospitals"])


@router.get("/current", response_model=HospitalResponse)
def get_hospitals_current(region: str = Query("All")):
    return get_hospital(region)


@router.get("/region/{region}", response_model=HospitalResponse)
def get_hospitals_by_region(region: str):
    return get_hospital(region)


@router.get("/capacity-trends")
def get_capacity_trends(region: str = Query("All")):
    return {"region": region, "trends": svc_get_hospital_capacity_trends(region)}


@router.get("/resources")
def get_hospital_resources(region: str = Query("All"), resourceType: str = Query("beds")):
    return svc_get_hospital_resources(region, resourceType)