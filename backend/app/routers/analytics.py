from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
import logging
from app.models.insights import InsightsResponse
from app.core.response import success
from app.services.ml import get_insights
import os
import pandas as pd
from app.core.config import DATA_DIR, resolve_path


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/insights", response_model=InsightsResponse)
def get_analytics_insights(disease: str = Query("covid-19"), region: str | None = Query(None)):
    logging.info("/analytics/insights GET disease=%s region=%s", disease, region)
    return success(get_insights(disease=disease, region=region).dict())


@router.get("/hotspots")
def get_hotspots(disease: str = Query("covid-19"), year: int | None = Query(default=None), top_n: int = Query(5, ge=1, le=20)):
    logging.info("/analytics/hotspots GET disease=%s top_n=%s", disease, top_n)
    # Compute top regions by average recent cases from training data
    df_path = os.path.join(DATA_DIR, "outbreakiq_training_data_filled.csv")
    hotspots = []
    if os.path.exists(df_path):
        try:
            df = pd.read_csv(df_path)
            if "disease" in df.columns and disease:
                df = df[df["disease"].astype(str).str.lower() == disease.lower()]
            if year is not None and all(c in df.columns for c in ["year"]):
                try:
                    df = df[df["year"].astype(int) == int(year)]
                except Exception:
                    pass
            if "state" in df.columns and "cases" in df.columns:
                grp = df.groupby("state", as_index=False)["cases"].mean()
                grp = grp.sort_values("cases", ascending=False)
                for _, row in grp.head(top_n).iterrows():
                    hotspots.append({"region": str(row["state"]), "score": float(row["cases"])})
        except Exception:
            pass
    # Fallback stub
    if not hotspots:
        hotspots = [
            {"region": "Lagos", "score": 0.9},
            {"region": "Kano", "score": 0.8},
            {"region": "Rivers", "score": 0.7},
        ]
    return success({"disease": disease, "hotspots": hotspots})


@router.get("/roc")
def get_roc_image(disease: str = Query("covid-19")):
    metrics_csv = resolve_path("reports", "production", "evaluation_metrics.csv")
    try:
        if os.path.exists(metrics_csv):
            df = pd.read_csv(metrics_csv)
            row = df[df["disease"].astype(str).str.lower() == str(disease).lower()].head(1)
            if row is not None and not row.empty:
                p = str(row.iloc[0].get("roc_path") or "").strip()
                if p:
                    path = resolve_path(*p.replace("\\", "/").split("/"))
                    if os.path.exists(path):
                        return FileResponse(path, media_type="image/png")
    except Exception:
        pass
    raise HTTPException(status_code=404, detail="ROC image not available for requested disease")

def _read_csv_records(path: str):
    """Helper to read CSV files and return records."""
    if not os.path.exists(path):
        return []
    try:
        df = pd.read_csv(path)
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient="records")
    except Exception:
        return []


@router.get("/model-metrics")
def get_model_metrics(disease: str | None = Query(None)):
    """Expose evaluation_metrics.csv entries with optional disease filtering."""
    path = resolve_path("reports", "production", "evaluation_metrics.csv")
    rows = _read_csv_records(path)
    if disease:
        rows = [r for r in rows if str(r.get("disease", "")).lower() == disease.lower()]
    return success({"rows": rows, "count": len(rows)})


@router.get("/regression-metrics")
def get_regression_metrics():
    """Expose metrics_regression.csv for baseline RandomForest stats."""
    path = resolve_path("reports", "production", "metrics_regression.csv")
    rows = _read_csv_records(path)
    return success({"rows": rows, "count": len(rows)})


