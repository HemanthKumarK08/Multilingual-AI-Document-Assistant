"""
Grounded RAG Benchmark Evaluation Script (Phase 5)
Evaluates end-to-end grounded answer generation, citation validity, fallback correctness, and latency.
"""

import argparse
import json
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.services.rag.coordinator import RAGCoordinator
from app.services.rag.llm_provider import MockLLMProvider, get_llm_provider


def run_rag_evaluation(
    eval_file: pathlib.Path = PROJECT_ROOT / "data" / "evaluation" / "eval_dataset.json",
    output_file: pathlib.Path = PROJECT_ROOT / "data" / "evaluation" / "rag_results.json",
    summary_report_file: pathlib.Path = PROJECT_ROOT / "data" / "evaluation" / "phase-5-evaluation-report.json",
    provider_name: Optional[str] = None,
):
    print("=" * 100)
    print(" MULTILINGUAL AI DOCUMENT ASSISTANT — GROUNDED RAG PIPELINE EVALUATION")
    print("=" * 100)

    if not eval_file.exists():
        print(f"Error: Evaluation file not found at {eval_file}")
        sys.exit(1)

    with open(eval_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # Use specified provider or detect if Gemini API key exists
    selected_provider_type = provider_name or settings.LLM_PROVIDER
    if selected_provider_type == "gemini" and not settings.GEMINI_API_KEY:
        print("[Notice] GEMINI_API_KEY not found in environment. Using MockLLMProvider for offline evaluation.")
        selected_provider_type = "mock"

    provider = get_llm_provider(selected_provider_type)

    print(f"Loaded {len(dataset)} evaluation questions from {eval_file.name}")
    print(f"LLM Provider Active: {selected_provider_type}\n")

    coordinator = RAGCoordinator(llm_provider=provider)

    total_queries = len(dataset)
    grounded_answers_count = 0
    valid_citations_count = 0
    correct_fallback_count = 0
    out_of_domain_count = 0
    latencies: List[float] = []
    results_log: List[Dict[str, Any]] = []

    for idx, item in enumerate(dataset, start=1):
        q_id = item.get("question_id", f"Q_{idx}")
        question = item.get("question", "")
        lang = item.get("language", "en")
        answer_available = item.get("answer_available", True)

        if not answer_available:
            out_of_domain_count += 1

        t0 = time.perf_counter()
        answer = coordinator.answer(
            query=question,
            language=lang if lang in ["en", "hi", "kn", "te"] else None,
        )
        latency = (time.perf_counter() - t0) * 1000.0
        latencies.append(latency)

        is_fallback = answer.fallback_used
        is_grounded = answer.grounded and not is_fallback

        # Check fallback correctness
        if not answer_available:
            if is_fallback:
                correct_fallback_count += 1
        else:
            if is_grounded:
                grounded_answers_count += 1

        # Check citation validity
        citations_valid = False
        if is_grounded:
            if answer.sources and all(s.chunk_id and s.page_number >= 1 for s in answer.sources):
                valid_citations_count += 1
                citations_valid = True
        elif is_fallback:
            # Fallback must not have citations
            if len(answer.sources) == 0:
                citations_valid = True

        results_log.append({
            "question_id": q_id,
            "question": question,
            "language": lang,
            "answer_available": answer_available,
            "latency_ms": round(latency, 2),
            "grounded": is_grounded,
            "fallback_used": is_fallback,
            "fallback_reason": answer.fallback_reason,
            "confidence_label": answer.confidence_label,
            "citations_count": len(answer.sources),
            "citations_valid": citations_valid,
            "answer_preview": answer.answer_text[:120] + "..." if len(answer.answer_text) > 120 else answer.answer_text,
        })

    in_domain_count = total_queries - out_of_domain_count
    grounded_rate = (grounded_answers_count / max(1, in_domain_count)) * 100.0
    fallback_correctness = (correct_fallback_count / max(1, out_of_domain_count)) * 100.0 if out_of_domain_count > 0 else 100.0
    citation_validity_rate = (valid_citations_count / max(1, total_queries)) * 100.0
    avg_latency = sum(latencies) / max(1, len(latencies))

    print(f"[RAG Evaluation Summary ({total_queries} Total Queries)]")
    print(f"  - In-Domain Questions      : {in_domain_count}")
    print(f"  - Grounded Answer Rate     : {grounded_rate:.2f}% ({grounded_answers_count}/{in_domain_count})")
    print(f"  - Out-of-Domain Questions  : {out_of_domain_count}")
    print(f"  - Fallback Correctness     : {fallback_correctness:.2f}% ({correct_fallback_count}/{out_of_domain_count})")
    print(f"  - Citation Validity Rate   : {citation_validity_rate:.2f}%")
    print(f"  - Average Response Latency : {avg_latency:.2f} ms")

    rag_summary = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_queries": total_queries,
        "in_domain_queries": in_domain_count,
        "out_of_domain_queries": out_of_domain_count,
        "grounded_answer_rate_pct": round(grounded_rate, 2),
        "fallback_correctness_pct": round(fallback_correctness, 2),
        "citation_validity_rate_pct": round(citation_validity_rate, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "results": results_log,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(rag_summary, f, indent=2, ensure_ascii=False)

    with open(summary_report_file, "w", encoding="utf-8") as f:
        json.dump({
            "phase": "Phase 5 — Hybrid Retrieval, Reranking, and Grounded RAG Pipeline",
            "status": "COMPLETED",
            "summary": rag_summary,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[Saved Detailed RAG Results] -> {output_file}")
    print(f"[Saved Evaluation Report]    -> {summary_report_file}")
    print("=" * 100)


if __name__ == "__main__":
    run_rag_evaluation()
