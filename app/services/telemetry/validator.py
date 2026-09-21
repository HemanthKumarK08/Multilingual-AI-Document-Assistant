"""
Privacy and Telemetry Event Validator (Phase 7)
Enforces strict schema compliance, numeric non-negativity, and zero-PII boundaries.
"""

from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.telemetry.schema import (
    FORBIDDEN_FIELD_NAMES,
    PROHIBITED_VALUE_PATTERNS,
    SCHEMA_VERSION,
    SUPPORTED_EVENT_TYPES,
    SUPPORTED_LANGUAGES,
    SUPPORTED_PROVIDERS,
    SUPPORTED_SCRIPTS,
)


class TelemetryValidationError(ValueError):
    """Raised when a telemetry record fails validation or violates privacy contracts."""
    pass


class TelemetryValidator:
    """
    Validates individual telemetry events and batches against privacy and schema rules.
    """

    @classmethod
    def validate_event_dict(cls, event_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validates raw event dictionary. Returns (is_valid, error_reason).
        """
        if not isinstance(event_data, dict):
            return False, "Event record must be a JSON dictionary object"

        # 1. Check for forbidden key names
        for key in event_data.keys():
            normalized_key = key.strip().lower()
            if normalized_key in FORBIDDEN_FIELD_NAMES:
                return False, f"Privacy Violation: Prohibited field '{key}' detected in telemetry payload"

        # 2. Check event_type
        event_type = event_data.get("event_type")
        if not event_type or not isinstance(event_type, str):
            return False, "Missing or invalid 'event_type'"
        if event_type not in SUPPORTED_EVENT_TYPES:
            return False, f"Unsupported event_type '{event_type}'. Must be one of {SUPPORTED_EVENT_TYPES}"

        # 3. Check event_id
        event_id = event_data.get("event_id")
        if not event_id or not isinstance(event_id, str):
            return False, "Missing or invalid 'event_id'"

        # 4. Check timestamp
        timestamp = event_data.get("timestamp") or event_data.get("timestamp_utc")
        if not timestamp or not isinstance(timestamp, str):
            return False, "Missing or invalid 'timestamp'"
        try:
            # Validate ISO 8601 format
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except Exception:
            return False, f"Invalid ISO-8601 UTC timestamp: '{timestamp}'"

        # 5. Check numeric fields are non-negative and finite
        numeric_fields = [
            "latency_ms", "retrieval_latency_ms", "reranking_latency_ms",
            "generation_latency_ms", "total_latency_ms", "best_retrieval_score",
            "candidate_count", "selected_chunk_count", "retrieved_chunk_count",
            "variant_count", "citation_count", "hour"
        ]
        for num_field in numeric_fields:
            if num_field in event_data and event_data[num_field] is not None:
                val = event_data[num_field]
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    return False, f"Field '{num_field}' must be a number, got {type(val).__name__}"
                if val < 0:
                    return False, f"Field '{num_field}' must be non-negative, got {val}"

        # 6. Check language and script if present
        lang = event_data.get("language")
        if lang is not None:
            if not isinstance(lang, str):
                return False, "Field 'language' must be a string"
            if lang.lower() not in SUPPORTED_LANGUAGES and lang != "und":
                return False, f"Unsupported language '{lang}'. Must be one of {SUPPORTED_LANGUAGES}"

        script = event_data.get("script")
        if script is not None:
            if not isinstance(script, str):
                return False, "Field 'script' must be a string"
            if script.lower() not in SUPPORTED_SCRIPTS:
                return False, f"Unsupported script '{script}'. Must be one of {SUPPORTED_SCRIPTS}"

        # 7. Check provider if present
        provider = event_data.get("provider")
        if provider is not None:
            if not isinstance(provider, str):
                return False, "Field 'provider' must be a string"
            if provider.lower() not in SUPPORTED_PROVIDERS:
                return False, f"Unsupported provider '{provider}'. Must be one of {SUPPORTED_PROVIDERS}"

        # 8. Check string value lengths and prohibited patterns (emails, phone numbers, API keys)
        for k, v in event_data.items():
            if isinstance(v, str):
                # Reject arbitrary long text blocks that might contain leaked queries or documents
                if len(v) > 200 and k not in ("error_details", "fallback_reason"):
                    return False, f"Suspicious oversized text value in field '{k}' ({len(v)} chars)"
                
                # Check for regex patterns of PII / Credentials
                for pattern in PROHIBITED_VALUE_PATTERNS:
                    if re.search(pattern, v):
                        return False, f"Privacy Violation: Potential sensitive credential/PII pattern detected in '{k}'"

        return True, None

    @classmethod
    def enforce_event_dict(cls, event_data: Dict[str, Any]) -> None:
        """
        Validates event and raises TelemetryValidationError if invalid.
        """
        is_valid, reason = cls.validate_event_dict(event_data)
        if not is_valid:
            raise TelemetryValidationError(reason)
