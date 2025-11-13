import os
from typing import Dict, Any, Optional

import requests
from fastapi import APIRouter, Query, HTTPException
import logging

from app.core.config import ALLOWED_DISEASES, OLLAMA_URL, OLLAMA_MODEL
from app.core.response import success
from app.services.ml import get_insights
from app.services.llm import generate_recommendations_ollama


router = APIRouter()


def _rule_based_recommendations(disease: str, region: Optional[str], insights: Dict[str, Any]) -> Dict[str, Any]:
    factors = insights.get("feature_importances", {}) or {}
    top = sorted([(k, v) for k, v in factors.items()], key=lambda x: abs(x[1]), reverse=True)[:5]

    recs = []
    for feat, weight in top:
        if "rain" in feat or "precip" in feat:
            recs.append("Increase sanitation around water sources; distribute water purification tablets.")
        elif "temp" in feat or "temperature" in feat:
            recs.append("Schedule community awareness on heat management and disease prevention.")
        elif "humidity" in feat:
            recs.append("Deploy mosquito nets and conduct indoor residual spraying.")
        elif "population" in feat or "density" in feat:
            recs.append("Reduce crowding in clinics; set up mobile outreach units.")
        else:
            recs.append("Strengthen surveillance and ensure availability of essential medications.")

    # Make unique and concise
    unique_recs = list(dict.fromkeys(recs))
    return {
        "source": "rule_based",
        "recommendations": unique_recs,
        "context": {
            "topFactors": [{"feature": f, "weight": float(w)} for f, w in top],
            "region": region,
            "disease": disease,
        },
    }


@router.get("/recommendations")
def get_recommendations(
    disease: str = Query("cholera"),
    region: Optional[str] = Query(default=None),
    year: Optional[int] = Query(default=None),
) -> Dict[str, Any]:
    logging.info("/recommendations GET disease=%s region=%s year=%s", disease, region, year)
    """Return preventive recommendations using a free AI API when available (Gemini),
    otherwise fall back to rule-based logic derived from feature importances.
    """
    if disease not in ALLOWED_DISEASES:
        raise HTTPException(status_code=400, detail=f"Unsupported disease: {disease}")

    insights = get_insights(disease=disease, region=region)

    # Prefer local Ollama when available
    try:
        if OLLAMA_URL and OLLAMA_MODEL:
            recs = generate_recommendations_ollama(disease=disease, region=region, year=year, insights=insights.dict() if hasattr(insights, "dict") else insights)
            if recs:
                return success({
                    "source": "ollama",
                    "recommendations": recs,
                    "region": region,
                    "disease": disease,
                    "year": year,
                })
    except Exception:
        # Fall through
        pass

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            prompt = (
                f"You are an epidemiology assistant. Given disease='{disease}', region='{region}', "
                f"year='{year}', and the following top risk factors: {insights.get('feature_importances', {})}. "
                "Return a concise list (4-6 bullets) of preventive recommendations tailored to these factors."
            )
            # Minimal Gemini REST call (models: gemini-1.5-flash) – will be used only if key is set
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
            resp = requests.post(
                url,
                params={"key": api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                },
                timeout=8,
            )
            resp.raise_for_status()
            data = resp.json()
            # Extract text safely
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            if text:
                return success({
                    "source": "gemini",
                    "recommendations": [t.strip("- ") for t in text.split("\n") if t.strip()],
                    "region": region,
                    "disease": disease,
                    "year": year,
                })
        except Exception:
            # Fall through to rule-based if API fails
            pass

    rb = _rule_based_recommendations(disease, region, insights.dict() if hasattr(insights, "dict") else insights)
    return success({"source": rb["source"], **rb})