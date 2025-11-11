from fastapi import APIRouter, Query
from app.models.risk_factors import RiskFactorsResponse, RiskFactor
from app.services.ml import get_insights


router = APIRouter(prefix="/risk-factors", tags=["risk-factors"])


@router.get("/{region}", response_model=RiskFactorsResponse)
def get_risk_factors(region: str, disease: str = Query("cholera")):
    # Leverage insights feature importance as proxy for regional risk factors
    ins = get_insights(disease=disease, region=region)
    factors = [RiskFactor(name=item.name, score=item.value) for item in (ins.featureImportance or [])]
    return RiskFactorsResponse(region=region, disease=disease, factors=factors)