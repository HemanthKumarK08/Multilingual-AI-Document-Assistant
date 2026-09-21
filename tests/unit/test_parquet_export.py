"""
Unit tests for Parquet Lake Export (scripts/export_telemetry_parquet.py)
"""

import json
from pathlib import Path
import pyarrow.parquet as pq
import pytest
from scripts.export_telemetry_parquet import export_parquet_lake


def test_parquet_export_and_partitioning(tmp_path: Path):
    validated_dir = tmp_path / "validated"
    parquet_dir = tmp_path / "parquet"
    validated_dir.mkdir(parents=True)

    test_file = validated_dir / "query_completed.jsonl"
    events = [
        {
            "schema_version": "1.0",
            "event_id": f"evt-{i}",
            "event_type": "query_completed",
            "timestamp": "2026-09-15T10:00:00Z" if i < 3 else "2026-09-16T11:00:00Z",
            "date": "2026-09-15" if i < 3 else "2026-09-16",
            "hour": 10 if i < 3 else 11,
            "language": "kn",
            "script": "kannada",
            "candidate_count": 20,
            "retrieved_chunk_count": 5,
            "retrieval_latency_ms": 25.0,
            "reranking_latency_ms": 2.0,
            "generation_latency_ms": 150.0,
            "total_latency_ms": 177.0,
            "provider": "mock",
            "answer_mode": "grounded",
            "fallback_used": False,
            "citation_count": 2,
            "citation_valid": True,
            "grounded": True,
            "error": False,
        }
        for i in range(5)
    ]

    with open(test_file, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    report = export_parquet_lake(
        validated_dir=validated_dir,
        parquet_dir=parquet_dir,
    )

    assert report["total_records_converted"] == 5
    assert report["partition_count"] == 2  # date=2026-09-15, date=2026-09-16

    # Verify parquet partition directories exist
    p1 = parquet_dir / "date=2026-09-15"
    p2 = parquet_dir / "date=2026-09-16"
    assert p1.exists()
    assert p2.exists()

    # Read back parquet with pyarrow
    dataset = pq.ParquetDataset(str(parquet_dir))
    table = dataset.read()
    assert table.num_rows == 5
