"""
Corpus Chunking & Provenance Verification Runner (Phase 3)
Chunks all canonical Phase 2 parsed JSON artifacts in data/processed/,
generates deterministic chunked JSON artifacts, validates source coverage and provenance,
and outputs data/processed/corpus_chunking_report.json.
"""

import argparse
import json
import pathlib
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.chunking.constants import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MINIMUM_CHUNK_SIZE,
)
from app.services.chunking.coordinator import ChunkingCoordinator
from app.services.chunking.models import ChunkingConfig


def run_corpus_chunking(
    input_dir: pathlib.Path = PROJECT_ROOT / "data" / "processed",
    output_dir: pathlib.Path = PROJECT_ROOT / "data" / "processed",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    minimum_chunk_size: int = DEFAULT_MINIMUM_CHUNK_SIZE,
    dry_run: bool = False,
    fail_fast: bool = False,
    verbose: bool = False,
):
    print("=" * 115)
    print(" MULTILINGUAL AI DOCUMENT ASSISTANT — CORPUS CHUNKING PIPELINE (PHASE 3)")
    print("=" * 115)

    config = ChunkingConfig(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        minimum_chunk_size=minimum_chunk_size,
    )
    coordinator = ChunkingCoordinator(config=config, output_dir=output_dir)

    print(f"\n[Configuration] Chunk Size: {config.chunk_size} chars | Overlap: {config.chunk_overlap} chars | Min Size: {config.minimum_chunk_size} char")
    print(f"[Input Directory]  {input_dir}")
    print(f"[Output Directory] {output_dir}")
    print(f"[Mode] Dry Run: {dry_run} | Fail Fast: {fail_fast} | Verbose: {verbose}\n")

    print(
        f"{'DOC ID':<15} | {'CATEGORY':<20} | {'LANG':<4} | {'SCRIPT':<10} | {'PAGES':<5} | {'SRC CHARS':<9} | {'CHUNKS':<6} | {'AVG LEN':<7} | {'MIN/MAX':<9} | {'TIME(ms)':<8} | {'STATUS'}"
    )
    print("-" * 125)

    if dry_run:
        # In dry-run mode, process without writing artifacts to disk
        parsed_files = sorted(input_dir.glob("*_parsed.json"))
        total_chunks = 0
        for p_file in parsed_files:
            art = coordinator.chunk_parsed_file(p_file, save_artifact=False)
            total_chunks += len(art.chunks)
            print(f"{art.source_document['doc_id']:<15} | [DRY-RUN PASS] {len(art.chunks)} chunks")
        print(f"\n[DRY RUN COMPLETE] Total documents: {len(parsed_files)} | Total potential chunks: {total_chunks}")
        return

    report = coordinator.chunk_corpus(input_dir=input_dir)

    for doc in report.documents:
        if doc.status == "success":
            min_max_str = f"{doc.min_chunk_length}/{doc.max_chunk_length}"
            print(
                f"{doc.doc_id:<15} | "
                f"{doc.category:<20} | "
                f"{doc.language:<4} | "
                f"{doc.script:<10} | "
                f"{doc.page_count:<5} | "
                f"{doc.source_character_count:<9} | "
                f"{doc.chunk_count:<6} | "
                f"{doc.avg_chunk_length:<7.1f} | "
                f"{min_max_str:<9} | "
                f"{doc.duration_ms:<8.2f} | "
                f"[PASS]"
            )
        else:
            print(
                f"{doc.doc_id:<15} | "
                f"{doc.category:<20} | "
                f"{doc.language:<4} | "
                f"{doc.script:<10} | "
                f"{'-':<5} | "
                f"{'-':<9} | "
                f"{'-':<6} | "
                f"{'-':<7} | "
                f"{'-':<9} | "
                f"{doc.duration_ms:<8.2f} | "
                f"[FAIL] {doc.error_message}"
            )
            if fail_fast:
                print("\n[FAIL-FAST] Terminating immediately upon document failure.")
                sys.exit(1)

    print("\n" + "=" * 115)
    print(" CORPUS CHUNKING SUMMARY")
    print("=" * 115)
    print(f"Total Discovered Documents : {report.total_discovered_documents}")
    print(f"Successfully Chunked       : {report.total_successful}")
    print(f"Failed Documents           : {report.total_failed}")
    print(f"Total Chunks Generated     : {report.total_chunks_generated}")
    print(f"Total Source Characters    : {report.total_source_characters}")
    print(f"Total Chunk Characters     : {report.total_chunk_characters}")
    print(f"Overall Average Chunk Len  : {report.overall_avg_chunk_length:.2f} chars")
    print(f"Total Processing Time      : {report.total_duration_seconds:.3f}s")
    print(f"Report File Written To     : {output_dir / 'corpus_chunking_report.json'}")
    print("=" * 115)

    if report.total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chunk parsed document artifacts in data/processed/")
    parser.add_argument("--input-dir", type=pathlib.Path, default=PROJECT_ROOT / "data" / "processed", help="Input directory containing *_parsed.json artifacts")
    parser.add_argument("--output-dir", type=pathlib.Path, default=PROJECT_ROOT / "data" / "processed", help="Output directory for *_chunks.json and report")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help="Target chunk size in characters (500-700)")
    parser.add_argument("--chunk-overlap", "--overlap", dest="chunk_overlap", type=int, default=DEFAULT_CHUNK_OVERLAP, help="Overlap size in characters")
    parser.add_argument("--min-chunk-size", type=int, default=DEFAULT_MINIMUM_CHUNK_SIZE, help="Minimum chunk size in characters")
    parser.add_argument("--dry-run", action="store_true", help="Perform chunking in memory without saving artifacts")
    parser.add_argument("--fail-fast", action="store_true", help="Halt execution on the first document error")
    parser.add_argument("--verbose", action="store_true", help="Print verbose execution details")
    args = parser.parse_args()

    run_corpus_chunking(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        minimum_chunk_size=args.min_chunk_size,
        dry_run=args.dry_run,
        fail_fast=args.fail_fast,
        verbose=args.verbose,
    )
