from pydantic import BaseModel
from typing import List


class RiskFactor(BaseModel):
    name: str
    score: float


class RiskFactorsResponse(BaseModel):
    region: str
    disease: str
    factors: List[RiskFactor]