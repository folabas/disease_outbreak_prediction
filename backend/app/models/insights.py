from pydantic import BaseModel
from typing import List


class Metrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    auc: float | None = None


class FeatureImportanceItem(BaseModel):
    name: str
    value: float


class InsightsResponse(BaseModel):
    metrics: Metrics
    featureImportance: List[FeatureImportanceItem]
    notes: str | None = None