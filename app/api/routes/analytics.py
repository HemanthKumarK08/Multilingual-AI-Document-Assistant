"""
Analytics Endpoints (Phase 7 & Environment Separation)
Exposes precomputed PySpark big data analytics summaries and metrics for administrative dashboards.
Supports strict environment isolation: LIVE, TEST, FIXTURE, and ALL.
"""

import json
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings

router = APIRouter()


def _load_analytics_file(filename: str, environment: str = "live") -> Dict[str, Any]:
    """
    Helper to safely read precomputed analytics JSON files for the requested environment.
    """
    valid_envs = {"live", "test", "fixture", "all"}
    clean_env = environment.lower() if environment else "live"
    if clean_env not in valid_envs:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid environment '{environment}'. Must be one of: {sorted(list(valid_envs))}"
        )

    analytics_dir = settings.telemetry_analytics_path
    
    # Check environment subdirectory first (e.g. data/telemetry/analytics/live/summary_metrics.json)
    env_file_path = analytics_dir / clean_env / filename
    root_file_path = analytics_dir / filename

    target_path = env_file_path if env_file_path.exists() else root_file_path

    if not target_path.exists():
        return {
            "status": "pending_generation",
            "environment": clean_env,
            "message": f"Analytics file '{filename}' for environment '{clean_env}' has not yet been generated.",
            "data_available": False,
            "source_record_count": 0,
            "total_queries": 0,
        }

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "environment" not in data:
                data["environment"] = clean_env
            if "data_available" not in data:
                data["data_available"] = True
            return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read analytics file '{filename}' for environment '{clean_env}': {str(e)}"
        )


@router.get("/summary")
async def get_analytics_summary(
    environment: Literal["live", "test", "fixture", "all"] = Query(default="live", description="Analytics dataset environment")
):
    """Returns high-level executive analytics KPIs for the specified environment."""
    return _load_analytics_file("summary_metrics.json", environment)


@router.get("/volume")
async def get_volume_metrics(
    environment: Literal["live", "test", "fixture", "all"] = Query(default="live", description="Analytics dataset environment")
):
    """Returns query volume, event distributions, and temporal aggregations."""
    return _load_analytics_file("volume_metrics.json", environment)


@router.get("/languages")
async def get_language_metrics(
    environment: Literal["live", "test", "fixture", "all"] = Query(default="live", description="Analytics dataset environment")
):
    """Returns query distributions across English, Hindi, Kannada, Telugu, and Romanized/Code-Mixed varieties."""
    return _load_analytics_file("language_metrics.json", environment)


@router.get("/users")
async def get_user_metrics(
    environment: Literal["live", "test", "fixture", "all"] = Query(default="live", description="Analytics dataset environment")
):
    """Returns anonymous user activity, language profiles, and session metrics."""
    return _load_analytics_file("user_metrics.json", environment)


@router.get("/language-performance")
async def get_language_performance_metrics(
    environment: Literal["live", "test", "fixture", "all"] = Query(default="live", description="Analytics dataset environment")
):
    """Returns detailed performance matrix comparing English, Hindi, Kannada, Telugu, and Code-Mixed."""
    return _load_analytics_file("language_performance_metrics.json", environment)


@router.get("/language-switching")
async def get_language_switching_metrics(
    environment: Literal["live", "test", "fixture", "all"] = Query(default="live", description="Analytics dataset environment")
):
    """Returns multilingual language transition matrices and switching pair counts."""
    return _load_analytics_file("language_switching_metrics.json", environment)


@router.get("/code-mixed")
async def get_code_mixed_metrics(
    environment: Literal["live", "test", "fixture", "all"] = Query(default="live", description="Analytics dataset environment")
):
    """Returns comparative performance across Native Script, Romanized, and Code-Mixed queries."""
    return _load_analytics_file("code_mixed_metrics.json", environment)


@router.get("/documents")
async def get_document_analytics(
    environment: Literal["live", "test", "fixture", "all"] = Query(default="live", description="Analytics dataset environment")
):
    """Returns document-level interaction volume, unique users, languages used, and grounding rates."""
    return _load_analytics_file("document_metrics.json", environment)


@router.get("/retrieval")
async def get_retrieval_metrics(
    environment: Literal["live", "test", "fixture", "all"] = Query(default="live", description="Analytics dataset environment")
):
    """Returns dense, lexical, and hybrid retrieval latencies, candidate counts, and variant stats."""
    return _load_analytics_file("retrieval_metrics.json", environment)


@router.get("/rag")
async def get_rag_metrics(
    environment: Literal["live", "test", "fixture", "all"] = Query(default="live", description="Analytics dataset environment")
):
    """Returns grounded answer rates, citation validity rates, generation latencies, and provider shares."""
    return _load_analytics_file("rag_metrics.json", environment)


@router.get("/errors")
async def get_error_metrics(
    environment: Literal["live", "test", "fixture", "all"] = Query(default="live", description="Analytics dataset environment")
):
    """Returns system error counts, fallback rates, and reliability metrics."""
    return _load_analytics_file("error_metrics.json", environment)


@router.get("/timeseries")
async def get_timeseries_metrics(
    environment: Literal["live", "test", "fixture", "all"] = Query(default="live", description="Analytics dataset environment")
):
    """Returns daily and hourly operational trends."""
    return _load_analytics_file("timeseries_metrics.json", environment)


@router.post("/run-spark-pipeline")
async def run_spark_pipeline_endpoint():
    """Triggers an on-demand PySpark analytical batch aggregation over the Parquet data lake."""
    try:
        from scripts.run_spark_analytics import run_spark_analytics
        summaries = run_spark_analytics(
            parquet_dir=settings.telemetry_parquet_path,
            analytics_dir=settings.telemetry_analytics_path,
        )
        return {
            "status": "success",
            "message": "PySpark multi-environment analytics batch job completed successfully.",
            "summaries": summaries,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PySpark job failed: {str(e)}")


@router.get("/health")
async def get_analytics_health(
    environment: Literal["live", "test", "fixture", "all"] = Query(default="live", description="Analytics dataset environment")
):
    """Health check for analytics pipeline and data lake presence."""
    analytics_dir = settings.telemetry_analytics_path
    parquet_dir = settings.telemetry_parquet_path
    manifest_path = analytics_dir / environment / "manifest.json"
    if not manifest_path.exists():
        manifest_path = analytics_dir / "manifest.json"

    has_parquet = parquet_dir.exists() and any(parquet_dir.glob("**/*.parquet"))
    has_analytics = manifest_path.exists()

    return {
        "status": "healthy" if has_analytics else "ready",
        "environment": environment,
        "parquet_lake_present": has_parquet,
        "analytics_precomputed": has_analytics,
        "analytics_directory": str(analytics_dir),
        "parquet_directory": str(parquet_dir),
    }
