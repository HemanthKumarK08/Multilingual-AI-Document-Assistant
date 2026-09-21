"""
Integration tests for Privacy Audit Engine (scripts/audit_telemetry_privacy.py)
"""

import json
from pathlib import Path
import pytest
from scripts.audit_telemetry_privacy import TelemetryPrivacyAuditor


def test_privacy_audit_clean_data(tmp_path: Path):
    telemetry_dir = tmp_path / "telemetry"
    raw_dir = telemetry_dir / "raw"
    raw_dir.mkdir(parents=True)

    clean_file = raw_dir / "clean_events.jsonl"
    clean_event = {
        "schema_version": "1.0",
        "event_id": "evt-001",
        "event_type": "query_completed",
        "timestamp": "2026-09-15T10:00:00Z",
        "language": "hi",
        "script": "devanagari",
        "candidate_count": 20,
        "retrieval_latency_ms": 22.0,
    }
    with open(clean_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(clean_event) + "\n")

    auditor = TelemetryPrivacyAuditor(base_telemetry_dir=telemetry_dir)
    report = auditor.run_full_audit()

    assert report["status"] == "PASS"
    assert report["violation_count"] == 0
    assert report["files_scanned"] == 1


def test_privacy_audit_detects_prohibited_fields(tmp_path: Path):
    telemetry_dir = tmp_path / "telemetry"
    raw_dir = telemetry_dir / "raw"
    raw_dir.mkdir(parents=True)

    poisoned_file = raw_dir / "leaked_query.jsonl"
    poisoned_event = {
        "schema_version": "1.0",
        "event_id": "evt-002",
        "event_type": "query_completed",
        "timestamp": "2026-09-15T10:00:00Z",
        "raw_query": "What is the fee structure for computer science engineering?",
    }
    with open(poisoned_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(poisoned_event) + "\n")

    auditor = TelemetryPrivacyAuditor(base_telemetry_dir=telemetry_dir)
    report = auditor.run_full_audit()

    assert report["status"] == "FAIL"
    assert report["violation_count"] > 0
    assert any(v["field_name"] == "raw_query" for v in report["violations"])


def test_privacy_audit_detects_pii_patterns(tmp_path: Path):
    telemetry_dir = tmp_path / "telemetry"
    raw_dir = telemetry_dir / "raw"
    raw_dir.mkdir(parents=True)

    poisoned_file = raw_dir / "leaked_email.jsonl"
    poisoned_event = {
        "schema_version": "1.0",
        "event_id": "evt-003",
        "event_type": "error",
        "timestamp": "2026-09-15T10:00:00Z",
        "error_type": "admin user leaked admin@university.edu token 123",
    }
    with open(poisoned_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(poisoned_event) + "\n")

    auditor = TelemetryPrivacyAuditor(base_telemetry_dir=telemetry_dir)
    report = auditor.run_full_audit()

    assert report["status"] == "FAIL"
    assert report["violation_count"] > 0
