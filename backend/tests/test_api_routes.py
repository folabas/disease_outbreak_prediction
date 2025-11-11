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
async def test_all_api_routes():
    """Confirm all key API endpoints respond with status 200 or valid JSON."""

    endpoints = [
        ("/api/predictions?disease=Covid-19&region=All", "Predictions"),
        ("/api/climate?region=Lagos", "Climate"),
        ("/api/population?region=All", "Population"),
        ("/api/hospital?region=All", "Hospital"),
        ("/api/insights?disease=Covid-19", "Insights"),
    ]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        for url, label in endpoints:
            response = await client.get(url)
            print(f"\n[TEST] {label}: {url} → {response.status_code}")
            print("Response JSON:", response.json())

            # Basic assertions
            assert response.status_code in (200, 422), f"{label} failed: {response.text}"
            assert isinstance(response.json(), dict), f"{label} should return JSON"