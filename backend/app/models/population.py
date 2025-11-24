from pydantic import BaseModel
from typing import List, Optional


class PopulationEntry(BaseModel):
    region: str
    value: float


class PopulationResponse(BaseModel):
    region: Optional[str] = None
    totalPopulation: Optional[int] = None
    growthRates: List[PopulationEntry]
    density: List[PopulationEntry]