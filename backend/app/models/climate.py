from pydantic import BaseModel
from typing import List, Optional


class ClimateQuery(BaseModel):
    region: str = "All"
    disease: Optional[str] = None
    lga: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    granularity: str = "weekly"

from pydantic import BaseModel
from typing import List, Optional


class ClimateQuery(BaseModel):
    region: str = "All"
    disease: Optional[str] = None
    lga: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    granularity: str = "weekly"


class SeriesPoint(BaseModel):
    date: str
    value: float


class ClimateResponse(BaseModel):
    region: str
    temperature: List[SeriesPoint]
    rainfall: List[SeriesPoint]
    summary: Optional[dict] = None