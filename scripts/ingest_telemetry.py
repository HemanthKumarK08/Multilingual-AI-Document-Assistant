"""
Telemetry Batch Ingestion & Privacy Validation Script (Phase 7)
Reads raw JSONL telemetry streams, validates them against strict privacy contracts,
and partitions records into validated and rejected stores.
"""

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.services.telemetry.validator import TelemetryValidator


def ingest_telemetry(
    input_dir: Path,
    validated_dir: Path,
    rejected_dir: Path,
) -> Dict[str, Any]:
    """
    Ingests all raw JSONL telemetry files, validates privacy and schema rules,
    and outputs validated and rejected records.
    """
    input_dir = Path(input_dir)
    validated_dir = Path(validated_dir)
    rejected_dir = Path(rejected_dir)

    validated_dir.mkdir(parents=True, exist_ok=True)
    rejected_dir.mkdir(parents=True, exist_ok=True)

    total_records = 0
    valid_records = 0
    rejected_records = 0

    rejection_reasons: Counter = Counter()
    event_type_distribution: Counter = Counter()
    dates_seen: Set[str] = set()
    seen_event_ids: Set[str] = set()

    # Collect input JSONL files
    if input_dir.is_file():
        input_files = [input_dir]
    elif input_dir.is_dir():
        input_files = sorted(list(input_dir.glob("*.jsonl")))
    else:
        input_files = []

    if not input_files:
        print(f"[Notice] No raw JSONL telemetry files found in {input_dir}")
        return {
            "total_records": 0,
            "valid_records": 0,
            "rejected_records": 0,
            "event_type_distribution": {},
            "rejection_reasons": {},
            "date_range": None,
        }

    # Open target file handles for validated streams
    validated_handles: Dict[str, Any] = {}
    rejected_log_path = rejected_dir / f"rejected_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
    rejected_handle = open(rejected_log_path, "a", encoding="utf-8")

    try:
        for file_path in input_files:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_idx, line in enumerate(f, start=1):
                    line_str = line.strip()
                    if not line_str:
                        continue

                    total_records += 1
                    try:
                        event_data = json.loads(line_str)
                    except json.JSONDecodeError as jde:
                        rejected_records += 1
                        rejection_reasons["Malformed JSON syntax"] += 1
                        rejected_handle.write(json.dumps({
                            "source_file": file_path.name,
                            "line_number": line_idx,
                            "reason": f"Malformed JSON: {str(jde)}",
                            "raw_content_preview": line_str[:100],
                            "rejected_at": datetime.utcnow().isoformat(),
                        }) + "\n")
                        continue

                    # Validate against privacy & contract rules
                    is_valid, reason = TelemetryValidator.validate_event_dict(event_data)

                    if not is_valid:
                        rejected_records += 1
                        rejection_reasons[reason or "Validation failure"] += 1
                        # Safe redacted rejection logging
                        safe_record_keys = list(event_data.keys())
                        rejected_handle.write(json.dumps({
                            "source_file": file_path.name,
                            "line_number": line_idx,
                            "reason": reason,
                            "keys_present": safe_record_keys,
                            "rejected_at": datetime.utcnow().isoformat(),
                        }) + "\n")
                        continue

                    # Deduplicate within current run
                    event_id = event_data.get("event_id")
                    if event_id in seen_event_ids:
                        continue
                    if event_id:
                        seen_event_ids.add(event_id)

                    event_type = event_data.get("event_type", "unknown")
                    event_type_distribution[event_type] += 1
                    valid_records += 1

                    # Date tracking
                    dt = event_data.get("date")
                    if not dt and "timestamp" in event_data:
                        dt = event_data["timestamp"][:10]
                    if dt:
                        dates_seen.add(dt)

                    # Ensure standard partition fields
                    if "schema_version" not in event_data:
                        event_data["schema_version"] = "1.0"
                    if "date" not in event_data and dt:
                        event_data["date"] = dt
                    if "hour" not in event_data and "timestamp" in event_data:
                        try:
                            event_data["hour"] = int(event_data["timestamp"][11:13])
                        except Exception:
                            event_data["hour"] = 0

                    if event_type not in validated_handles:
                        target_validated_path = validated_dir / f"{event_type}.jsonl"
                        validated_handles[event_type] = open(target_validated_path, "a", encoding="utf-8")

                    validated_handles[event_type].write(json.dumps(event_data, ensure_ascii=False) + "\n")

    finally:
        for h in validated_handles.values():
            h.close()
        rejected_handle.close()

    date_range = None
    if dates_seen:
        sorted_dates = sorted(list(dates_seen))
        date_range = {"start_date": sorted_dates[0], "end_date": sorted_dates[-1]}

    summary = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "input_directory": str(input_dir),
        "validated_directory": str(validated_dir),
        "rejected_directory": str(rejected_dir),
        "total_records": total_records,
        "valid_records": valid_records,
        "rejected_records": rejected_records,
        "event_type_distribution": dict(event_type_distribution),
        "rejection_reasons": dict(rejection_reasons),
        "date_range": date_range,
    }

    return summary


def main():
    parser = argparse.ArgumentParser(description="Ingest and validate raw JSONL telemetry streams")
    parser.add_argument("--input", default=str(settings.telemetry_raw_path), help="Input raw directory or JSONL file")
    parser.add_argument("--output", default=str(settings.telemetry_validated_path), help="Output validated directory")
    parser.add_argument("--rejected", default=str(settings.telemetry_rejected_path), help="Output rejected directory")
    args = parser.parse_args()

    print("=" * 80)
    print(" TELEMETRY INGESTION & PRIVACY VALIDATION PIPELINE (Phase 7)")
    print("=" * 80)
    print(f"Input Directory     : {args.input}")
    print(f"Validated Directory : {args.output}")
    print(f"Rejected Directory  : {args.rejected}\n")

    summary = ingest_telemetry(
        input_dir=Path(args.input),
        validated_dir=Path(args.output),
        rejected_dir=Path(args.rejected),
    )

    print(f"Total Input Records : {summary['total_records']}")
    print(f"Valid Records       : {summary['valid_records']}")
    print(f"Rejected Records    : {summary['rejected_records']}")
    if summary['date_range']:
        print(f"Date Range          : {summary['date_range']['start_date']} to {summary['date_range']['end_date']}")

    if summary['event_type_distribution']:
        print("\nEvent Type Breakdown:")
        for ev_type, count in summary['event_type_distribution'].items():
            print(f"  - {ev_type:<25}: {count}")

    if summary['rejection_reasons']:
        print("\nRejection Reasons:")
        for reason, count in summary['rejection_reasons'].items():
            print(f"  - {reason:<45}: {count}")

    print("=" * 80)


if __name__ == "__main__":
    main()
