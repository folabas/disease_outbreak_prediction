from pydantic import BaseModel
from typing import Any, Dict, List


class HospitalTotals(BaseModel):
    facilities: int
    avgBedCapacity: float
    bedsPer10k: float


class HospitalResponse(BaseModel):
    region: str
    totals: HospitalTotals
    facilitiesGeo: Dict[str, Any]