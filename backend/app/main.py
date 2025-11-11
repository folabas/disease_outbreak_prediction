from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import ALLOWED_ORIGINS
from app.routers import predictions, climate, population, hospital, insights
from app.routers import risk_factors, hospitals, disease, geo, analytics


app = FastAPI(title="OutbreakIQ API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "outbreakiq", "version": "1.0"}


app.include_router(predictions.router, prefix="/api", tags=["predictions"])
app.include_router(climate.router, prefix="/api", tags=["climate"])
app.include_router(population.router, prefix="/api", tags=["population"])
app.include_router(hospital.router, prefix="/api", tags=["hospital"])
app.include_router(insights.router, prefix="/api", tags=["insights"])
app.include_router(risk_factors.router, prefix="/api", tags=["risk-factors"])
app.include_router(hospitals.router, prefix="/api", tags=["hospitals"])
app.include_router(disease.router, prefix="/api", tags=["disease"])
app.include_router(geo.router, prefix="/api", tags=["geo"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])