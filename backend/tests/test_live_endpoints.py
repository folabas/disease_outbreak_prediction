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
async def test_live_endpoints_core():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        # Climate forecast via Open-Meteo (fallbacks to recent series if offline)
        r = await client.get("/api/climate/forecast/Lagos?disease=Cholera")
        assert r.status_code in (200, 422)
        assert r.headers.get("content-type", "").startswith("application/json")
        js = r.json()
        # ClimateResponse should have at least temperature or rainfall arrays
        assert isinstance(js, dict)
        assert ("temperature" in js) or ("rainfall" in js)

        # Geo boundaries (loads GeoJSON file if present, else sample FeatureCollection)
        r = await client.get("/api/geo/boundaries?region=All")
        assert r.status_code in (200, 422)
        assert r.headers.get("content-type", "").startswith("application/json")
        js = r.json()
        assert isinstance(js, dict)
        assert js.get("type") == "FeatureCollection"

        # Hospitals current (plural)
        r = await client.get("/api/hospitals/current?region=All")
        assert r.status_code in (200, 422)
        assert r.headers.get("content-type", "").startswith("application/json")

        # Disease alerts (uses service combining predictions and optional metrics)
        r = await client.get("/api/disease/alerts?region=All&disease=Cholera&threshold=0.7")
        assert r.status_code in (200, 422)
        assert r.headers.get("content-type", "").startswith("application/json")
        js = r.json()
        assert isinstance(js, dict)
        assert "alerts" in js