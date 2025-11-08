import os
from typing import List


def project_root() -> str:
    """Resolve the project root directory (parent of backend/)."""
    # backend/app/core/config.py -> backend/app/core -> backend/app -> backend
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.abspath(os.path.join(backend_dir, ".."))


MODELS_DIR = os.path.join(project_root(), "models")
DATA_DIR = os.path.join(project_root(), "data")
REPORTS_DIR = os.path.join(project_root(), "reports", "production")


ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def resolve_path(*parts: str) -> str:
    return os.path.join(project_root(), *parts)