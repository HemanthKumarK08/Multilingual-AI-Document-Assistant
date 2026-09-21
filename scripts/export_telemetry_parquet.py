"""
Validated Telemetry to Partitioned Parquet Data Lake Exporter (Phase 7)
Converts validated JSONL telemetry records into partitioned columnar Parquet files
optimized for local PySpark batch analytics.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

import pyarrow as pa
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings


# Standardized PyArrow Schema for Telemetry Parquet Data Lake
TELEMETRY_ARROW_SCHEMA = pa.schema([
    ("schema_version", pa.string()),
    ("event_id", pa.string()),
    ("event_type", pa.string()),
    ("timestamp", pa.string()),
    ("date", pa.string()),
    ("hour", pa.int32()),
    ("request_id_hash", pa.string()),
    ("query_id", pa.string()),
    ("retrieval_id", pa.string()),
    ("language", pa.string()),
    ("script", pa.string()),
    ("query_type", pa.string()),
    ("is_code_mixed", pa.bool_()),
    ("variant_count", pa.int32()),
    ("candidate_count", pa.int32()),
    ("retrieved_chunk_count", pa.int32()),
    ("selected_chunk_count", pa.int32()),
    ("best_retrieval_score", pa.float64()),
    ("latency_ms", pa.float64()),
    ("retrieval_latency_ms", pa.float64()),
    ("reranking_latency_ms", pa.float64()),
    ("generation_latency_ms", pa.float64()),
    ("total_latency_ms", pa.float64()),
    ("provider", pa.string()),
    ("answer_mode", pa.string()),
    ("fallback_used", pa.bool_()),
    ("fallback_reason", pa.string()),
    ("citation_count", pa.int32()),
    ("citation_valid", pa.bool_()),
    ("grounded", pa.bool_()),
    ("error", pa.bool_()),
    ("error_type", pa.string()),
])


def normalize_record_for_parquet(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures all schema fields are present with correct scalar default types."""
    ts = rec.get("timestamp") or rec.get("timestamp_utc") or datetime.utcnow().isoformat()
    dt = rec.get("date") or ts[:10]
    hr = rec.get("hour")
    if hr is None:
        try:
            hr = int(ts[11:13])
        except Exception:
            hr = 0

    return {
        "schema_version": str(rec.get("schema_version", "1.0")),
        "event_id": str(rec.get("event_id", "")),
        "event_type": str(rec.get("event_type", "unknown")),
        "timestamp": str(ts),
        "date": str(dt),
        "hour": int(hr),
        "request_id_hash": str(rec.get("request_id_hash", "")),
        "query_id": str(rec.get("query_id", "")),
        "retrieval_id": str(rec.get("retrieval_id", "")),
        "language": str(rec.get("language", "und")),
        "script": str(rec.get("script", "unknown")),
        "query_type": str(rec.get("query_type", "cross_lingual_fact")),
        "is_code_mixed": bool(rec.get("is_code_mixed", False)),
        "variant_count": int(rec.get("variant_count", 1)),
        "candidate_count": int(rec.get("candidate_count", 0)),
        "retrieved_chunk_count": int(rec.get("retrieved_chunk_count", rec.get("selected_chunk_count", 0))),
        "selected_chunk_count": int(rec.get("selected_chunk_count", rec.get("retrieved_chunk_count", 0))),
        "best_retrieval_score": float(rec.get("best_retrieval_score", 0.0)),
        "latency_ms": float(rec.get("latency_ms", rec.get("total_latency_ms", 0.0))),
        "retrieval_latency_ms": float(rec.get("retrieval_latency_ms", 0.0)),
        "reranking_latency_ms": float(rec.get("reranking_latency_ms", 0.0)),
        "generation_latency_ms": float(rec.get("generation_latency_ms", 0.0)),
        "total_latency_ms": float(rec.get("total_latency_ms", rec.get("latency_ms", 0.0))),
        "provider": str(rec.get("provider", "mock")),
        "answer_mode": str(rec.get("answer_mode", "grounded")),
        "fallback_used": bool(rec.get("fallback_used", False)),
        "fallback_reason": str(rec.get("fallback_reason") or ""),
        "citation_count": int(rec.get("citation_count", 0)),
        "citation_valid": bool(rec.get("citation_valid", True)),
        "grounded": bool(rec.get("grounded", rec.get("answer_grounded", True))),
        "error": bool(rec.get("error", False)),
        "error_type": str(rec.get("error_type") or ""),
    }


def export_parquet_lake(
    validated_dir: Path,
    parquet_dir: Path,
) -> Dict[str, Any]:
    """
    Reads validated JSONL files and writes partitioned Parquet tables.
    """
    validated_dir = Path(validated_dir)
    parquet_dir = Path(parquet_dir)
    parquet_dir.mkdir(parents=True, exist_ok=True)

    jsonl_files = sorted(list(validated_dir.glob("*.jsonl"))) if validated_dir.exists() else []
    if not jsonl_files:
        print(f"[Notice] No validated JSONL files found in {validated_dir}")
        return {
            "total_records_converted": 0,
            "partition_count": 0,
            "parquet_directory": str(parquet_dir),
        }

    records: List[Dict[str, Any]] = []
    for jf in jsonl_files:
        with open(jf, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        raw_data = json.loads(line_str)
                        normalized = normalize_record_for_parquet(raw_data)
                        records.append(normalized)
                    except Exception as e:
                        continue

    if not records:
        print("[Notice] Zero valid records parsed for Parquet conversion.")
        return {
            "total_records_converted": 0,
            "partition_count": 0,
            "parquet_directory": str(parquet_dir),
        }

    # Convert to PyArrow Table
    dict_columns = {col_name: [r[col_name] for r in records] for col_name in TELEMETRY_ARROW_SCHEMA.names}
    table = pa.Table.from_pydict(dict_columns, schema=TELEMETRY_ARROW_SCHEMA)

    # Write partitioned dataset by date and event_type
    pq.write_to_dataset(
        table,
        root_path=str(parquet_dir),
        partition_cols=["date", "event_type"],
        use_dictionary=True,
        compression="SNAPPY",
        existing_data_behavior="overwrite_or_ignore",
    )

    # Count generated partition folders
    partition_dirs = [p for p in parquet_dir.glob("date=*/event_type=*") if p.is_dir()]

    return {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "total_records_converted": len(records),
        "partition_count": len(partition_dirs),
        "parquet_directory": str(parquet_dir),
        "schema_fields": TELEMETRY_ARROW_SCHEMA.names,
    }


def main():
    parser = argparse.ArgumentParser(description="Export validated JSONL telemetry to partitioned Parquet Data Lake")
    parser.add_argument("--input", default=str(settings.telemetry_validated_path), help="Input validated JSONL directory")
    parser.add_argument("--output", default=str(settings.telemetry_parquet_path), help="Output Parquet directory")
    args = parser.parse_args()

    print("=" * 80)
    print(" PARQUET DATA LAKE EXPORTER (Phase 7)")
    print("=" * 80)
    print(f"Validated Input   : {args.input}")
    print(f"Parquet Lake Path : {args.output}\n")

    result = export_parquet_lake(
        validated_dir=Path(args.input),
        parquet_dir=Path(args.output),
    )

    print(f"Records Converted : {result['total_records_converted']}")
    print(f"Partitions Active : {result['partition_count']}")
    print(f"Parquet Output    : {result['parquet_directory']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
