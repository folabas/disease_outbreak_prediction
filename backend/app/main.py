from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException as FastAPIHTTPException
import logging

from app.core.config import ALLOWED_ORIGINS, API_PREFIX, API_V1_PREFIX
from app.routers import predictions, climate, population, hospital, insights
from app.routers import risk_factors, hospitals, disease, geo, analytics, metadata, recommendations, aggregates
from app.core.errors import http_exception_handler, unhandled_exception_handler, init_logging
from app.core.response import success


app = FastAPI(title="OutbreakIQ API", version="1.0")
init_logging()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(f"{API_PREFIX}/health")
def health():
    return success({"service": "outbreakiq", "version": "1.0"})

@app.get(f"{API_V1_PREFIX}/health")
def health_v1():
    return success({"service": "outbreakiq", "version": "1.0"})

app.include_router(predictions.router, prefix=API_PREFIX, tags=["predictions"])
app.include_router(climate.router, prefix=API_PREFIX, tags=["climate"])
app.include_router(population.router, prefix=API_PREFIX, tags=["population"])
app.include_router(hospital.router, prefix=API_PREFIX, tags=["hospital"])
app.include_router(insights.router, prefix=API_PREFIX, tags=["insights"])
app.include_router(risk_factors.router, prefix=API_PREFIX, tags=["risk-factors"])
app.include_router(hospitals.router, prefix=API_PREFIX, tags=["hospitals"])
app.include_router(disease.router, prefix=API_PREFIX, tags=["disease"])
app.include_router(geo.router, prefix=API_PREFIX, tags=["geo"])
app.include_router(analytics.router, prefix=API_PREFIX, tags=["analytics"])
app.include_router(metadata.router, prefix=API_PREFIX, tags=["metadata"])
app.include_router(recommendations.router, prefix=API_PREFIX, tags=["recommendations"])
app.include_router(aggregates.router, prefix=API_PREFIX, tags=["charts"])

# Versioned v1 routes for stabilization and future evolution
app.include_router(predictions.router, prefix=API_V1_PREFIX, tags=["predictions"])
app.include_router(climate.router, prefix=API_V1_PREFIX, tags=["climate"])
app.include_router(population.router, prefix=API_V1_PREFIX, tags=["population"])
app.include_router(hospital.router, prefix=API_V1_PREFIX, tags=["hospital"])
app.include_router(insights.router, prefix=API_V1_PREFIX, tags=["insights"])
app.include_router(risk_factors.router, prefix=API_V1_PREFIX, tags=["risk-factors"])
app.include_router(hospitals.router, prefix=API_V1_PREFIX, tags=["hospitals"])
app.include_router(disease.router, prefix=API_V1_PREFIX, tags=["disease"])
app.include_router(geo.router, prefix=API_V1_PREFIX, tags=["geo"])
app.include_router(analytics.router, prefix=API_V1_PREFIX, tags=["analytics"])
app.include_router(metadata.router, prefix=API_V1_PREFIX, tags=["metadata"])
app.include_router(recommendations.router, prefix=API_V1_PREFIX, tags=["recommendations"])
app.include_router(aggregates.router, prefix=API_V1_PREFIX, tags=["charts"])

# Global exception handlers to enforce a stable error envelope
app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Simple request logging middleware to verify frontend calls
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = getattr(request, "_start_time", None) or None
    try:
        method = request.method
        path = request.url.path
        query = str(request.url.query)
        logging.info("REQ %s %s%s", method, path, (f"?{query}" if query else ""))
    except Exception:
        # Avoid blocking the request on logging errors
        pass
    response = await call_next(request)
    try:
        logging.info("RES %s %s -> %s", request.method, request.url.path, response.status_code)
    except Exception:
        pass
    return response