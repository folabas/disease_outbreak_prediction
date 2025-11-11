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