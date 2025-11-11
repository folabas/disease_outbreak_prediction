from pydantic import BaseModel
from typing import List


class PopulationEntry(BaseModel):
    region: str
    value: float


class PopulationResponse(BaseModel):
    growthRates: List[PopulationEntry]
    density: List[PopulationEntry]