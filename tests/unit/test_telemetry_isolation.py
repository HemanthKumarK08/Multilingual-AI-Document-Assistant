"""
Unit Tests for Telemetry Environment Isolation & HMAC Identity Derivation
"""

import pytest
from app.services.telemetry.user_identity import (
    generate_anonymous_user_id,
    generate_anonymous_session_id,
)
from app.services.telemetry.models import RAGTelemetryEvent, UnifiedQueryTelemetryEvent
from app.services.telemetry.validator import TelemetryValidator


def test_hmac_anonymous_user_derivation():
    sess_1 = "session-uuid-12345"
    sess_2 = "session-uuid-67890"

    user_1 = generate_anonymous_user_id(sess_1)
    user_2 = generate_anonymous_user_id(sess_2)

    assert user_1 is not None
    assert user_1.startswith("USER-")
    assert len(user_1) == 13  # USER- + 8 hex chars
    assert user_1 != user_2  # Different sessions yield distinct user IDs

    # Deterministic derivation for same session
    assert generate_anonymous_user_id(sess_1) == user_1

    # Empty inputs return None
    assert generate_anonymous_user_id(None) is None
    assert generate_anonymous_user_id("") is None

    # Fixture alias preservation
    assert generate_anonymous_user_id("USER-001") == "USER-001"
    assert generate_anonymous_user_id("USER-035") == "USER-035"


def test_hmac_anonymous_session_derivation():
    sess_1 = "session-uuid-12345"
    s_hash = generate_anonymous_session_id(sess_1)

    assert s_hash is not None
    assert s_hash.startswith("SES-")
    assert len(s_hash) == 12  # SES- + 8 hex chars
    assert generate_anonymous_session_id(None) is None


def test_telemetry_environment_validation():
    # Valid environments
    for env in ("live", "test", "fixture"):
        ev = RAGTelemetryEvent(
            query_id="Q-100",
            telemetry_environment=env,
            language="en",
            script="latin",
        )
        is_valid, reason = TelemetryValidator.validate_event_dict(ev.model_dump())
        assert is_valid is True
        assert reason is None

    # Invalid environment rejection
    bad_ev = {
        "schema_version": "1.0",
        "event_id": "evt-invalid-env",
        "event_type": "rag_response",
        "telemetry_environment": "untrusted_production_fake",
        "timestamp": "2026-10-07T10:00:00Z",
    }
    is_valid, reason = TelemetryValidator.validate_event_dict(bad_ev)
    assert is_valid is False
    assert "Unsupported telemetry_environment" in reason
