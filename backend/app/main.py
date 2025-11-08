from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import ALLOWED_ORIGINS
from app.routers import predictions, climate, population, hospital, insights


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