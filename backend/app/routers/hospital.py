from fastapi import APIRouter, Query
from app.models.hospital import HospitalResponse
from app.services.ml import get_hospital


router = APIRouter(prefix="/hospital", tags=["hospital"])


@router.get("/", response_model=HospitalResponse)
def get_hospital_summary(region: str = Query("All")):
    return get_hospital(region)