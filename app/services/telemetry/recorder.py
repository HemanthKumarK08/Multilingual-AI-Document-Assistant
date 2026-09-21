"""
Telemetry Recorder Module (Phase 7)
Validates and persists privacy-safe telemetry events into raw JSONL log stores.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.services.telemetry.models import (
    ErrorTelemetryEvent,
    RAGTelemetryEvent,
    RetrievalTelemetryEvent,
    UnifiedQueryTelemetryEvent,
)
from app.services.telemetry.validator import TelemetryValidator


class TelemetryRecorder:
    """
    Safely records structured telemetry events to JSON lines files with strict privacy validation.
    Avoids recording raw queries, document bodies, prompts, or secrets.
    """

    def __init__(self, telemetry_dir: Optional[str] = None):
        base_dir = Path(telemetry_dir or settings.TELEMETRY_DIRECTORY)
        self.raw_dir = base_dir / "raw"
        self.enabled = settings.TELEMETRY_ENABLED
        if self.enabled:
            self.raw_dir.mkdir(parents=True, exist_ok=True)

    def record_event(
        self,
        event: Union[RetrievalTelemetryEvent, RAGTelemetryEvent, UnifiedQueryTelemetryEvent, ErrorTelemetryEvent, Dict[str, Any]],
    ) -> bool:
        """
        Validates and appends a telemetry event to the appropriate raw JSONL log file.
        Returns True if successfully validated and recorded, False otherwise.
        """
        if not self.enabled:
            return False

        try:
            if isinstance(event, BaseModel):
                event_dict = event.model_dump()
                event_type = getattr(event, "event_type", "event")
                json_line = event.model_dump_json() + "\n"
            elif isinstance(event, dict):
                event_dict = event
                event_type = event.get("event_type", "event")
                import json
                json_line = json.dumps(event, ensure_ascii=False) + "\n"
            else:
                logger.warning(f"Unsupported telemetry event type: {type(event)}")
                return False

            # Strict privacy & contract validation
            TelemetryValidator.enforce_event_dict(event_dict)

            target_file = self.raw_dir / f"{event_type}.jsonl"
            with open(target_file, "a", encoding="utf-8") as f:
                f.write(json_line)
            return True

        except Exception as e:
            logger.warning(f"Failed to record validated telemetry event: {e}")
            return False


# Singleton instance
telemetry_recorder = TelemetryRecorder()
