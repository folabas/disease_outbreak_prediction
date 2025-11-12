# OutbreakIQ Backend

FastAPI backend providing endpoints for predictions, climate, population, hospital, and insights. Designed to load ML models and data from the project.

## Structure

```
backend/
  app/
    __init__.py
    main.py
    core/
      __init__.py
      config.py
    models/
      __init__.py
      predictions.py
      climate.py
      population.py
      hospital.py
      insights.py
    routers/
      __init__.py
      predictions.py
      climate.py
      population.py
      hospital.py
      insights.py
    services/
      __init__.py
      ml.py
requirements.txt
```

## Quickstart

1. Create virtual environment

```
python -m venv .venv
```

2. Install dependencies

```
.venv/Scripts/python -m pip install -r backend/requirements.txt
```

3. Run the server

```
cd backend
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for Swagger UI.

## API Versioning and Deprecation

- Stable versioned routes are available under `api/v1`. The legacy prefix `api/` is kept temporarily for parity verification.
- Success responses are normalized to the envelope: `{"status": "success", "data": {...}, "timestamp": ISO8601, "message"?}`. Error responses use `{"status": "error", "error": {"code": <int>, "message": <string>}}`.
- Input validation is enforced for common parameters like `disease` (allowed: `cholera`, `malaria`), `region` (non-empty string), and `date` (ISO format or `YYYY-Wnn`).

### Deprecation Timeline

1. Parity verification: ensure `api/v1` covers all endpoints used by the frontend and tests.
2. Announce deprecation: update client configs and documentation to point to `api/v1` exclusively.
3. Remove legacy `api/` registration once parity is confirmed and tests pass.

If you depend on legacy `api/` endpoints, migrate to `api/v1` and confirm envelopes match the normalized contract.