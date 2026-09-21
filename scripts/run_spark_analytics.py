"""
PySpark Batch Analytics Pipeline (Phase 7)
Executes local PySpark aggregations over partitioned Parquet data lakes,
producing deterministic summary, language, retrieval, RAG, reliability, and time-series JSON metrics.
"""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings


def setup_spark_environment() -> None:
    """Configures environment variables for local PySpark execution on macOS Apple Silicon."""
    # 1. Prefer Homebrew OpenJDK 17 if available
    jdk17_path = "/opt/homebrew/opt/openjdk@17"
    if os.path.exists(jdk17_path):
        os.environ["JAVA_HOME"] = jdk17_path
        os.environ["PATH"] = f"{jdk17_path}/bin:" + os.environ.get("PATH", "")

    # 2. Avoid path-with-colon classpath issues by symlinking SPARK_HOME if needed
    venv_pyspark = Path(sys.prefix) / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages" / "pyspark"
    if venv_pyspark.exists():
        symlink_target = Path("/tmp/aiml_pyspark_home")
        try:
            if symlink_target.is_symlink() or symlink_target.exists():
                symlink_target.unlink()
            symlink_target.symlink_to(venv_pyspark)
            os.environ["SPARK_HOME"] = str(symlink_target)
        except Exception:
            pass

    # 3. Synchronize python executable between driver and worker
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable


