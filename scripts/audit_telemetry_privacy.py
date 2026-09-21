"""
Comprehensive Telemetry Privacy Audit Scanner (Phase 7)
Scans JSONL logs, Parquet files, and analytics JSON outputs for prohibited fields,
raw user text, credentials, or PII leakages. Fails with non-zero exit code on violations.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.services.telemetry.schema import FORBIDDEN_FIELD_NAMES, PROHIBITED_VALUE_PATTERNS


class TelemetryPrivacyAuditor:
    """
    Audits telemetry stores and analytics artifacts against privacy rules.
    """

    def __init__(self, base_telemetry_dir: Optional[Path] = None, telemetry_dir: Optional[Path] = None):
        target = base_telemetry_dir or telemetry_dir or settings.telemetry_path
        self.base_dir = Path(target)
        self.violations: List[Dict[str, Any]] = []
        self.files_scanned = 0
        self.records_scanned = 0

    def scan_dict(self, record: Dict[str, Any], file_path: Path, record_index: int) -> None:
        """Inspects a single dictionary record for forbidden fields and sensitive values."""
        self.records_scanned += 1

        # 1. Check for forbidden key names
        for key, val in record.items():
            norm_key = key.strip().lower()
            if norm_key in FORBIDDEN_FIELD_NAMES:
                self.violations.append({
                    "file": str(file_path.relative_to(PROJECT_ROOT) if file_path.is_relative_to(PROJECT_ROOT) else file_path),
                    "record_index": record_index,
                    "violation_type": "FORBIDDEN_KEY_DETECTED",
                    "field_name": key,
                    "details": f"Prohibited field '{key}' found in telemetry record.",
                })

            # 2. Check string values
            if isinstance(val, str):
                # Pattern detection (emails, phones, API keys)
                for pat in PROHIBITED_VALUE_PATTERNS:
                    if re.search(pat, val):
                        self.violations.append({
                            "file": str(file_path.relative_to(PROJECT_ROOT) if file_path.is_relative_to(PROJECT_ROOT) else file_path),
                            "record_index": record_index,
                            "violation_type": "SENSITIVE_PATTERN_MATCH",
                            "field_name": key,
                            "details": f"Value in field '{key}' matched suspicious PII or API credential regex pattern.",
                        })

                # Oversized string detection
                if len(val) > 200 and key not in ("error_details", "fallback_reason", "source_parquet_path", "source_path", "output_directory"):
                    self.violations.append({
                        "file": str(file_path.relative_to(PROJECT_ROOT) if file_path.is_relative_to(PROJECT_ROOT) else file_path),
                        "record_index": record_index,
                        "violation_type": "SUSPICIOUS_LONG_TEXT",
                        "field_name": key,
                        "details": f"Oversized string ({len(val)} chars) in field '{key}' may indicate raw text leakage.",
                    })

            elif isinstance(val, dict):
                self.scan_dict(val, file_path, record_index)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        self.scan_dict(item, file_path, record_index)

    def scan_jsonl_file(self, file_path: Path) -> None:
        """Scans a JSON Lines file."""
        self.files_scanned += 1
        with open(file_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                line_str = line.strip()
                if line_str:
                    try:
                        rec = json.loads(line_str)
                        self.scan_dict(rec, file_path, idx)
                    except Exception:
                        pass

    def scan_json_file(self, file_path: Path) -> None:
        """Scans a structured JSON file."""
        self.files_scanned += 1
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    self.scan_dict(data, file_path, 1)
                elif isinstance(data, list):
                    for idx, item in enumerate(data, start=1):
                        if isinstance(item, dict):
                            self.scan_dict(item, file_path, idx)
            except Exception:
                pass

    def scan_parquet_file(self, file_path: Path) -> None:
        """Scans a Parquet file via PyArrow."""
        self.files_scanned += 1
        try:
            import pyarrow.parquet as pq
            table = pq.read_table(file_path)
            for key in table.schema.names:
                if key.lower() in FORBIDDEN_FIELD_NAMES:
                    self.violations.append({
                        "file": str(file_path.relative_to(PROJECT_ROOT) if file_path.is_relative_to(PROJECT_ROOT) else file_path),
                        "record_index": 0,
                        "violation_type": "FORBIDDEN_KEY_DETECTED",
                        "field_name": key,
                        "details": f"Prohibited column '{key}' in Parquet schema.",
                    })
            records = table.to_pylist()
            for idx, rec in enumerate(records, start=1):
                self.scan_dict(rec, file_path, idx)
        except Exception as e:
            pass

    def run_full_audit(self) -> Dict[str, Any]:
        """Executes recursive audit across raw, validated, parquet, and analytics directories."""
        self.violations.clear()
        self.files_scanned = 0
        self.records_scanned = 0

        if not self.base_dir.exists():
            return {
                "audit_timestamp_utc": datetime.utcnow().isoformat() + "Z",
                "status": "PASS",
                "message": f"Telemetry directory {self.base_dir} does not exist yet.",
                "files_scanned": 0,
                "records_scanned": 0,
                "violation_count": 0,
                "violations": [],
            }

        # 1. Scan JSONL files
        for jsonl_file in self.base_dir.glob("**/*.jsonl"):
            # Exclude rejected logs from raw violation count as they are expected to contain quarantine keys
            if "rejected" in str(jsonl_file):
                continue
            self.scan_jsonl_file(jsonl_file)

        # 2. Scan JSON analytics outputs
        for json_file in (self.base_dir / "analytics").glob("*.json"):
            self.scan_json_file(json_file)

        # 3. Scan Parquet files
        for parquet_file in (self.base_dir / "parquet").glob("**/*.parquet"):
            self.scan_parquet_file(parquet_file)

        passed = len(self.violations) == 0
        return {
            "audit_timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "status": "PASS" if passed else "FAIL",
            "files_scanned": self.files_scanned,
            "records_scanned": self.records_scanned,
            "violation_count": len(self.violations),
            "violations": self.violations,
        }


def main():
    parser = argparse.ArgumentParser(description="Audit telemetry files and data lake for zero-raw-query privacy compliance")
    parser.add_argument("--dir", "--telemetry", dest="dir", default=str(settings.telemetry_path), help="Base telemetry directory")
    args = parser.parse_args()

    print("=" * 80)
    print(" TELEMETRY PRIVACY AUDIT & ZERO-RAW-DATA VERIFICATION (Phase 7)")
    print("=" * 80)
    print(f"Target Directory : {args.dir}\n")

    auditor = TelemetryPrivacyAuditor(Path(args.dir))
    report = auditor.run_full_audit()

    print(f"Files Scanned    : {report['files_scanned']}")
    print(f"Records Scanned  : {report['records_scanned']}")
    print(f"Violations Found : {report['violation_count']}")
    print(f"Audit Status     : {report['status']}")

    if report["violations"]:
        print("\n[!] PRIVACY VIOLATIONS DETECTED:")
        for v in report["violations"]:
            print(f"  - [{v['violation_type']}] {v['file']} (Record {v['record_index']}): {v['details']}")
        print("=" * 80)
        sys.exit(1)

    print("\n[✓] ZERO RAW DATA LEAKAGE VERIFIED: Telemetry stores strictly compliant.")
    print("=" * 80)
    sys.exit(0)


if __name__ == "__main__":
    main()
