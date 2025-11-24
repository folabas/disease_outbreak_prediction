"""
Patch script to add missing endpoints to analytics.py
This script safely appends the missing endpoints without corrupting the file.
"""

# Read the current analytics.py
with open("backend/app/routers/analytics.py", "r", encoding="utf-8") as f:
    content = f.read()

# Check if endpoints already exist
if "/model-metrics" in content:
    print("Endpoints already exist, skipping patch")
    exit(0)

# Add the missing imports and endpoints
additional_code = '''

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
    normalized = rel_path.replace("\\\\", "/")
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
    normalized = path.replace("\\\\", "/")
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
'''

# Write the patched file
with open("backend/app/routers/analytics.py", "a", encoding="utf-8") as f:
    f.write(additional_code)

print("Successfully patched analytics.py with missing endpoints")