def run_spark_analytics(
    parquet_dir: Path,
    analytics_dir: Path,
) -> Dict[str, Any]:
    """
    Executes PySpark analytical jobs and serializes structured JSON outputs.
    """
    setup_spark_environment()
    parquet_dir = Path(parquet_dir)
    analytics_dir = Path(analytics_dir)
    analytics_dir.mkdir(parents=True, exist_ok=True)

    from pyspark.sql import SparkSession
    import pyspark.sql.functions as F
    from pyspark.sql.types import DoubleType, IntegerType

    spark = (
        SparkSession.builder
        .master(settings.SPARK_MASTER)
        .appName(settings.SPARK_APP_NAME)
        .config("spark.driver.memory", settings.SPARK_DRIVER_MEMORY)
        .config("spark.sql.shuffle.partitions", str(settings.SPARK_SHUFFLE_PARTITIONS))
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )

    now_iso = datetime.utcnow().isoformat() + "Z"

    try:
        # Check if parquet lake has data
        parquet_files = list(parquet_dir.glob("**/*.parquet"))
        if not parquet_files:
            print(f"[Notice] No parquet files found in {parquet_dir}. Writing default baseline metrics.")
            empty_summary = {
                "generated_at_utc": now_iso,
                "source_record_count": 0,
                "total_events": 0,
                "total_queries": 0,
                "grounded_answer_rate": 0.0,
                "fallback_rate": 0.0,
                "avg_total_latency_ms": 0.0,
            }
            with open(analytics_dir / "summary_metrics.json", "w", encoding="utf-8") as f:
                json.dump(empty_summary, f, indent=2)
            return empty_summary

        df = spark.read.parquet(str(parquet_dir))
        total_records = df.count()

        # Cache DataFrame for repeated aggregations
        df.cache()

        # ----------------------------------------------------------------------
        # A. Volume Analytics
        # ----------------------------------------------------------------------
        event_types_df = df.groupBy("event_type").count().collect()
        event_types_dict = {str(row["event_type"]): row["count"] for row in event_types_df}

        daily_df = df.groupBy("date").count().orderBy("date").collect()
        daily_dict = {str(row["date"]): row["count"] for row in daily_df}

        hourly_df = df.groupBy("hour").count().orderBy("hour").collect()
        hourly_dict = {str(row["hour"]): row["count"] for row in hourly_df}

        query_events_count = event_types_dict.get("query_completed", 0)
        retrieval_events_count = event_types_dict.get("retrieval_completed", 0)
        rag_events_count = event_types_dict.get("rag_response", 0)
        error_events_count = event_types_dict.get("error", 0)

        volume_metrics = {
            "generated_at_utc": now_iso,
            "source_record_count": total_records,
            "total_events": total_records,
            "query_completed_count": query_events_count,
            "retrieval_completed_count": retrieval_events_count,
            "rag_response_count": rag_events_count,
            "error_count": error_events_count,
            "events_by_type": event_types_dict,
            "events_by_date": daily_dict,
            "events_by_hour": hourly_dict,
        }

        # ----------------------------------------------------------------------
        # B. Language Analytics (Filtered to queries / RAG events)
        # ----------------------------------------------------------------------
        queries_df = df.filter(F.col("event_type").isin("query_completed", "rag_response"))
        q_count = queries_df.count()

        lang_counts_df = queries_df.groupBy("language").agg(
            F.count("*").alias("count"),
            F.avg("total_latency_ms").alias("avg_latency_ms"),
            F.sum(F.when(F.col("fallback_used") == True, 1).otherwise(0)).alias("fallback_count")
        ).collect()

        language_metrics_dict = {}
        for row in lang_counts_df:
            cnt = row["count"]
            fb_cnt = row["fallback_count"] or 0
            language_metrics_dict[row["language"]] = {
                "count": cnt,
                "percentage": round((cnt / max(1, q_count)) * 100.0, 2),
                "avg_latency_ms": round(row["avg_latency_ms"] or 0.0, 2),
                "fallback_count": fb_cnt,
                "fallback_rate": round((fb_cnt / max(1, cnt)) * 100.0, 2),
            }

        script_counts_df = queries_df.groupBy("script").count().collect()
        script_dict = {row["script"]: row["count"] for row in script_counts_df}

        code_mixed_count = queries_df.filter(F.col("is_code_mixed") == True).count()

        language_metrics = {
            "generated_at_utc": now_iso,
            "total_queries_analyzed": q_count,
            "language_distribution": language_metrics_dict,
            "script_distribution": script_dict,
            "code_mixed_queries_count": code_mixed_count,
            "code_mixed_percentage": round((code_mixed_count / max(1, q_count)) * 100.0, 2),
        }

        # ----------------------------------------------------------------------
        # C. Retrieval Analytics
        # ----------------------------------------------------------------------
        retrieval_stats = df.select(
            F.avg("retrieval_latency_ms").alias("avg_retrieval_latency"),
            F.expr("percentile_approx(retrieval_latency_ms, 0.50)").alias("p50_retrieval_latency"),
            F.expr("percentile_approx(retrieval_latency_ms, 0.95)").alias("p95_retrieval_latency"),
            F.avg("candidate_count").alias("avg_candidates"),
            F.avg("retrieved_chunk_count").alias("avg_retrieved_chunks"),
            F.avg("variant_count").alias("avg_variants"),
            F.avg("reranking_latency_ms").alias("avg_reranking_latency"),
            F.avg("best_retrieval_score").alias("avg_best_score"),
        ).collect()[0]

        retrieval_by_lang_df = df.groupBy("language").agg(
            F.avg("retrieval_latency_ms").alias("avg_latency"),
            F.avg("candidate_count").alias("avg_candidates"),
            F.avg("variant_count").alias("avg_variants"),
        ).collect()
        retrieval_by_lang = {
            row["language"]: {
                "avg_latency_ms": round(row["avg_latency"] or 0.0, 2),
                "avg_candidates": round(row["avg_candidates"] or 0.0, 2),
                "avg_variants": round(row["avg_variants"] or 0.0, 2),
            }
            for row in retrieval_by_lang_df
        }

        retrieval_metrics = {
            "generated_at_utc": now_iso,
            "avg_retrieval_latency_ms": round(retrieval_stats["avg_retrieval_latency"] or 0.0, 2),
            "p50_retrieval_latency_ms": round(retrieval_stats["p50_retrieval_latency"] or 0.0, 2),
            "p95_retrieval_latency_ms": round(retrieval_stats["p95_retrieval_latency"] or 0.0, 2),
            "avg_candidate_count": round(retrieval_stats["avg_candidates"] or 0.0, 2),
            "avg_retrieved_chunk_count": round(retrieval_stats["avg_retrieved_chunks"] or 0.0, 2),
            "avg_query_variant_count": round(retrieval_stats["avg_variants"] or 1.0, 2),
            "avg_reranking_latency_ms": round(retrieval_stats["avg_reranking_latency"] or 0.0, 2),
            "avg_best_retrieval_score": round(retrieval_stats["avg_best_score"] or 0.0, 4),
            "retrieval_by_language": retrieval_by_lang,
        }

        # ----------------------------------------------------------------------
        # D. Grounded RAG and Generation Analytics
        # ----------------------------------------------------------------------
        rag_stats = queries_df.select(
            F.avg("total_latency_ms").alias("avg_total_latency"),
            F.expr("percentile_approx(total_latency_ms, 0.50)").alias("p50_total_latency"),
            F.expr("percentile_approx(total_latency_ms, 0.95)").alias("p95_total_latency"),
            F.avg("generation_latency_ms").alias("avg_generation_latency"),
            F.avg("citation_count").alias("avg_citations"),
            F.sum(F.when(F.col("grounded") == True, 1).otherwise(0)).alias("grounded_count"),
            F.sum(F.when(F.col("citation_valid") == True, 1).otherwise(0)).alias("citation_valid_count"),
            F.sum(F.when(F.col("fallback_used") == True, 1).otherwise(0)).alias("fallback_count"),
        ).collect()[0]

        total_q = max(1, q_count)
        grounded_count = rag_stats["grounded_count"] or 0
        citation_valid_count = rag_stats["citation_valid_count"] or 0
        fallback_count = rag_stats["fallback_count"] or 0

        providers_df = queries_df.groupBy("provider").count().collect()
        provider_dict = {row["provider"]: row["count"] for row in providers_df}

        rag_metrics = {
            "generated_at_utc": now_iso,
            "queries_evaluated": q_count,
            "avg_total_latency_ms": round(rag_stats["avg_total_latency"] or 0.0, 2),
            "p50_total_latency_ms": round(rag_stats["p50_total_latency"] or 0.0, 2),
            "p95_total_latency_ms": round(rag_stats["p95_total_latency"] or 0.0, 2),
            "avg_generation_latency_ms": round(rag_stats["avg_generation_latency"] or 0.0, 2),
            "grounded_answer_rate": round((grounded_count / total_q) * 100.0, 2),
            "citation_validity_rate": round((citation_valid_count / total_q) * 100.0, 2),
            "fallback_answer_rate": round((fallback_count / total_q) * 100.0, 2),
            "avg_citation_count": round(rag_stats["avg_citations"] or 0.0, 2),
            "provider_distribution": provider_dict,
        }

        # ----------------------------------------------------------------------
        # E. Reliability & Error Analytics
        # ----------------------------------------------------------------------
        error_df = df.filter((F.col("error") == True) | (F.col("event_type") == "error"))
        error_count = error_df.count()

        error_types_df = error_df.groupBy("error_type").count().collect()
        error_types_dict = {row["error_type"]: row["count"] for row in error_types_df if row["error_type"]}

        error_metrics = {
            "generated_at_utc": now_iso,
            "total_records": total_records,
            "error_events_count": error_count,
            "overall_error_rate": round((error_count / max(1, total_records)) * 100.0, 2),
            "errors_by_type": error_types_dict,
            "fallback_events_count": fallback_count,
            "fallback_rate": round((fallback_count / total_q) * 100.0, 2),
        }

        # ----------------------------------------------------------------------
        # F. Time-Series Daily & Hourly Trends
        # ----------------------------------------------------------------------
        daily_trends_df = queries_df.groupBy("date").agg(
            F.count("*").alias("queries"),
            F.avg("total_latency_ms").alias("avg_latency"),
            F.sum(F.when(F.col("fallback_used") == True, 1).otherwise(0)).alias("fallbacks"),
            F.sum(F.when(F.col("grounded") == True, 1).otherwise(0)).alias("grounded"),
        ).orderBy("date").collect()

        daily_trends = [
            {
                "date": str(row["date"]),
                "queries": row["queries"],
                "avg_latency_ms": round(row["avg_latency"] or 0.0, 2),
                "fallback_rate": round(((row["fallbacks"] or 0) / max(1, row["queries"])) * 100.0, 2),
                "grounded_rate": round(((row["grounded"] or 0) / max(1, row["queries"])) * 100.0, 2),
            }
            for row in daily_trends_df
        ]

        timeseries_metrics = {
            "generated_at_utc": now_iso,
            "daily_trends": daily_trends,
            "hourly_distribution": hourly_dict,
        }

        # ----------------------------------------------------------------------
        # G. Executive Summary Metrics
        # ----------------------------------------------------------------------
        summary_metrics = {
            "generated_at_utc": now_iso,
            "source_record_count": total_records,
            "total_queries": q_count,
            "total_retrieval_events": retrieval_events_count,
            "grounded_answer_rate": rag_metrics["grounded_answer_rate"],
            "citation_validity_rate": rag_metrics["citation_validity_rate"],
            "fallback_rate": rag_metrics["fallback_answer_rate"],
            "error_rate": error_metrics["overall_error_rate"],
            "avg_retrieval_latency_ms": retrieval_metrics["avg_retrieval_latency_ms"],
            "p95_retrieval_latency_ms": retrieval_metrics["p95_retrieval_latency_ms"],
            "avg_total_latency_ms": rag_metrics["avg_total_latency_ms"],
            "p95_total_latency_ms": rag_metrics["p95_total_latency_ms"],
            "languages_active": len(language_metrics_dict),
            "code_mixed_query_share": language_metrics["code_mixed_percentage"],
        }

        # Save all JSON files
        outputs_map = {
            "summary_metrics.json": summary_metrics,
            "volume_metrics.json": volume_metrics,
            "language_metrics.json": language_metrics,
            "retrieval_metrics.json": retrieval_metrics,
            "rag_metrics.json": rag_metrics,
            "error_metrics.json": error_metrics,
            "timeseries_metrics.json": timeseries_metrics,
        }

        for filename, data in outputs_map.items():
            out_file = analytics_dir / filename
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        # ----------------------------------------------------------------------
        # H. Analytics Manifest
        # ----------------------------------------------------------------------
        manifest = {
            "schema_version": "1.0",
            "analytics_version": "1.0",
            "generated_at_utc": now_iso,
            "source_parquet_path": str(parquet_dir),
            "output_directory": str(analytics_dir),
            "input_records_processed": total_records,
            "generated_files": list(outputs_map.keys()),
            "privacy_audit_status": "COMPLIANT_ZERO_RAW_DATA",
        }
        with open(analytics_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return summary_metrics

    finally:
        spark.stop()


def main():
    parser = argparse.ArgumentParser(description="Run PySpark Batch Analytics Pipeline on Telemetry Parquet Data Lake")
    parser.add_argument("--input", default=str(settings.telemetry_parquet_path), help="Input Parquet data lake directory")
    parser.add_argument("--output", default=str(settings.telemetry_analytics_path), help="Output analytics JSON directory")
    args = parser.parse_args()

    print("=" * 80)
    print(" PYSPARK BATCH ANALYTICS PIPELINE (Phase 7)")
    print("=" * 80)
    print(f"Parquet Input Directory : {args.input}")
    print(f"Analytics Output Path   : {args.output}\n")

    summary = run_spark_analytics(
        parquet_dir=Path(args.input),
        analytics_dir=Path(args.output),
    )

    print("[Generated Executive Analytics Summary]")
    print(f"  - Total Records Processed  : {summary.get('source_record_count', 0)}")
    print(f"  - Total Queries Analyzed   : {summary.get('total_queries', 0)}")
    print(f"  - Grounded Answer Rate     : {summary.get('grounded_answer_rate', 0.0):.2f}%")
    print(f"  - Citation Validity Rate   : {summary.get('citation_validity_rate', 0.0):.2f}%")
    print(f"  - Fallback Rate            : {summary.get('fallback_rate', 0.0):.2f}%")
    print(f"  - Avg Retrieval Latency    : {summary.get('avg_retrieval_latency_ms', 0.0):.2f} ms")
    print(f"  - P95 Total Latency        : {summary.get('p95_total_latency_ms', 0.0):.2f} ms")
    print(f"  - Code-Mixed Query Share   : {summary.get('code_mixed_query_share', 0.0):.2f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()
