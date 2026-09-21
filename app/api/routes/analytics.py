"""
Analytics Endpoints (Phase 7)
Exposes precomputed PySpark big data analytics summaries and metrics for administrative dashboards.
"""

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.core.config import settings

router = APIRouter()


def _load_analytics_file(filename: str) -> Dict[str, Any]:
    """Helper to safely read precomputed analytics JSON files."""
    analytics_dir = settings.telemetry_analytics_path
    file_path = analytics_dir / filename

    if not file_path.exists():
        # Return structured fallback when analytics have not yet been run
        return {
            "status": "pending_generation",
            "message": f"Analytics file '{filename}' has not yet been generated. Run scripts/run_spark_analytics.py.",
            "data_available": False,
        }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["data_available"] = True
            return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read analytics file '{filename}': {str(e)}"
        )


@router.get("/summary")
async def get_analytics_summary():
    """Returns high-level executive analytics KPIs."""
    return _load_analytics_file("summary_metrics.json")


@router.get("/volume")
async def get_volume_metrics():
    """Returns query volume, event distributions, and temporal aggregations."""
    return _load_analytics_file("volume_metrics.json")


@router.get("/languages")
async def get_language_metrics():
    """Returns query distributions across English, Hindi, Kannada, Telugu, and Romanized/Code-Mixed varieties."""
    return _load_analytics_file("language_metrics.json")


@router.get("/retrieval")
async def get_retrieval_metrics():
    """Returns dense, lexical, and hybrid retrieval latencies, candidate counts, and variant stats."""
    return _load_analytics_file("retrieval_metrics.json")


@router.get("/rag")
async def get_rag_metrics():
    """Returns grounded answer rates, citation validity rates, generation latencies, and provider shares."""
    return _load_analytics_file("rag_metrics.json")


@router.get("/errors")
async def get_error_metrics():
    """Returns system error counts, fallback rates, and reliability metrics."""
    return _load_analytics_file("error_metrics.json")


@router.get("/timeseries")
async def get_timeseries_metrics():
    """Returns daily and hourly operational trends."""
    return _load_analytics_file("timeseries_metrics.json")


@router.get("/health")
async def get_analytics_health():
    """Health check for analytics pipeline and data lake presence."""
    analytics_dir = settings.telemetry_analytics_path
    parquet_dir = settings.telemetry_parquet_path
    manifest_path = analytics_dir / "manifest.json"

    has_parquet = parquet_dir.exists() and any(parquet_dir.glob("**/*.parquet"))
    has_analytics = manifest_path.exists()

    return {
        "status": "healthy" if has_analytics else "ready",
        "parquet_lake_present": has_parquet,
        "analytics_precomputed": has_analytics,
        "analytics_directory": str(analytics_dir),
        "parquet_directory": str(parquet_dir),
    }
