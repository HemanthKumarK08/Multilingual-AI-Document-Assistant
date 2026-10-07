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
            import os
            # Resolve current active telemetry environment
            active_env = os.environ.get("TELEMETRY_ENVIRONMENT")
            if not active_env:
                if os.environ.get("PYTEST_CURRENT_TEST") or settings.APP_ENV == "testing":
                    active_env = "test"
                else:
                    active_env = settings.TELEMETRY_ENVIRONMENT or "live"

            if isinstance(event, BaseModel):
                event_dict = event.model_dump()
                if not event_dict.get("telemetry_environment"):
                    event_dict["telemetry_environment"] = active_env
                    setattr(event, "telemetry_environment", active_env)
                event_type = getattr(event, "event_type", "event")
                json_line = event.model_dump_json() + "\n"
            elif isinstance(event, dict):
                event_dict = event
                if not event_dict.get("telemetry_environment"):
                    event_dict["telemetry_environment"] = active_env
                event_type = event.get("event_type", "event")
                import json
                json_line = json.dumps(event_dict, ensure_ascii=False) + "\n"
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
