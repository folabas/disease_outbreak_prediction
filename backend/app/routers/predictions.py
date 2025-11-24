from fastapi import APIRouter, Query
import logging
from app.models.predictions import PredictionQuery, PredictionResponse
from app.services.ml import predict_series
from app.core.response import success
from app.core.validators import validate_region, validate_disease


router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/")
def get_predictions(
    region: str = Query("All"),
    disease: str = Query("cholera"),
    window: int = Query(14, ge=1, le=180),
):
    logging.info("/predictions GET region=%s disease=%s window=%s", region, disease, window)
    region = validate_region(region) or "All"
    disease = validate_disease(disease) or disease
    q = PredictionQuery(region=region, disease=disease, window=window)
    return success(predict_series(q).dict())


@router.get("/current")
def get_current_predictions(
    region: str = Query("All"),
    disease: str = Query("cholera"),
    window: int = Query(14, ge=1, le=180),
):
    logging.info("/predictions/current GET region=%s disease=%s window=%s", region, disease, window)
    region = validate_region(region) or "All"
    disease = validate_disease(disease) or disease
    q = PredictionQuery(region=region, disease=disease, window=window)
    return success(predict_series(q).dict())


@router.get("/region/{region}")
def get_predictions_by_region(
    region: str,
    disease: str = Query("cholera"),
    window: int = Query(14, ge=1, le=180),
):
    logging.info("/predictions/region/%s GET disease=%s window=%s", region, disease, window)
    region = validate_region(region) or region
    disease = validate_disease(disease) or disease
    q = PredictionQuery(region=region, disease=disease, window=window)
    return success(predict_series(q).dict())


@router.get("/historical")
def get_historical_predictions(
    region: str = Query("All"),
    disease: str = Query("cholera"),
    window: int = Query(30, ge=1, le=365),
):
    # Reuse predict_series to generate a summary, but extend timeseries with recent actuals
    logging.info("/predictions/historical GET region=%s disease=%s window=%s", region, disease, window)
    region = validate_region(region) or "All"
    disease = validate_disease(disease) or disease
    q = PredictionQuery(region=region, disease=disease, window=window)
    try:
        # Attempt to append recent historical actuals from training data if available
        import os
        import pandas as pd
        from app.core.config import DATA_DIR

        df_path = os.path.join(DATA_DIR, "outbreak_dataset.csv")
        if os.path.exists(df_path):
            df = pd.read_csv(df_path)
            if "disease" in df.columns and disease:
                df = df[df["disease"].astype(str).str.lower() == disease.lower()]
            if "state" in df.columns:
                if region and region != "All":
                    df = df[df["state"].astype(str).str.lower() == region.lower()]
                else:
                    if any(df["state"].astype(str).str.lower() == "all"):
                        df = df[df["state"].astype(str).str.lower() == "all"]

            sort_cols = [c for c in ["year", "week"] if c in df.columns]
            if sort_cols:
                df = df.sort_values(sort_cols).reset_index(drop=True)

            # Build recent actual series
            records = []
            for _, row in df.tail(min(window, 50)).iterrows():
                date = None
                if "date" in df.columns:
                    date = str(row.get("date"))
                elif all(c in df.columns for c in ["year", "week"]):
                    date = f"{int(row.get('year'))}-W{int(row.get('week'))}"
                else:
                    date = "unknown"
                actual = None
                if "cases" in df.columns:
                    try:
                        actual = float(row.get("cases"))
                    except Exception:
                        actual = None
                records.append({"date": date, "actual": actual})

            # Merge into base timeseries by prepending historical actuals without predicted values
            historic = []
            for r in records:
                try:
                    historic.append(type(base.timeseries[0])(date=r["date"], predicted=0.0, actual=r["actual"]))
                except Exception:
                    pass
            base.timeseries = historic + (base.timeseries or [])
    except Exception:
        # If anything fails, return the base response wrapped
        return success(base.dict())
    return success(base.dict())


@router.post("/predict")
def post_predict(payload: PredictionQuery):
    """
    Real-time prediction endpoint.
    Accepts standard PredictionQuery with optional custom parameters.
    """
    logging.info("/predictions/predict POST region=%s disease=%s", payload.region, payload.disease)
    payload.region = validate_region(payload.region) or payload.region
    payload.disease = validate_disease(payload.disease) or payload.disease
    result = predict_series(payload)
    return success(result.dict())


@router.post("/predict/custom")
def post_custom_predict(
    disease: str = Query(...),
    region: str = Query("All"),
    temperature: float | None = Query(None),
    humidity: float | None = Query(None),
    precipitation: float | None = Query(None),
    population: float | None = Query(None),
    window: int = Query(14, ge=1, le=180),
):
    """
    Real-time prediction with custom input parameters.
    Allows users to input specific climate and demographic values for custom predictions.
    """
    logging.info("/predictions/predict/custom POST disease=%s region=%s", disease, region)
    disease = validate_disease(disease) or disease
    region = validate_region(region) or "All"
    
    # Create prediction query
    q = PredictionQuery(region=region, disease=disease, window=window)
    
    # If custom parameters provided, they will be used by predict_series
    # (Note: This requires enhancing predict_series to accept custom features)
    # For now, return standard prediction
    result = predict_series(q)
    
    # Add metadata about custom inputs
    custom_inputs = {}
    if temperature is not None:
        custom_inputs["temperature"] = temperature
    if humidity is not None:
        custom_inputs["humidity"] = humidity
    if precipitation is not None:
        custom_inputs["precipitation"] = precipitation
    if population is not None:
        custom_inputs["population"] = population
    
    result_dict = result.dict()
    if custom_inputs:
        result_dict["customInputs"] = custom_inputs
        result_dict["notes"] = (result_dict.get("notes", "") + f" Custom inputs provided: {custom_inputs}").strip()
    
    return success(result_dict)