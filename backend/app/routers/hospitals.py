from fastapi import APIRouter, Query
from app.models.hospital import HospitalResponse
from app.services.ml import (
    get_hospital,
    get_hospital_capacity_trends as svc_get_hospital_capacity_trends,
    get_hospital_resources as svc_get_hospital_resources,
)


router = APIRouter(prefix="/hospitals", tags=["hospitals"])


@router.get("/current", response_model=HospitalResponse)
def get_hospitals_current(region: str = Query("All")):
    return get_hospital(region)


@router.get("/region/{region}", response_model=HospitalResponse)
def get_hospitals_by_region(region: str):
    return get_hospital(region)


@router.get("/capacity-trends")
def get_capacity_trends(
    region: str = Query("All"),
    startDate: str | None = None,
    endDate: str | None = None,
):
    trends = svc_get_hospital_capacity_trends(region)
    # Filter by date range if provided
    # Note: trends use ISO week format (YYYY-W##), but startDate/endDate might be ISO datetime
    # Only filter if both are in the same format
    if startDate or endDate:
        filtered = []
        for trend in trends:
            trend_date = trend.get("date", "")
            # Only apply filtering if formats match (both ISO week or both ISO datetime)
            if "-W" in trend_date:
                # Trend is in ISO week format, only filter if params are also in week format
                if startDate and "-W" in startDate and trend_date < startDate:
                    continue
                if endDate and "-W" in endDate and trend_date > endDate:
                    continue
            else:
                # Trend is in ISO datetime format
                if startDate and trend_date < startDate:
                    continue
                if endDate and trend_date > endDate:
                    continue
            filtered.append(trend)
        trends = filtered
    return {"region": region, "trends": trends}


@router.get("/resources")
def get_hospital_resources(region: str = Query("All"), resourceType: str = Query("beds")):
    return svc_get_hospital_resources(region, resourceType)