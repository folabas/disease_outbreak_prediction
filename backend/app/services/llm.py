import os
from typing import List, Dict, Any, Optional

import requests

from app.core.config import OLLAMA_URL, OLLAMA_MODEL


def _compose_prompt(disease: str, region: Optional[str], year: Optional[int], insights: Dict[str, Any]) -> str:
    top = insights.get("feature_importances") or {}
    ctx = \
        f"Disease: {disease}. Region: {region or 'All'}. Year: {year or ''}. " \
        f"Top risk factors: {top}."
    return (
        "You are an epidemiology assistant. Based on the context, provide 5 preventive "
        "public health recommendations tailored to the disease and region. "
        "Return STRICT JSON only with the following schema: "
        "{\"recommendations\": [\"Recommendation 1\", \"Recommendation 2\", ...]} . "
        "Make each item concise and actionable. Context: " + ctx
    )


def generate_recommendations_ollama(
    disease: str,
    region: Optional[str],
    year: Optional[int],
    insights: Dict[str, Any],
    timeout_seconds: int = 10,
) -> List[str]:
    url = f"{OLLAMA_URL.rstrip('/')}/api/generate"
    payload: Dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "prompt": _compose_prompt(disease, region, year, insights),
        "format": "json",
        "stream": False,
    }
    resp = requests.post(url, json=payload, timeout=timeout_seconds)
    resp.raise_for_status()
    data = resp.json()
    # When format=json and stream=false, Ollama returns { response: "{...json...}", ... }
    txt = data.get("response") or ""
    try:
        import json as _json
        obj = _json.loads(txt) if isinstance(txt, str) else (txt or {})
        items = obj.get("recommendations") or []
        if isinstance(items, list):
            return [str(x).strip() for x in items if x]
    except Exception:
        pass
    return []