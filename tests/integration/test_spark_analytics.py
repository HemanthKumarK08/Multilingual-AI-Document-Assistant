"""
Integration tests for PySpark Telemetry Analytics Pipeline (scripts/run_spark_analytics.py)
"""

import json
from pathlib import Path
import pytest
from scripts.export_telemetry_parquet import export_parquet_lake
from scripts.run_spark_analytics import run_spark_analytics


@pytest.fixture(scope="module")
def spark_fixture_data(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("spark_telemetry_test")
    validated_dir = base_dir / "validated"
    parquet_dir = base_dir / "parquet"
    analytics_dir = base_dir / "analytics"
    validated_dir.mkdir(parents=True)

    # Write small batch of events
    events = [
        {
            "schema_version": "1.0",
            "event_id": f"evt-{i}",
            "event_type": "query_completed",
            "timestamp": "2026-09-15T10:00:00Z",
            "date": "2026-09-15",
            "hour": 10,
            "language": "kn" if i % 2 == 0 else "hi",
            "script": "kannada" if i % 2 == 0 else "devanagari",
            "is_code_mixed": False,
            "variant_count": 3,
            "candidate_count": 20,
            "retrieved_chunk_count": 4,
            "retrieval_latency_ms": 20.0 + i,
            "reranking_latency_ms": 2.0,
            "generation_latency_ms": 100.0 + i * 10,
            "total_latency_ms": 122.0 + i * 11,
            "provider": "mock",
            "answer_mode": "grounded" if i < 8 else "fallback",
            "fallback_used": (i >= 8),
            "citation_count": 2 if i < 8 else 0,
            "citation_valid": (i < 8),
            "grounded": (i < 8),
            "error": False,
        }
        for i in range(10)
    ]

    test_jsonl = validated_dir / "query_completed.jsonl"
    with open(test_jsonl, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    export_parquet_lake(validated_dir, parquet_dir)

    return {
        "parquet_dir": parquet_dir,
        "analytics_dir": analytics_dir,
        "record_count": 10,
    }


def test_spark_analytics_computation(spark_fixture_data):
    parquet_dir = spark_fixture_data["parquet_dir"]
    analytics_dir = spark_fixture_data["analytics_dir"]

    summary_metrics = run_spark_analytics(
        parquet_dir=parquet_dir,
        analytics_dir=analytics_dir,
    )

    assert summary_metrics["source_record_count"] == 10
    assert summary_metrics["total_queries"] == 10
    assert summary_metrics["grounded_answer_rate"] == 80.0
    assert summary_metrics["fallback_rate"] == 20.0

    # Verify manifest
    manifest_path = analytics_dir / "manifest.json"
    assert manifest_path.exists()
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        assert manifest["input_records_processed"] == 10
        assert manifest["privacy_audit_status"] == "COMPLIANT_ZERO_RAW_DATA"

    # Verify language metrics
    lang_path = analytics_dir / "language_metrics.json"
    assert lang_path.exists()
    with open(lang_path, "r", encoding="utf-8") as f:
        languages = json.load(f)
        assert "language_distribution" in languages
        kn = languages["language_distribution"]["kn"]
        assert kn["count"] == 5
        assert kn["percentage"] == 50.0

    # Verify retrieval metrics
    retrieval_path = analytics_dir / "retrieval_metrics.json"
    assert retrieval_path.exists()
    with open(retrieval_path, "r", encoding="utf-8") as f:
        retrieval = json.load(f)
        assert retrieval["avg_retrieval_latency_ms"] > 0
        assert retrieval["avg_candidate_count"] == 20.0

    # Verify RAG metrics
    rag_path = analytics_dir / "rag_metrics.json"
    assert rag_path.exists()
    with open(rag_path, "r", encoding="utf-8") as f:
        rag = json.load(f)
        assert rag["grounded_answer_rate"] == 80.0
        assert rag["fallback_answer_rate"] == 20.0
        assert rag["citation_validity_rate"] == 80.0
