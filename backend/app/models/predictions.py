from pydantic import BaseModel
from typing import List, Optional


class PredictionQuery(BaseModel):
    disease: str
    region: str = "All"
    lga: Optional[str] = None
    asOf: Optional[str] = None
    horizonDays: int = 14
    granularity: str = "daily"


class TimePoint(BaseModel):
    date: str
    predicted: float
    actual: Optional[float] = None


class RiskSummary(BaseModel):
    riskScore: float
    riskLevel: str
    confidence: float


class FeatureImportance(BaseModel):
    feature: str
    importance: float


class PredictionResponse(BaseModel):
    region: str
    disease: str
    summary: RiskSummary
    timeseries: List[TimePoint]
    explanations: Optional[List[FeatureImportance]] = None
    modelVersion: Optional[str] = None
    generatedAt: Optional[str] = None