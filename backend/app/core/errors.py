from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException
import logging


def init_logging() -> None:
    """Initialize basic structured logging for the API."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def http_exception_handler(request: Request, exc: FastAPIHTTPException) -> JSONResponse:
    status_code = exc.status_code or 500
    detail = exc.detail if isinstance(exc.detail, (str, dict)) else str(exc.detail)
    logging.error("HTTPException: %s %s -> %s", request.method, request.url.path, detail)
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "error": {
                "code": status_code,
                "message": detail,
            },
        },
    )


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logging.exception("Unhandled error at %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": 500,
                "message": "Internal server error",
            },
        },
    )