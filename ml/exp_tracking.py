from __future__ import annotations

import json
import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import mlflow
    import mlflow.sklearn  # noqa: F401
    _MLFLOW_AVAILABLE = True
except Exception:
    _MLFLOW_AVAILABLE = False


def sha256_file(path: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


class Tracker:
    """Experiment tracking with MLflow, falling back to a JSON registry.

    Minimal wrapper to avoid scattering tracking code across training scripts.
    """

    def __init__(self, project_root: Path, models_dir: Path, experiment_name: str = "OutbreakIQ"):
        self.project_root = project_root
        self.models_dir = models_dir
        self.registry_path = self.models_dir / "registry.json"
        self.experiment_name = experiment_name

        if _MLFLOW_AVAILABLE:
            try:
                mlflow.set_experiment(self.experiment_name)
            except Exception:
                # If a remote backend fails, continue silently and fallback later if needed
                pass

    def start(self, run_name: str, tags: Optional[Dict[str, str]] = None):
        if _MLFLOW_AVAILABLE:
            return mlflow.start_run(run_name=run_name, tags=tags)
        # No-op context manager
        class _Dummy:
            def __enter__(self):
                return None
            def __exit__(self, exc_type, exc, tb):
                return False
        return _Dummy()

    def log_params(self, params: Dict[str, Any]):
        if _MLFLOW_AVAILABLE:
            try:
                mlflow.log_params(params)
            except Exception:
                pass

    def log_metrics(self, metrics: Dict[str, float]):
        if _MLFLOW_AVAILABLE:
            try:
                mlflow.log_metrics(metrics)
            except Exception:
                pass

    def log_model(self, model: Any, artifact_path: str):
        if _MLFLOW_AVAILABLE:
            try:
                mlflow.sklearn.log_model(model, artifact_path)
            except Exception:
                pass

    def record_fallback(
        self,
        *,
        script: str,
        disease: str,
        dataset_path: Path,
        model_path: Path,
        params: Dict[str, Any],
        metrics: Dict[str, float],
        stage: str = "staging",
        extra: Optional[Dict[str, Any]] = None,
    ):
        """Append a JSON entry to models/registry.json as a simple registry."""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        rec = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "script": script,
            "disease": disease,
            "dataset_path": str(dataset_path),
            "dataset_sha256": sha256_file(dataset_path),
            "model_path": str(model_path),
            "params": params,
            "metrics": metrics,
            "stage": stage,
        }
        if extra:
            rec.update(extra)

        data = []
        if self.registry_path.exists():
            try:
                data = json.loads(self.registry_path.read_text())
            except Exception:
                data = []
        data.append(rec)
        self.registry_path.write_text(json.dumps(data, indent=2))