"""
Synthetic Privacy-Safe Telemetry Fixture Generator (Phase 7)
Generates realistic, validated telemetry logs in data/telemetry/raw/
reflecting Phase 5 and Phase 6 multilingual benchmark distributions.
"""

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import random
import sys
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.services.telemetry.models import UnifiedQueryTelemetryEvent


def generate_fixture_telemetry(
    output_raw_dir: Path,
    num_days: int = 7,
    records_per_day: int = 50,
) -> Path:
    """
    Generates realistic privacy-safe telemetry events across languages and timestamps.
    """
    output_raw_dir = Path(output_raw_dir)
    output_raw_dir.mkdir(parents=True, exist_ok=True)

    target_file = output_raw_dir / "query_completed.jsonl"
    
    languages = ["en", "hi", "kn", "te"]
    lang_weights = [0.40, 0.25, 0.20, 0.15]
    
    providers = ["gemini", "ollama", "mock"]
    provider_weights = [0.70, 0.20, 0.10]

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=num_days)

    total_records = 0
    with open(target_file, "w", encoding="utf-8") as f:
        for day_offset in range(num_days):
            current_date = start_date + timedelta(days=day_offset)
            date_str = current_date.strftime("%Y-%m-%d")

            for _ in range(records_per_day):
                hour = random.randint(8, 22)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                ts = f"{date_str}T{hour:02d}:{minute:02d}:{second:02d}Z"

                lang = random.choices(languages, weights=lang_weights)[0]
                is_code_mixed = random.random() < 0.15
                
                if lang == "en":
                    script = "latin"
                    q_type = "fact_lookup"
                elif is_code_mixed:
                    script = "latin"
                    q_type = "code_mixed_retrieval"
                elif lang == "hi":
                    script = "devanagari"
                    q_type = "cross_lingual_fact"
                elif lang == "kn":
                    script = "kannada"
                    q_type = "cross_lingual_fact"
                elif lang == "te":
                    script = "telugu"
                    q_type = "cross_lingual_fact"
                else:
                    script = "latin"
                    q_type = "fact_lookup"

                # Simulate fallbacks (~8% out-of-domain)
                is_fallback = random.random() < 0.08
                provider = random.choices(providers, weights=provider_weights)[0]

                # Latencies based on Phase 6 warm benchmarks
                ret_latency = round(random.uniform(18.0, 32.0), 2)
                rerank_latency = round(random.uniform(1.2, 3.5), 2)
                gen_latency = round(random.uniform(150.0, 450.0) if provider != "mock" else random.uniform(5.0, 15.0), 2)
                total_latency = round(ret_latency + rerank_latency + gen_latency + random.uniform(2.0, 6.0), 2)

                event = UnifiedQueryTelemetryEvent(
                    schema_version="1.0",
                    event_id=str(uuid4()),
                    event_type="query_completed",
                    timestamp=ts,
                    date=date_str,
                    hour=hour,
                    request_id_hash=str(uuid4())[:16],
                    query_id=f"Q-FIX-{total_records+1:04d}",
                    retrieval_id=f"RET-FIX-{total_records+1:04d}",
                    language=lang,
                    script=script,
                    query_type=q_type,
                    is_code_mixed=is_code_mixed,
                    variant_count=random.randint(1, 4) if lang != "en" else 1,
                    candidate_count=random.randint(15, 30),
                    retrieved_chunk_count=5 if not is_fallback else random.randint(0, 2),
                    best_retrieval_score=round(random.uniform(0.75, 0.98), 4) if not is_fallback else round(random.uniform(0.10, 0.32), 4),
                    retrieval_latency_ms=ret_latency,
                    reranking_latency_ms=rerank_latency,
                    generation_latency_ms=gen_latency,
                    total_latency_ms=total_latency,
                    provider=provider,
                    answer_mode="fallback" if is_fallback else "grounded",
                    fallback_used=is_fallback,
                    fallback_reason="INSUFFICIENT_EVIDENCE" if is_fallback else None,
                    citation_count=random.randint(1, 3) if not is_fallback else 0,
                    citation_valid=True if not is_fallback else False,
                    grounded=not is_fallback,
                    error=False,
                )

                f.write(event.model_dump_json() + "\n")
                total_records += 1

    print(f"[Generated Fixture] {total_records} validated events written to {target_file}")
    return target_file


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic privacy-safe telemetry events")
    parser.add_argument("--output", default=str(settings.telemetry_raw_path), help="Raw telemetry output directory")
    parser.add_argument("--days", type=int, default=7, help="Number of historical days")
    parser.add_argument("--records-per-day", type=int, default=50, help="Records per day")
    args = parser.parse_args()

    generate_fixture_telemetry(
        output_raw_dir=Path(args.output),
        num_days=args.days,
        records_per_day=args.records_per_day,
    )


if __name__ == "__main__":
    main()
