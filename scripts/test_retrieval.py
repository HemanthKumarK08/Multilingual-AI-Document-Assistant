"""
Interactive and Diagnostic Retrieval Testing Script (Phase 5)
Executes end-to-end retrieval for any query and displays candidate provenance and scores.
"""

import argparse
import json
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.retrieval.coordinator import RetrievalCoordinator
from app.services.retrieval.models import RetrievalFilter


def main():
    parser = argparse.ArgumentParser(description="Test Multilingual Hybrid Retrieval")
    parser.add_argument("query", type=str, help="Query string to search for")
    parser.add_argument("--language", type=str, default=None, help="Explicit language override (en, hi, kn, te)")
    parser.add_argument("--top_k", type=int, default=5, help="Number of final results to display")
    parser.add_argument("--doc_id", type=str, default=None, help="Optional doc_id filter")
    parser.add_argument("--category", type=str, default=None, help="Optional category filter")

    args = parser.parse_args()

    print("=" * 100)
    print(" MULTILINGUAL AI DOCUMENT ASSISTANT — RETRIEVAL DIAGNOSTIC RUNNER")
    print("=" * 100)
    print(f"Query: '{args.query}'")
    if args.language:
        print(f"Explicit Language: {args.language}")
    
    filters = None
    if args.doc_id or args.category:
        filters = RetrievalFilter(doc_id=args.doc_id, category=args.category)
        print(f"Filters: {filters.model_dump(exclude_none=True)}")
    print("-" * 100)

    coordinator = RetrievalCoordinator()
    result = coordinator.retrieve(
        raw_query=args.query,
        language=args.language,
        filters=filters,
        final_top_k=args.top_k,
    )

    print(f"\n[Query Analysis]")
    print(f"  - Detected Script   : {result.query.script}")
    print(f"  - Detected Language : {result.query.language} ({result.query.language_source})")
    print(f"  - Code-Mixed        : {result.query.is_code_mixed}")
    print(f"  - Romanized         : {result.query.is_romanized}")
    print(f"  - Total Candidates  : {result.total_candidates_found}")
    print(f"  - Latency           : {result.latency_ms:.2f} ms")

    print(f"\n[Top {len(result.candidates)} Retrieved Candidates]")
    for cand in result.candidates:
        print(f"\n Rank {cand.rank} | Chunk: {cand.chunk_id} | Doc: {cand.doc_id} (Page {cand.page_number})")
        print(f" Section : {cand.section_title or 'General'} (File: {cand.filename})")
        print(f" Methods : {', '.join(cand.retrieval_methods)}")
        print(f" Scores  : Dense={cand.dense_score} | Lexical={cand.lexical_score} | Hybrid={cand.hybrid_score} | Rerank={cand.rerank_score}")
        print(f" Text    : {repr(cand.text_content[:140])}...")

    if result.warnings:
        print(f"\n[Warnings]: {result.warnings}")

    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
