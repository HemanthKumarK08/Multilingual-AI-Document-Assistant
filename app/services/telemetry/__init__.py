"""
Telemetry Service Package (Phase 7)
"""

from app.services.telemetry.models import (
    ErrorTelemetryEvent,
    RAGTelemetryEvent,
    RetrievalTelemetryEvent,
    UnifiedQueryTelemetryEvent,
)
from app.services.telemetry.recorder import TelemetryRecorder, telemetry_recorder
from app.services.telemetry.schema import SCHEMA_VERSION
from app.services.telemetry.validator import TelemetryValidationError, TelemetryValidator

__all__ = [
    "SCHEMA_VERSION",
    "RetrievalTelemetryEvent",
    "RAGTelemetryEvent",
    "UnifiedQueryTelemetryEvent",
    "ErrorTelemetryEvent",
    "TelemetryRecorder",
    "telemetry_recorder",
    "TelemetryValidator",
    "TelemetryValidationError",
]
