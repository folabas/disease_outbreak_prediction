"""
Data versioning and reproducibility tracking for ML models.

This module tracks dataset versions, model versions, and their relationships
to ensure reproducibility of predictions and model training.
"""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
VERSION_FILE = BASE_DIR / "data" / ".data_version.json"


def compute_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return ""


def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """Get metadata for a file (size, mtime, hash)."""
    try:
        stat = file_path.stat()
        return {
            "path": str(file_path.relative_to(BASE_DIR)),
            "size_bytes": stat.st_size,
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "hash": compute_file_hash(file_path),
        }
    except Exception:
        return {}


def track_dataset_version(dataset_name: str, file_path: Path) -> Dict[str, Any]:
    """Track version information for a dataset file."""
    if not file_path.exists():
        return {}
    
    metadata = get_file_metadata(file_path)
    if not metadata:
        return {}
    
    # Load existing version tracking
    versions = {}
    if VERSION_FILE.exists():
        try:
            with open(VERSION_FILE, "r") as f:
                versions = json.load(f)
        except Exception:
            versions = {}
    
    # Initialize dataset tracking if needed
    if "datasets" not in versions:
        versions["datasets"] = {}
    
    if dataset_name not in versions["datasets"]:
        versions["datasets"][dataset_name] = []
    
    # Check if this version already exists
    existing = next(
        (v for v in versions["datasets"][dataset_name] if v.get("hash") == metadata["hash"]),
        None
    )
    
    if existing:
        return existing
    
    # Add new version entry
    version_entry = {
        "version": len(versions["datasets"][dataset_name]) + 1,
        "timestamp": datetime.utcnow().isoformat(),
        **metadata,
    }
    
    versions["datasets"][dataset_name].append(version_entry)
    
    # Save updated versions
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VERSION_FILE, "w") as f:
        json.dump(versions, f, indent=2)
    
    return version_entry


def get_dataset_version(dataset_name: str) -> Optional[Dict[str, Any]]:
    """Get the latest version information for a dataset."""
    if not VERSION_FILE.exists():
        return None
    
    try:
        with open(VERSION_FILE, "r") as f:
            versions = json.load(f)
        
        if "datasets" not in versions:
            return None
        
        dataset_versions = versions["datasets"].get(dataset_name, [])
        if not dataset_versions:
            return None
        
        # Return the latest version (last in list)
        return dataset_versions[-1]
    except Exception:
        return None


def track_model_version(model_name: str, model_path: Path, dataset_versions: Dict[str, str]) -> Dict[str, Any]:
    """Track version information for a trained model."""
    if not model_path.exists():
        return {}
    
    metadata = get_file_metadata(model_path)
    if not metadata:
        return {}
    
    # Load existing version tracking
    versions = {}
    if VERSION_FILE.exists():
        try:
            with open(VERSION_FILE, "r") as f:
                versions = json.load(f)
        except Exception:
            versions = {}
    
    # Initialize model tracking if needed
    if "models" not in versions:
        versions["models"] = {}
    
    if model_name not in versions["models"]:
        versions["models"][model_name] = []
    
    # Add new version entry
    version_entry = {
        "version": len(versions["models"][model_name]) + 1,
        "timestamp": datetime.utcnow().isoformat(),
        "dataset_versions": dataset_versions,  # Track which dataset versions were used
        **metadata,
    }
    
    versions["models"][model_name].append(version_entry)
    
    # Save updated versions
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VERSION_FILE, "w") as f:
        json.dump(versions, f, indent=2)
    
    return version_entry


def get_model_version(model_name: str) -> Optional[Dict[str, Any]]:
    """Get the latest version information for a model."""
    if not VERSION_FILE.exists():
        return None
    
    try:
        with open(VERSION_FILE, "r") as f:
            versions = json.load(f)
        
        if "models" not in versions:
            return None
        
        model_versions = versions["models"].get(model_name, [])
        if not model_versions:
            return None
        
        # Return the latest version
        return model_versions[-1]
    except Exception:
        return None


def get_data_freshness(dataset_name: str) -> Optional[Dict[str, Any]]:
    """Get data freshness information (last modified time, age)."""
    version_info = get_dataset_version(dataset_name)
    if not version_info:
        return None
    
    try:
        modified_time = datetime.fromisoformat(version_info["modified_time"])
        age_days = (datetime.utcnow() - modified_time.replace(tzinfo=None)).days
        
        return {
            "dataset": dataset_name,
            "last_modified": version_info["modified_time"],
            "age_days": age_days,
            "is_fresh": age_days < 30,  # Consider data fresh if less than 30 days old
            "version": version_info.get("version", 1),
        }
    except Exception:
        return None

