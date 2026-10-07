"""
PySpark Batch Analytics Pipeline (Phase 7 & Environment Separation)
Executes local PySpark aggregations over partitioned Parquet data lakes,
producing deterministic summary, language, retrieval, RAG, reliability, and time-series JSON metrics
for isolated environments: LIVE, TEST, FIXTURE, and ALL.
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


DOC_TITLES = {
    "DOC-ACAD-001": "Academic Regulations & Evaluation Guidelines v1.0",
    "DOC-EXAM-002": "Examination Conduct & Malpractice Rules",
    "DOC-FEE-003": "Fee Structure & Payment Policies",
    "DOC-SCH-004": "Scholarship & Financial Aid Schemes",
    "DOC-HOSTEL-005": "Hostel Rules & Campus Code of Conduct",
    "DOC-ATTN-001": "Attendance Policies & Academic Standards",
    "DOC-HOST-001": "Hostel Admission & Fee Schedule",
    "DOC-SCHOL-003": "Merit & Need-Based Scholarship Rules",
    "DOC-RES-002": "Research Guidelines & Ethics",
}

LANG_LABELS = {
    "en": "English",
    "hi": "हिन्दी (Hindi)",
    "kn": "ಕನ್ನಡ (Kannada)",
    "te": "తెలుగు (Telugu)",
}


def _write_empty_metrics(target_dir: Path, env_name: str, now_iso: str) -> Dict[str, Any]:
    """Writes empty baseline metrics when no records exist for the specified environment."""
    target_dir.mkdir(parents=True, exist_ok=True)
    
    empty_summary = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "source_record_count": 0,
        "total_events": 0,
        "total_queries": 0,
        "total_users": 0,
        "active_users": 0,
        "avg_queries_per_user": 0.0,
        "most_used_language": "en",
        "languages_active": 0,
        "total_retrieval_events": 0,
        "grounded_answer_rate": 0.0,
        "citation_validity_rate": 0.0,
        "fallback_rate": 0.0,
        "error_rate": 0.0,
        "avg_retrieval_latency_ms": 0.0,
        "p95_retrieval_latency_ms": 0.0,
        "avg_total_latency_ms": 0.0,
        "p95_total_latency_ms": 0.0,
        "code_mixed_query_share": 0.0,
        "data_available": False,
    }

    empty_volume = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "source_record_count": 0,
        "total_events": 0,
        "query_completed_count": 0,
        "retrieval_completed_count": 0,
        "rag_response_count": 0,
        "error_count": 0,
        "events_by_type": {},
        "events_by_date": {},
        "events_by_hour": {},
        "data_available": False,
    }

    empty_languages = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_queries_analyzed": 0,
        "language_distribution": {},
        "script_distribution": {},
        "code_mixed_queries_count": 0,
        "code_mixed_percentage": 0.0,
        "data_available": False,
    }

    empty_lang_perf = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_queries_analyzed": 0,
        "languages": [],
        "by_language": {},
        "data_available": False,
    }

    empty_users = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_unique_users": 0,
        "avg_queries_per_user": 0.0,
        "user_language_profiles": [],
        "top_anonymous_users": [],
        "daily_active_users": [],
        "data_available": False,
    }

    empty_switching = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_switches_detected": 0,
        "transitions": [],
        "transition_matrix": {},
        "data_available": False,
    }

    empty_code_mixed = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_queries_analyzed": 0,
        "code_mixed_count": 0,
        "total_code_mixed_queries": 0,
        "code_mixed_percentage": 0.0,
        "code_mixed_share_pct": 0.0,
        "romanized_count": 0,
        "romanized_percentage": 0.0,
        "script_type_comparison": [],
        "comparison": {},
        "data_available": False,
    }

    empty_documents = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_documents_referenced": 0,
        "total_documents_analyzed": 0,
        "documents": [],
        "data_available": False,
    }

    empty_retrieval = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "avg_retrieval_latency_ms": 0.0,
        "p50_retrieval_latency_ms": 0.0,
        "p95_retrieval_latency_ms": 0.0,
        "avg_candidate_count": 0.0,
        "avg_retrieved_chunk_count": 0.0,
        "avg_query_variant_count": 0.0,
        "avg_reranking_latency_ms": 0.0,
        "avg_best_retrieval_score": 0.0,
        "retrieval_by_language": {},
        "data_available": False,
    }

    empty_rag = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "queries_evaluated": 0,
        "avg_total_latency_ms": 0.0,
        "p50_total_latency_ms": 0.0,
        "p95_total_latency_ms": 0.0,
        "avg_generation_latency_ms": 0.0,
        "grounded_answer_rate": 0.0,
        "citation_validity_rate": 0.0,
        "fallback_answer_rate": 0.0,
        "avg_citation_count": 0.0,
        "provider_distribution": {},
        "data_available": False,
    }

    empty_error = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_records": 0,
        "error_events_count": 0,
        "overall_error_rate": 0.0,
        "errors_by_type": {},
        "fallback_events_count": 0,
        "fallback_rate": 0.0,
        "data_available": False,
    }

    empty_timeseries = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "daily_trends": [],
        "hourly_distribution": {},
        "data_available": False,
    }

    outputs = {
        "summary_metrics.json": empty_summary,
        "volume_metrics.json": empty_volume,
        "language_metrics.json": empty_languages,
        "language_performance_metrics.json": empty_lang_perf,
        "user_metrics.json": empty_users,
        "language_switching_metrics.json": empty_switching,
        "code_mixed_metrics.json": empty_code_mixed,
        "document_metrics.json": empty_documents,
        "retrieval_metrics.json": empty_retrieval,
        "rag_metrics.json": empty_rag,
        "error_metrics.json": empty_error,
        "timeseries_metrics.json": empty_timeseries,
    }

    for fn, data in outputs.items():
        with open(target_dir / fn, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    manifest = {
        "schema_version": "1.0",
        "analytics_version": "2.0",
        "environment": env_name,
        "generated_at_utc": now_iso,
        "input_records_processed": 0,
        "data_available": False,
        "generated_files": list(outputs.keys()),
    }
    with open(target_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return empty_summary


def _compute_metrics_for_dataset(
    df,
    env_name: str,
    target_dir: Path,
    now_iso: str,
    spark
) -> Dict[str, Any]:
    """Aggregates an environment-filtered PySpark DataFrame and serializes output JSONs."""
    import pyspark.sql.functions as F
    from pyspark.sql.window import Window

    target_dir.mkdir(parents=True, exist_ok=True)
    total_records = df.count()

    if total_records == 0:
        return _write_empty_metrics(target_dir, env_name, now_iso)

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
        "environment": env_name,
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
        "data_available": True,
    }

    # ----------------------------------------------------------------------
    # B. User Analytics (Anonymous User & Session Aggregations)
    # ----------------------------------------------------------------------
    queries_df = df.filter(F.col("event_type").isin("query_completed", "rag_response"))
    q_count = queries_df.count()
    total_q = max(1, q_count)

    # Filter out empty or unassigned user IDs for authentic user statistics
    identified_users_df = queries_df.filter(
        (F.col("anonymous_user_id").isNotNull()) & (F.col("anonymous_user_id") != "")
    )
    user_counts_df = identified_users_df.groupBy("anonymous_user_id").agg(
        F.count("*").alias("query_count"),
        F.collect_set("language").alias("languages_used"),
        F.collect_set("document_id").alias("documents_accessed"),
        F.sum(F.when(F.col("grounded") == True, 1).otherwise(0)).alias("grounded_count"),
        F.sum(F.when(F.col("fallback_used") == True, 1).otherwise(0)).alias("fallback_count"),
        F.avg("total_latency_ms").alias("avg_latency_ms")
    ).orderBy(F.col("query_count").desc()).collect()

    total_unique_users = len(user_counts_df)
    avg_queries_per_user = round(total_q / max(1, total_unique_users), 2) if total_unique_users > 0 else 0.0

    top_anonymous_users = []
    for row in user_counts_df[:25]:
        u_queries = row["query_count"]
        u_grounded = row["grounded_count"] or 0
        u_fallback = row["fallback_count"] or 0
        docs_clean = [d for d in (row["documents_accessed"] or []) if d and str(d).strip()]
        top_anonymous_users.append({
            "anonymous_user_id": row["anonymous_user_id"],
            "query_count": u_queries,
            "languages_used": sorted(list(row["languages_used"] or [])),
            "documents_accessed": len(docs_clean),
            "grounded_rate": round((u_grounded / max(1, u_queries)) * 100.0, 1),
            "fallback_rate": round((u_fallback / max(1, u_queries)) * 100.0, 1),
            "avg_latency_ms": round(row["avg_latency_ms"] or 0.0, 1),
        })

    # User language preference profiles
    user_lang_profiles_df = identified_users_df.groupBy("anonymous_user_id").agg(
        F.collect_set("language").alias("langs"),
        F.sum(F.when(F.col("is_code_mixed") == True, 1).otherwise(0)).alias("code_mixed_count"),
        F.count("*").alias("total_user_queries")
    ).collect()

    profile_counts: Dict[str, int] = {
        "English Only": 0,
        "English + Hindi": 0,
        "English + Kannada": 0,
        "English + Telugu": 0,
        "Multilingual (3+ Languages)": 0,
        "Code-Mixed & Romanized": 0,
    }

    for row in user_lang_profiles_df:
        u_langs = set(row["langs"] or [])
        cm_count = row["code_mixed_count"] or 0
        tot = row["total_user_queries"] or 1
        if cm_count / tot >= 0.4:
            profile_counts["Code-Mixed & Romanized"] += 1
        elif u_langs == {"en"}:
            profile_counts["English Only"] += 1
        elif u_langs == {"en", "hi"} or u_langs == {"hi"}:
            profile_counts["English + Hindi"] += 1
        elif u_langs == {"en", "kn"} or u_langs == {"kn"}:
            profile_counts["English + Kannada"] += 1
        elif u_langs == {"en", "te"} or u_langs == {"te"}:
            profile_counts["English + Telugu"] += 1
        else:
            profile_counts["Multilingual (3+ Languages)"] += 1

    user_language_profiles = [
        {"profile": k, "user_count": v, "percentage": round((v / max(1, total_unique_users)) * 100.0, 1) if total_unique_users > 0 else 0.0}
        for k, v in profile_counts.items()
    ]

    dau_df = queries_df.groupBy("date").agg(
        F.countDistinct("anonymous_user_id").alias("dau"),
        F.count("*").alias("queries")
    ).orderBy("date").collect()

    daily_active_users = [
        {"date": str(row["date"]), "active_users": row["dau"] or 1, "queries": row["queries"]}
        for row in dau_df
    ]

    user_metrics = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_unique_users": total_unique_users,
        "avg_queries_per_user": avg_queries_per_user,
        "user_language_profiles": user_language_profiles,
        "top_anonymous_users": top_anonymous_users,
        "daily_active_users": daily_active_users,
        "data_available": True,
    }

    # ----------------------------------------------------------------------
    # C. Multilingual & Language Performance Metrics
    # ----------------------------------------------------------------------
    lang_agg_df = queries_df.groupBy("language").agg(
        F.count("*").alias("total_queries"),
        F.avg("total_latency_ms").alias("avg_total_latency"),
        F.expr("percentile_approx(total_latency_ms, 0.95)").alias("p95_total_latency"),
        F.avg("retrieval_latency_ms").alias("avg_retrieval_latency"),
        F.avg("generation_latency_ms").alias("avg_generation_latency"),
        F.sum(F.when(F.col("grounded") == True, 1).otherwise(0)).alias("grounded_count"),
        F.sum(F.when(F.col("citation_valid") == True, 1).otherwise(0)).alias("citation_valid_count"),
        F.sum(F.when(F.col("fallback_used") == True, 1).otherwise(0)).alias("fallback_count"),
        F.sum(F.when(F.col("is_code_mixed") == True, 1).otherwise(0)).alias("code_mixed_count"),
        F.sum(F.when(F.col("is_romanized") == True, 1).otherwise(0)).alias("romanized_count"),
        F.avg("retrieved_chunk_count").alias("avg_retrieved_chunks"),
        F.avg("citation_count").alias("avg_citations"),
        F.collect_list("provider").alias("providers_list"),
    ).orderBy(F.col("total_queries").desc()).collect()

    language_performance_list = []
    language_performance_dict = {}
    lang_dist_dict = {}

    for row in lang_agg_df:
        l_code = row["language"]
        l_count = row["total_queries"]
        l_grounded = row["grounded_count"] or 0
        l_citation_valid = row["citation_valid_count"] or 0
        l_fallback = row["fallback_count"] or 0
        l_cm = row["code_mixed_count"] or 0
        l_rom = row["romanized_count"] or 0

        # Provider breakdown for this language
        prov_counter: Dict[str, int] = {}
        for p in (row["providers_list"] or []):
            prov_counter[p] = prov_counter.get(p, 0) + 1

        g_rate = round((l_grounded / max(1, l_count)) * 100.0, 1)
        stat = "Excellent" if g_rate >= 80.0 else ("Good" if g_rate >= 60.0 else "Needs Attention")

        lang_perf_item = {
            "language": l_code,
            "language_name": LANG_LABELS.get(l_code, l_code.upper()),
            "total_queries": l_count,
            "query_share_pct": round((l_count / total_q) * 100.0, 1),
            "grounded_rate": g_rate,
            "citation_validity_rate": round((l_citation_valid / max(1, l_count)) * 100.0, 1),
            "fallback_rate": round((l_fallback / max(1, l_count)) * 100.0, 1),
            "avg_latency_ms": round(row["avg_total_latency"] or 0.0, 1),
            "avg_total_latency_ms": round(row["avg_total_latency"] or 0.0, 1),
            "p95_latency_ms": round(row["p95_total_latency"] or 0.0, 1),
            "p95_total_latency_ms": round(row["p95_total_latency"] or 0.0, 1),
            "avg_retrieval_latency_ms": round(row["avg_retrieval_latency"] or 0.0, 2),
            "avg_generation_latency_ms": round(row["avg_generation_latency"] or 0.0, 1),
            "avg_retrieved_chunks": round(row["avg_retrieved_chunks"] or 0.0, 2),
            "avg_citations": round(row["avg_citations"] or 0.0, 2),
            "code_mixed_count": l_cm,
            "code_mixed_rate": round((l_cm / max(1, l_count)) * 100.0, 1),
            "romanized_count": l_rom,
            "status": stat,
            "provider_distribution": prov_counter,
        }

        language_performance_list.append(lang_perf_item)
        language_performance_dict[l_code] = lang_perf_item
        lang_dist_dict[l_code] = {
            "count": l_count,
            "percentage": round((l_count / total_q) * 100.0, 1),
            "avg_latency_ms": round(row["avg_total_latency"] or 0.0, 1),
            "fallback_count": l_fallback,
            "fallback_rate": round((l_fallback / max(1, l_count)) * 100.0, 1),
        }

    # Ensure all 4 supported languages are in language_performance_list
    for required_lang in ["en", "hi", "kn", "te"]:
        if required_lang not in language_performance_dict:
            missing_item = {
                "language": required_lang,
                "language_name": LANG_LABELS.get(required_lang, required_lang.upper()),
                "total_queries": 0,
                "query_share_pct": 0.0,
                "grounded_rate": 0.0,
                "citation_validity_rate": 0.0,
                "fallback_rate": 0.0,
                "avg_latency_ms": 0.0,
                "avg_total_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p95_total_latency_ms": 0.0,
                "avg_retrieval_latency_ms": 0.0,
                "avg_generation_latency_ms": 0.0,
                "avg_retrieved_chunks": 0.0,
                "avg_citations": 0.0,
                "code_mixed_count": 0,
                "code_mixed_rate": 0.0,
                "romanized_count": 0,
                "status": "Needs Attention",
                "provider_distribution": {},
            }
            language_performance_list.append(missing_item)
            language_performance_dict[required_lang] = missing_item
            lang_dist_dict[required_lang] = {
                "count": 0, "percentage": 0.0, "avg_latency_ms": 0.0, "fallback_count": 0, "fallback_rate": 0.0
            }

    script_df = queries_df.groupBy("script").count().collect()
    script_dict = {str(row["script"]): row["count"] for row in script_df}

    cm_total = queries_df.filter(F.col("is_code_mixed") == True).count()

    language_metrics = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_queries_analyzed": q_count,
        "language_distribution": lang_dist_dict,
        "script_distribution": script_dict,
        "code_mixed_queries_count": cm_total,
        "code_mixed_percentage": round((cm_total / total_q) * 100.0, 2),
        "data_available": True,
    }

    language_performance_metrics = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_queries_analyzed": q_count,
        "languages": language_performance_list,
        "by_language": language_performance_dict,
        "data_available": True,
    }

    # ----------------------------------------------------------------------
    # D. Language Switching Transitions
    # ----------------------------------------------------------------------
    # Method 1: Using explicit previous_language field
    switch_explicit_df = queries_df.filter(
        (F.col("previous_language").isNotNull()) & 
        (F.col("previous_language") != "") & 
        (F.col("previous_language") != F.col("language"))
    ).groupBy("previous_language", "language").count().collect()

    transitions_list = []
    transition_matrix: Dict[str, Dict[str, int]] = {}
    total_switches = 0

    if switch_explicit_df:
        for row in switch_explicit_df:
            p_lang = row["previous_language"]
            c_lang = row["language"]
            cnt = row["count"]
            total_switches += cnt

            if p_lang not in transition_matrix:
                transition_matrix[p_lang] = {}
            transition_matrix[p_lang][c_lang] = cnt

            transitions_list.append({
                "from_language": p_lang,
                "from_language_name": LANG_LABELS.get(p_lang, p_lang.upper()),
                "to_language": c_lang,
                "to_language_name": LANG_LABELS.get(c_lang, c_lang.upper()),
                "transition_count": cnt,
            })
    else:
        # Method 2: Derive transitions within same session using window function
        session_window = Window.partitionBy("session_id").orderBy("timestamp")
        lagged_df = queries_df.withColumn("lag_lang", F.lag("language", 1).over(session_window))
        session_switches_df = lagged_df.filter(
            (F.col("lag_lang").isNotNull()) & (F.col("lag_lang") != F.col("language"))
        ).groupBy("lag_lang", "language").count().collect()

        for row in session_switches_df:
            p_lang = row["lag_lang"]
            c_lang = row["language"]
            cnt = row["count"]
            total_switches += cnt

            if p_lang not in transition_matrix:
                transition_matrix[p_lang] = {}
            transition_matrix[p_lang][c_lang] = cnt

            transitions_list.append({
                "from_language": p_lang,
                "from_language_name": LANG_LABELS.get(p_lang, p_lang.upper()),
                "to_language": c_lang,
                "to_language_name": LANG_LABELS.get(c_lang, c_lang.upper()),
                "transition_count": cnt,
            })

    transitions_list.sort(key=lambda x: x["transition_count"], reverse=True)

    language_switching_metrics = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_switches_detected": total_switches,
        "transitions": transitions_list,
        "transition_matrix": transition_matrix,
        "data_available": True,
    }

    # ----------------------------------------------------------------------
    # E. Code-Mixed & Romanized Analytics
    # ----------------------------------------------------------------------
    cm_df = queries_df.filter(F.col("is_code_mixed") == True)
    rom_df = queries_df.filter(F.col("is_romanized") == True)
    native_df = queries_df.filter((F.col("is_code_mixed") == False) & (F.col("is_romanized") == False))

    def _stats_for_subset(sub_df, name):
        c = sub_df.count()
        if c == 0:
            return {
                "category": name, "script_type": name, "query_count": 0, "share_pct": 0.0,
                "grounded_rate": 0.0, "fallback_rate": 0.0, "avg_latency_ms": 0.0,
                "avg_retrieval_latency_ms": 0.0, "avg_retrieved_chunks": 0.0
            }
        g = sub_df.filter(F.col("grounded") == True).count()
        fb = sub_df.filter(F.col("fallback_used") == True).count()
        lat = sub_df.select(F.avg("total_latency_ms")).collect()[0][0] or 0.0
        ret_lat = sub_df.select(F.avg("retrieval_latency_ms")).collect()[0][0] or 0.0
        chunks = sub_df.select(F.avg("retrieved_chunk_count")).collect()[0][0] or 0.0
        return {
            "category": name,
            "script_type": name,
            "query_count": c,
            "share_pct": round((c / total_q) * 100.0, 1),
            "grounded_rate": round((g / c) * 100.0, 1),
            "fallback_rate": round((fb / c) * 100.0, 1),
            "avg_latency_ms": round(lat, 1),
            "avg_retrieval_latency_ms": round(ret_lat, 2),
            "avg_retrieved_chunks": round(chunks, 2),
        }

    native_stats = _stats_for_subset(native_df, "Native Script Standard")
    cm_stats = _stats_for_subset(cm_df, "Code-Mixed")
    rom_stats = _stats_for_subset(rom_df, "Romanized Indic")

    code_mixed_metrics = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_queries_analyzed": q_count,
        "code_mixed_count": cm_stats["query_count"],
        "total_code_mixed_queries": cm_stats["query_count"],
        "code_mixed_percentage": cm_stats["share_pct"],
        "code_mixed_share_pct": cm_stats["share_pct"],
        "romanized_count": rom_stats["query_count"],
        "romanized_percentage": rom_stats["share_pct"],
        "script_type_comparison": [native_stats, cm_stats, rom_stats],
        "comparison": {
            "native_script": native_stats,
            "code_mixed": cm_stats,
            "romanized": rom_stats,
        },
        "data_available": True,
    }

    # ----------------------------------------------------------------------
    # F. Document Analytics
    # ----------------------------------------------------------------------
    valid_docs_df = queries_df.filter((F.col("document_id").isNotNull()) & (F.col("document_id") != ""))
    doc_agg_df = valid_docs_df.groupBy("document_id").agg(
        F.count("*").alias("total_queries"),
        F.countDistinct("anonymous_user_id").alias("unique_users"),
        F.collect_set("language").alias("languages_used"),
        F.sum(F.when(F.col("grounded") == True, 1).otherwise(0)).alias("grounded_count"),
        F.sum(F.when(F.col("fallback_used") == True, 1).otherwise(0)).alias("fallback_count"),
        F.avg("total_latency_ms").alias("avg_latency"),
        F.avg("citation_count").alias("avg_citations")
    ).orderBy(F.col("total_queries").desc()).collect()

    doc_list = []
    for row in doc_agg_df:
        d_id = row["document_id"]
        d_q = row["total_queries"]
        d_g = row["grounded_count"] or 0
        d_fb = row["fallback_count"] or 0

        doc_list.append({
            "document_id": d_id,
            "title": DOC_TITLES.get(d_id, f"Institutional Document ({d_id})"),
            "total_queries": d_q,
            "query_count": d_q,
            "query_share_pct": round((d_q / total_q) * 100.0, 1),
            "unique_users": row["unique_users"] or 1,
            "languages_used": sorted(list(row["languages_used"] or [])),
            "grounded_rate": round((d_g / max(1, d_q)) * 100.0, 1),
            "fallback_rate": round((d_fb / max(1, d_q)) * 100.0, 1),
            "avg_latency_ms": round(row["avg_latency"] or 0.0, 1),
            "avg_citations": round(row["avg_citations"] or 0.0, 1),
        })

    document_metrics = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_documents_referenced": len(doc_list),
        "total_documents_analyzed": len(doc_list),
        "documents": doc_list,
        "data_available": True,
    }

    # ----------------------------------------------------------------------
    # G. Retrieval & Grounded RAG Analytics
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
        "environment": env_name,
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
        "data_available": True,
    }

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

    grounded_count = rag_stats["grounded_count"] or 0
    citation_valid_count = rag_stats["citation_valid_count"] or 0
    fallback_count = rag_stats["fallback_count"] or 0

    providers_df = queries_df.groupBy("provider").count().collect()
    provider_dict = {row["provider"]: row["count"] for row in providers_df}

    rag_metrics = {
        "environment": env_name,
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
        "data_available": True,
    }

    # ----------------------------------------------------------------------
    # H. Reliability & Error Analytics
    # ----------------------------------------------------------------------
    error_df = df.filter((F.col("error") == True) | (F.col("event_type") == "error"))
    error_count = error_df.count()

    error_types_df = error_df.groupBy("error_type").count().collect()
    error_types_dict = {row["error_type"]: row["count"] for row in error_types_df if row["error_type"]}

    error_metrics = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "total_records": total_records,
        "error_events_count": error_count,
        "overall_error_rate": round((error_count / max(1, total_records)) * 100.0, 2),
        "errors_by_type": error_types_dict,
        "fallback_events_count": fallback_count,
        "fallback_rate": round((fallback_count / total_q) * 100.0, 2),
        "data_available": True,
    }

    # ----------------------------------------------------------------------
    # I. Time-Series Daily & Hourly Trends
    # ----------------------------------------------------------------------
    daily_trends_df = queries_df.groupBy("date").agg(
        F.count("*").alias("queries"),
        F.countDistinct("anonymous_user_id").alias("active_users"),
        F.avg("total_latency_ms").alias("avg_latency"),
        F.sum(F.when(F.col("fallback_used") == True, 1).otherwise(0)).alias("fallbacks"),
        F.sum(F.when(F.col("grounded") == True, 1).otherwise(0)).alias("grounded"),
    ).orderBy("date").collect()

    daily_trends = [
        {
            "date": str(row["date"]),
            "queries": row["queries"],
            "active_users": row["active_users"] or 1,
            "avg_latency_ms": round(row["avg_latency"] or 0.0, 2),
            "fallback_rate": round(((row["fallbacks"] or 0) / max(1, row["queries"])) * 100.0, 2),
            "grounded_rate": round(((row["grounded"] or 0) / max(1, row["queries"])) * 100.0, 2),
            "grounded_count": row["grounded"] or 0,
            "fallback_count": row["fallbacks"] or 0,
        }
        for row in daily_trends_df
    ]

    timeseries_metrics = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "daily_trends": daily_trends,
        "hourly_distribution": hourly_dict,
        "data_available": True,
    }

    # ----------------------------------------------------------------------
    # J. Executive Summary Metrics
    # ----------------------------------------------------------------------
    most_used_lang = language_performance_list[0]["language"] if language_performance_list else "en"
    summary_metrics = {
        "environment": env_name,
        "generated_at_utc": now_iso,
        "source_record_count": total_records,
        "total_queries": q_count,
        "total_users": total_unique_users,
        "active_users": total_unique_users,
        "avg_queries_per_user": avg_queries_per_user,
        "most_used_language": most_used_lang,
        "languages_active": len(language_performance_list),
        "total_retrieval_events": retrieval_events_count,
        "grounded_answer_rate": rag_metrics["grounded_answer_rate"],
        "citation_validity_rate": rag_metrics["citation_validity_rate"],
        "fallback_rate": rag_metrics["fallback_answer_rate"],
        "error_rate": error_metrics["overall_error_rate"],
        "avg_retrieval_latency_ms": retrieval_metrics["avg_retrieval_latency_ms"],
        "p95_retrieval_latency_ms": retrieval_metrics["p95_retrieval_latency_ms"],
        "avg_total_latency_ms": rag_metrics["avg_total_latency_ms"],
        "p95_total_latency_ms": rag_metrics["p95_total_latency_ms"],
        "code_mixed_query_share": code_mixed_metrics["code_mixed_percentage"],
        "data_available": True,
    }

    outputs_map = {
        "summary_metrics.json": summary_metrics,
        "volume_metrics.json": volume_metrics,
        "language_metrics.json": language_metrics,
        "language_performance_metrics.json": language_performance_metrics,
        "user_metrics.json": user_metrics,
        "language_switching_metrics.json": language_switching_metrics,
        "code_mixed_metrics.json": code_mixed_metrics,
        "document_metrics.json": document_metrics,
        "retrieval_metrics.json": retrieval_metrics,
        "rag_metrics.json": rag_metrics,
        "error_metrics.json": error_metrics,
        "timeseries_metrics.json": timeseries_metrics,
    }

    for filename, data in outputs_map.items():
        out_file = target_dir / filename
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    manifest = {
        "schema_version": "1.0",
        "analytics_version": "2.0",
        "environment": env_name,
        "generated_at_utc": now_iso,
        "source_parquet_path": str(settings.telemetry_parquet_path),
        "output_directory": str(target_dir),
        "input_records_processed": total_records,
        "data_available": True,
        "generated_files": list(outputs_map.keys()),
        "privacy_audit_status": "COMPLIANT_ZERO_RAW_DATA",
    }
    with open(target_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return summary_metrics


def run_spark_analytics(
    parquet_dir: Path,
    analytics_dir: Path,
) -> Dict[str, Any]:
    """
    Executes PySpark analytical jobs across LIVE, TEST, FIXTURE, and ALL environments.
    """
    setup_spark_environment()
    parquet_dir = Path(parquet_dir)
    analytics_dir = Path(analytics_dir)
    analytics_dir.mkdir(parents=True, exist_ok=True)

    from pyspark.sql import SparkSession
    import pyspark.sql.functions as F

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
        parquet_files = list(parquet_dir.glob("**/*.parquet"))
        if not parquet_files:
            print(f"[Notice] No parquet files found in {parquet_dir}. Writing default baseline metrics.")
            for env_name in ("live", "test", "fixture", "all"):
                _write_empty_metrics(analytics_dir / env_name, env_name, now_iso)
            return _write_empty_metrics(analytics_dir, "all", now_iso)

        df = spark.read.parquet(str(parquet_dir))
        df.cache()

        # Compute for LIVE
        df_live = df.filter(F.col("telemetry_environment") == "live")
        live_summary = _compute_metrics_for_dataset(df_live, "live", analytics_dir / "live", now_iso, spark)

        # Compute for TEST
        df_test = df.filter(F.col("telemetry_environment") == "test")
        test_summary = _compute_metrics_for_dataset(df_test, "test", analytics_dir / "test", now_iso, spark)

        # Compute for FIXTURE
        df_fixture = df.filter(F.col("telemetry_environment") == "fixture")
        fixture_summary = _compute_metrics_for_dataset(df_fixture, "fixture", analytics_dir / "fixture", now_iso, spark)

        # Compute for ALL
        all_summary = _compute_metrics_for_dataset(df, "all", analytics_dir / "all", now_iso, spark)

        # Also write root analytics_dir corresponding to ALL / default
        _compute_metrics_for_dataset(df, "all", analytics_dir, now_iso, spark)

        all_summary["environments"] = {
            "all": all_summary,
            "live": live_summary,
            "test": test_summary,
            "fixture": fixture_summary,
        }

        return all_summary

    finally:
        spark.stop()


def main():
    parser = argparse.ArgumentParser(description="Run PySpark Batch Analytics Pipeline on Telemetry Parquet Data Lake")
    parser.add_argument("--input", default=str(settings.telemetry_parquet_path), help="Input Parquet data lake directory")
    parser.add_argument("--output", default=str(settings.telemetry_analytics_path), help="Output analytics JSON directory")
    args = parser.parse_args()

    print("=" * 80)
    print(" PYSPARK BATCH ANALYTICS PIPELINE (Phase 7 - Multi-Environment)")
    print("=" * 80)
    print(f"Parquet Input Directory : {args.input}")
    print(f"Analytics Output Path   : {args.output}\n")

    summary_result = run_spark_analytics(
        parquet_dir=Path(args.input),
        analytics_dir=Path(args.output),
    )

    envs = summary_result.get("environments", {})
    all_sum = envs.get("all", summary_result)
    live_sum = envs.get("live", {})
    test_sum = envs.get("test", {})
    fix_sum = envs.get("fixture", {})

    print("[Multi-Environment Analytics Summary]")
    print(f"  - LIVE Dataset Records     : {live_sum.get('source_record_count', 0)} (Queries: {live_sum.get('total_queries', 0)}, Users: {live_sum.get('total_users', 0)})")
    print(f"  - TEST Dataset Records     : {test_sum.get('source_record_count', 0)} (Queries: {test_sum.get('total_queries', 0)})")
    print(f"  - FIXTURE Dataset Records  : {fix_sum.get('source_record_count', 0)} (Queries: {fix_sum.get('total_queries', 0)})")
    print(f"  - ALL Dataset Records      : {all_sum.get('source_record_count', 0)} (Total Queries: {all_sum.get('total_queries', 0)})")
    print("=" * 80)


if __name__ == "__main__":
    main()
