from typing import Optional
from fastapi import HTTPException
from datetime import datetime

from app.core.config import ALLOWED_DISEASES


def validate_disease(disease: Optional[str]) -> Optional[str]:
    if disease is None:
        return None
    d = disease.strip().lower()
    if d not in ALLOWED_DISEASES:
        raise HTTPException(status_code=400, detail=f"Unsupported disease: {disease}")
    return d


def validate_region(region: Optional[str]) -> Optional[str]:
    # Accept any non-empty region string; specific allowed sets can be added later
    if region is None:
        return None
    r = region.strip()
    if not r:
        raise HTTPException(status_code=400, detail="Region cannot be empty")
    return r


def validate_date_str(date_str: Optional[str]) -> Optional[str]:
    if date_str is None:
        return None
    try:
        # Accept either YYYY-MM-DD or ISO 8601
        # If week format is used (YYYY-Wnn), we allow it as-is.
        if "W" in date_str:
            return date_str
        datetime.fromisoformat(date_str)
        return date_str
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date_str}")