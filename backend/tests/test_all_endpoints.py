import os
import sys
import pytest
from httpx import AsyncClient, ASGITransport


# Ensure the 'backend' directory is on sys.path so `app` is importable
THIS_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(THIS_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app  # noqa: E402


@pytest.mark.asyncio
async def test_all_api_endpoints():
    """Exercise all implemented API endpoints to ensure they respond."""

    endpoints = [
        # Health
        ("/api/health", "Health"),

        # Predictions
        ("/api/predictions?disease=Cholera&region=All&window=14", "Predictions (query)"),
        ("/api/predictions/current?disease=Cholera&region=All&window=14", "Predictions current"),
        ("/api/predictions/region/Lagos?disease=Cholera&window=14", "Predictions by region"),
        ("/api/predictions/historical?disease=Cholera&region=All&window=30", "Predictions historical"),

        # Risk Factors
        ("/api/risk-factors/Lagos?disease=Cholera", "Risk factors by region"),

        # Climate
        ("/api/climate?region=Lagos&disease=Cholera", "Climate (query)"),
        ("/api/climate/current/Lagos?disease=Cholera", "Climate current"),
        ("/api/climate/historical?region=All&disease=Cholera", "Climate historical"),
        ("/api/climate/forecast/Lagos?disease=Cholera", "Climate forecast"),

        # Population
        ("/api/population?region=All", "Population (query)"),
        ("/api/population/stats/Lagos", "Population stats by region"),
        ("/api/population/demographics/Lagos", "Population demographics"),

        # Hospitals (plural)
        ("/api/hospitals/current?region=All", "Hospitals current"),
        ("/api/hospitals/region/Lagos", "Hospitals by region"),
        ("/api/hospitals/capacity-trends?region=All", "Hospitals capacity trends"),
        ("/api/hospitals/resources?region=All&resourceType=beds", "Hospitals resources"),

        # Hospital (singular, legacy)
        ("/api/hospital?region=All", "Hospital singular"),

        # Disease
        ("/api/disease/current/Cholera?region=All", "Disease current"),
        ("/api/disease/Cholera/region/Lagos", "Disease by region"),
        ("/api/disease/historical?region=All&disease=Cholera&window=24", "Disease historical"),
        ("/api/disease/alerts?region=All&disease=Cholera&threshold=0.7", "Disease alerts"),

        # Geo
        ("/api/geo/boundaries?region=All", "Geo boundaries"),
        ("/api/geo/heatmap?region=All&disease=Cholera", "Geo heatmap"),

        # Analytics
        ("/api/analytics/insights?disease=Cholera", "Analytics insights"),
        ("/api/analytics/hotspots?disease=Cholera&top_n=5", "Analytics hotspots"),
    ]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        for url, label in endpoints:
            resp = await client.get(url)
            print(f"\n[TEST] {label}: {url} → {resp.status_code}")
            try:
                data = resp.json()
                print("Response JSON keys:", list(data.keys()) if isinstance(data, dict) else type(data))
            except Exception:
                print("Response not JSON", resp.text[:200])

            assert resp.status_code in (200, 422), f"{label} failed: {resp.text}"
            # Basic JSON shape
            assert resp.headers.get("content-type", "").startswith("application/json"), f"{label} should return JSON"