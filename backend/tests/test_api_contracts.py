import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health_v1():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "success"
    assert isinstance(body.get("timestamp"), str)
    assert body.get("data", {}).get("service") == "outbreakiq"


@pytest.mark.parametrize("path", [
    "/api/v1/analytics/insights",
    "/api/v1/predictions",
    "/api/v1/climate",
    "/api/v1/population",
    "/api/v1/hospital",
])
def test_basic_endpoints_ok(path):
    resp = client.get(path)
    assert resp.status_code == 200


def test_disease_validation_error():
    resp = client.get("/api/v1/disease/current/unknown")
    assert resp.status_code == 400
    body = resp.json()
    # Error envelope
    assert body.get("status") == "error"
    assert body.get("error", {}).get("code") == 400


def test_metadata_options_endpoint():
    resp = client.get("/api/v1/metadata/options")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "success"
    data = body.get("data", {})
    assert isinstance(data.get("diseases", []), list)
    assert isinstance(data.get("years", []), list)
    assert isinstance(data.get("regions", []), list)


def test_recommendations_endpoint():
    resp = client.get("/api/v1/recommendations", params={"disease": "cholera"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "success"
    data = body.get("data") or {}
    # Should return a list of recommendations
    recs = data.get("recommendations") or data.get("data", {}).get("recommendations")
    assert isinstance(recs, list)


def test_predictions_current_envelope():
    resp = client.get("/api/v1/predictions/current", params={"region": "All", "disease": "cholera"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "success"
    assert isinstance(body.get("timestamp"), str)
    data = body.get("data", {})
    assert data.get("region") is not None
    assert data.get("disease") in ("cholera", "malaria")


def test_disease_current_envelope():
    resp = client.get("/api/v1/disease/current/cholera", params={"region": "All"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "success"
    assert isinstance(body.get("timestamp"), str)
    data = body.get("data", {})
    assert data.get("disease") == "cholera"
    assert data.get("region") is not None


def test_predicted_actual_merge_endpoint():
    resp = client.get("/api/v1/charts/predicted-actual", params={"disease": "cholera", "region": "All"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "success"
    data = body.get("data", {})
    assert isinstance(data.get("series", []), list)
    assert isinstance(data.get("live_only", False), bool)