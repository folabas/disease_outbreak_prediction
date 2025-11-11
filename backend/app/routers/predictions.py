from fastapi import APIRouter, Query
from app.models.predictions import PredictionQuery, PredictionResponse
from app.services.ml import predict_series


router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/", response_model=PredictionResponse)
def get_predictions(
    region: str = Query("All"),
    disease: str = Query("cholera"),
    window: int = Query(14, ge=1, le=180),
):
    q = PredictionQuery(region=region, disease=disease, window=window)
    return predict_series(q)


@router.get("/current", response_model=PredictionResponse)
def get_current_predictions(
    region: str = Query("All"),
    disease: str = Query("cholera"),
    window: int = Query(14, ge=1, le=180),
):
    q = PredictionQuery(region=region, disease=disease, window=window)
    return predict_series(q)


@router.get("/region/{region}", response_model=PredictionResponse)
def get_predictions_by_region(
    region: str,
    disease: str = Query("cholera"),
    window: int = Query(14, ge=1, le=180),
):
    q = PredictionQuery(region=region, disease=disease, window=window)
    return predict_series(q)


@router.get("/historical", response_model=PredictionResponse)
def get_historical_predictions(
    region: str = Query("All"),
    disease: str = Query("cholera"),
    window: int = Query(30, ge=1, le=365),
):
    # Reuse predict_series to generate a summary, but extend timeseries with recent actuals
    q = PredictionQuery(region=region, disease=disease, window=window)
    base = predict_series(q)
    try:
        # Attempt to append recent historical actuals from training data if available
        import os
        import pandas as pd
        from app.core.config import DATA_DIR

        df_path = os.path.join(DATA_DIR, "outbreakiq_training_data_filled.csv")
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
        # If anything fails, return the base response
        return base
    return base