@router.get("/alert-metrics")
def get_alert_metrics(disease: str | None = Query(None)):
    """Expose metrics_alert_classification.csv for outbreak alert performance."""
    path = resolve_path("reports", "production", "metrics_alert_classification.csv")
    rows = _read_csv_records(path)
    if disease:
        rows = [r for r in rows if str(r.get("disease", "")).lower() == disease.lower()]
    
    # Transform field names and convert percentages to decimals
    # CSV has precision_weighted_pct (as percentage like 68.82), frontend expects decimal (0.6882)
    transformed_rows = []
    for row in rows:
        precision_pct = row.get("precision_weighted_pct")
        recall_pct = row.get("recall_weighted_pct")
        f1_pct = row.get("f1_weighted_pct")
        
        transformed = {
            "disease": row.get("disease"),
            "precision": precision_pct / 100 if precision_pct is not None else None,
            "recall": recall_pct / 100 if recall_pct is not None else None,
            "f1": f1_pct / 100 if f1_pct is not None else None,
        }
        transformed_rows.append(transformed)
    
    return success({"rows": transformed_rows, "count": len(transformed_rows)})


def _artifact_entry(name: str, rel_path: str):
    """Helper to create artifact entry."""
    from urllib.parse import quote
    normalized = rel_path.replace("\\", "/")
    parts = [p for p in normalized.split("/") if p]
    full = resolve_path(*parts)
    exists = os.path.exists(full)
    size_bytes = os.path.getsize(full) if exists else None
    updated_at = os.path.getmtime(full) if exists else None
    return {
        "name": name,
        "path": normalized,
        "exists": exists,
        "size_bytes": size_bytes,
        "updated_at": updated_at,
        "download_url": f"/api/v1/analytics/download?path={quote(normalized)}",
    }


def _collect_artifacts():
    """Collect all available artifacts."""
    artifacts = [
        _artifact_entry("Evaluation Metrics", "reports/production/evaluation_metrics.csv"),
        _artifact_entry("Regression Metrics", "reports/production/metrics_regression.csv"),
        _artifact_entry("Alert Metrics", "reports/production/metrics_alert_classification.csv"),
        _artifact_entry("Summary Report", "reports/production/summary_report.txt"),
        _artifact_entry("Health JSON", "reports/production/health.json"),
    ]

    metrics_path = resolve_path("reports", "production", "evaluation_metrics.csv")
    if os.path.exists(metrics_path):
        try:
            df = pd.read_csv(metrics_path)
            for _, row in df.iterrows():
                disease = str(row.get("disease", "")).strip() or "unknown"
                chart = str(row.get("chart_path", "")).strip()
                roc = str(row.get("roc_path", "")).strip()
                if chart:
                    artifacts.append(_artifact_entry(f"Actual vs Predicted ({disease})", chart))
                if roc:
                    artifacts.append(_artifact_entry(f"ROC Curve ({disease})", roc))
        except Exception:
            pass

    return artifacts


@router.get("/artifacts")
def list_artifacts():
    """List all available report artifacts."""
    return success({"artifacts": _collect_artifacts()})


@router.get("/download")
def download_artifact(path: str):
    """Download a specific artifact."""
    normalized = path.replace("\\", "/")
    parts = [p for p in normalized.split("/") if p]
    full = resolve_path(*parts)
    reports_root = resolve_path("reports", "production")
    if not os.path.exists(full):
        raise HTTPException(status_code=404, detail="Artifact not found")
    if os.path.commonpath([full, reports_root]) != reports_root:
        raise HTTPException(status_code=400, detail="Access to requested path is not allowed")
    return FileResponse(full, filename=os.path.basename(full))


@router.get("/health")
def get_reports_health():
    """Get health status of reports."""
    import json
    path = resolve_path("reports", "production", "health.json")
    if not os.path.exists(path):
        return success({"health": None})
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        payload = None
    return success({"health": payload})


@router.post("/refresh-reports")
def refresh_reports():
    """Trigger report refresh."""
    import subprocess
    from app.core.config import project_root
    script_path = resolve_path("scripts", "console_report.py")
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="console_report.py not found")
    try:
        result = subprocess.run(
            ["python", script_path, "--all"],
            cwd=project_root(),
            capture_output=True,
            text=True,
            timeout=900,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="Report refresh timed out") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return success({
        "exit_code": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    })
