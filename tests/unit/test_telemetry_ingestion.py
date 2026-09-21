"""
Unit tests for Telemetry Ingestion Pipeline (scripts/ingest_telemetry.py)
"""

import json
from pathlib import Path
import pytest
from scripts.ingest_telemetry import ingest_telemetry


def test_ingestion_valid_and_rejected_separation(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    validated_dir = tmp_path / "validated"
    rejected_dir = tmp_path / "rejected"
    raw_dir.mkdir(parents=True)

    # Prepare raw JSONL file with valid and invalid entries
    test_jsonl = raw_dir / "test_events.jsonl"
    events = [
        # Valid event
        {
            "schema_version": "1.0",
            "event_id": "evt-001",
            "event_type": "query_completed",
            "timestamp": "2026-09-15T10:00:00Z",
            "language": "hi",
            "script": "devanagari",
            "retrieval_latency_ms": 15.2,
            "total_latency_ms": 120.0,
        },
        # Prohibited field event
        {
            "schema_version": "1.0",
            "event_id": "evt-002",
            "event_type": "query_completed",
            "timestamp": "2026-09-15T10:00:00Z",
            "raw_query": "sensitive student query text",
        },
        # Negative latency event
        {
            "schema_version": "1.0",
            "event_id": "evt-003",
            "event_type": "retrieval_completed",
            "timestamp": "2026-09-15T10:00:00Z",
            "latency_ms": -10.0,
        },
        # Non-JSON corrupted line
        "INVALID_NON_JSON_LINE",
    ]

    with open(test_jsonl, "w", encoding="utf-8") as f:
        for ev in events:
            if isinstance(ev, dict):
                f.write(json.dumps(ev) + "\n")
            else:
                f.write(ev + "\n")

    report = ingest_telemetry(
        input_dir=raw_dir,
        validated_dir=validated_dir,
        rejected_dir=rejected_dir,
    )

    assert report["total_records"] == 4
    assert report["valid_records"] == 1
    assert report["rejected_records"] == 3

    # Check that validated output file exists
    valid_files = list(validated_dir.glob("*.jsonl"))
    assert len(valid_files) > 0
    with open(valid_files[0], "r", encoding="utf-8") as f:
        valid_lines = [json.loads(line) for line in f if line.strip()]
        assert len(valid_lines) == 1
        assert valid_lines[0]["event_id"] == "evt-001"

    # Check rejected output file exists
    rej_files = list(rejected_dir.glob("*.jsonl"))
    assert len(rej_files) > 0
    with open(rej_files[0], "r", encoding="utf-8") as f:
        rej_lines = [json.loads(line) for line in f if line.strip()]
        assert len(rej_lines) == 3


def test_empty_raw_directory(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    validated_dir = tmp_path / "validated"
    rejected_dir = tmp_path / "rejected"
    raw_dir.mkdir(parents=True)

    report = ingest_telemetry(
        input_dir=raw_dir,
        validated_dir=validated_dir,
        rejected_dir=rejected_dir,
    )

    assert report["total_records"] == 0
    assert report["valid_records"] == 0
    assert report["rejected_records"] == 0
