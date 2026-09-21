"""
Corpus Embedding Generation Runner (Phase 4)
Generates dense multilingual embeddings for all Phase 3 chunk artifacts.
"""

import argparse
import pathlib
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.services.embeddings.coordinator import EmbeddingCoordinator
from app.services.embeddings.models import EmbeddingConfig


def run_embed_corpus(
    input_dir: pathlib.Path = PROJECT_ROOT / "data" / "processed",
    output_dir: pathlib.Path = PROJECT_ROOT / "data" / "embeddings",
    model_name: str = settings.EMBEDDING_MODEL_NAME,
    device: str = settings.EMBEDDING_DEVICE,
    batch_size: int = settings.EMBEDDING_BATCH_SIZE,
    max_length: int = settings.EMBEDDING_MAX_LENGTH,
    normalize: bool = settings.EMBEDDING_NORMALIZE,
    dry_run: bool = False,
    verbose: bool = False,
):
    print("=" * 105)
    print(" MULTILINGUAL AI DOCUMENT ASSISTANT — CORPUS EMBEDDING PIPELINE (PHASE 4)")
    print("=" * 105)

    config = EmbeddingConfig(
        model_name=model_name,
        dimension=settings.EMBEDDING_DIMENSION,
        device=device,
        batch_size=batch_size,
        max_length=max_length,
        normalize=normalize,
    )
    coordinator = EmbeddingCoordinator(config=config)

    print(f"\n[Model] {config.model_name} (dim={config.dimension}) on [{config.device}]")
    print(f"[Batch Size] {config.batch_size} | [Normalize] {config.normalize} | [Max Length] {config.max_length}")
    print(f"[Input Directory]  {input_dir}")
    print(f"[Output Directory] {output_dir}")
    print(f"[Mode] Dry Run: {dry_run} | Verbose: {verbose}\n")

    report = coordinator.embed_corpus(
        input_dir=input_dir,
        output_dir=output_dir,
        save_artifacts=not dry_run,
    )

    print(f"{'DOC ID':<15} | {'CHUNKS':<8} | {'TIME(ms)':<10} | {'STATUS'}")
    print("-" * 50)
    for doc in report.document_summaries:
        print(f"{doc['doc_id']:<15} | {doc['chunk_count']:<8} | {doc['duration_ms']:<10.2f} | [PASS] {doc['status']}")

    print("\n" + "=" * 105)
    print(" EMBEDDING SUMMARY")
    print("=" * 105)
    print(f"Total Discovered Documents : {report.documents_discovered}")
    print(f"Successfully Embedded      : {report.documents_succeeded}")
    print(f"Failed Documents           : {report.documents_failed}")
    print(f"Total Chunks Embedded      : {report.chunks_embedded}")
    print(f"Total Elapsed Time         : {report.total_elapsed_seconds:.3f}s")
    print(f"Report File Written To     : {output_dir / 'embedding_report.json'}")
    print("=" * 105)

    if report.documents_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate embeddings for Phase 3 chunk artifacts")
    parser.add_argument("--input-dir", type=pathlib.Path, default=PROJECT_ROOT / "data" / "processed")
    parser.add_argument("--output-dir", type=pathlib.Path, default=PROJECT_ROOT / "data" / "embeddings")
    parser.add_argument("--model-name", type=str, default=settings.EMBEDDING_MODEL_NAME)
    parser.add_argument("--device", type=str, default=settings.EMBEDDING_DEVICE)
    parser.add_argument("--batch-size", type=int, default=settings.EMBEDDING_BATCH_SIZE)
    parser.add_argument("--max-length", type=int, default=settings.EMBEDDING_MAX_LENGTH)
    parser.add_argument("--normalize", action="store_true", default=settings.EMBEDDING_NORMALIZE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    run_embed_corpus(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        model_name=args.model_name,
        device=args.device,
        batch_size=args.batch_size,
        max_length=args.max_length,
        normalize=args.normalize,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
