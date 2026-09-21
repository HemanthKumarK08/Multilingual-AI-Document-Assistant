"""
Unit Tests for Phase 7 Telemetry Contract and Privacy Validation
"""

import pytest
from app.services.telemetry.models import UnifiedQueryTelemetryEvent, RetrievalTelemetryEvent, RAGTelemetryEvent
from app.services.telemetry.schema import FORBIDDEN_FIELD_NAMES, SCHEMA_VERSION
from app.services.telemetry.validator import TelemetryValidationError, TelemetryValidator


def test_valid_unified_event():
    event = UnifiedQueryTelemetryEvent(
        query_id="Q-TEST-001",
        language="kn",
        script="kannada",
        candidate_count=25,
        retrieved_chunk_count=5,
        retrieval_latency_ms=22.4,
        total_latency_ms=210.5,
    )
    is_valid, reason = TelemetryValidator.validate_event_dict(event.model_dump())
    assert is_valid is True
    assert reason is None


def test_forbidden_field_rejection():
    for forbidden in ["raw_query", "query", "prompt", "answer", "passage", "token", "api_key", "password"]:
        bad_payload = {
            "schema_version": SCHEMA_VERSION,
            "event_id": "test-id",
            "event_type": "query_completed",
            "timestamp": "2026-09-15T10:00:00Z",
            forbidden: "secret user query or prompt payload",
        }
        is_valid, reason = TelemetryValidator.validate_event_dict(bad_payload)
        assert is_valid is False
        assert "Privacy Violation: Prohibited field" in reason


def test_negative_numeric_rejection():
    bad_payload = {
        "schema_version": SCHEMA_VERSION,
        "event_id": "test-id",
        "event_type": "query_completed",
        "timestamp": "2026-09-15T10:00:00Z",
        "retrieval_latency_ms": -5.0,
    }
    is_valid, reason = TelemetryValidator.validate_event_dict(bad_payload)
    assert is_valid is False
    assert "must be non-negative" in reason


def test_unsupported_event_type():
    bad_payload = {
        "schema_version": SCHEMA_VERSION,
        "event_id": "test-id",
        "event_type": "unauthorized_tracking_event",
        "timestamp": "2026-09-15T10:00:00Z",
    }
    is_valid, reason = TelemetryValidator.validate_event_dict(bad_payload)
    assert is_valid is False
    assert "Unsupported event_type" in reason


def test_invalid_timestamp():
    bad_payload = {
        "schema_version": SCHEMA_VERSION,
        "event_id": "test-id",
        "event_type": "query_completed",
        "timestamp": "not-a-timestamp",
    }
    is_valid, reason = TelemetryValidator.validate_event_dict(bad_payload)
    assert is_valid is False
    assert "Invalid ISO-8601 UTC timestamp" in reason


def test_suspicious_oversized_string():
    bad_payload = {
        "schema_version": SCHEMA_VERSION,
        "event_id": "test-id",
        "event_type": "query_completed",
        "timestamp": "2026-09-15T10:00:00Z",
        "query_type": "A" * 300,
    }
    is_valid, reason = TelemetryValidator.validate_event_dict(bad_payload)
    assert is_valid is False
    assert "Suspicious oversized text value" in reason


def test_sensitive_pattern_rejection():
    bad_payload = {
        "schema_version": SCHEMA_VERSION,
        "event_id": "test-id",
        "event_type": "query_completed",
        "timestamp": "2026-09-15T10:00:00Z",
        "error_type": "leak student@example.com in error log",
    }
    is_valid, reason = TelemetryValidator.validate_event_dict(bad_payload)
    assert is_valid is False
    assert "Potential sensitive credential/PII pattern" in reason
