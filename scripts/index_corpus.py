"""
Corpus Vector Indexing Runner (Phase 4)
Embeds Phase 3 chunk artifacts and upserts them into persistent ChromaDB storage.
"""

import argparse
import pathlib
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.services.embeddings.models import EmbeddingConfig
from app.services.embeddings.coordinator import EmbeddingCoordinator
from app.services.vector_store.models import VectorStoreConfig
from app.services.vector_store.coordinator import VectorStoreCoordinator


def run_index_corpus(
    input_dir: pathlib.Path = PROJECT_ROOT / "data" / "processed",
    persist_directory: pathlib.Path = PROJECT_ROOT / "data" / "vector_store",
    collection_name: str = settings.VECTOR_STORE_COLLECTION_NAME,
    model_name: str = settings.EMBEDDING_MODEL_NAME,
    device: str = settings.EMBEDDING_DEVICE,
    batch_size: int = settings.EMBEDDING_BATCH_SIZE,
    normalize: bool = settings.EMBEDDING_NORMALIZE,
    remove_stale: bool = False,
    rebuild: bool = False,
    verbose: bool = False,
):
    print("=" * 115)
    print(" MULTILINGUAL AI DOCUMENT ASSISTANT — CHROMADB VECTOR INDEXING (PHASE 4)")
    print("=" * 115)

    emb_config = EmbeddingConfig(
        model_name=model_name,
        dimension=settings.EMBEDDING_DIMENSION,
        device=device,
        batch_size=batch_size,
        normalize=normalize,
    )
    emb_coordinator = EmbeddingCoordinator(config=emb_config)

    vec_config = VectorStoreConfig(
        persist_directory=str(persist_directory),
        collection_name=collection_name,
        distance_metric=settings.VECTOR_STORE_DISTANCE_METRIC,
        index_version=settings.VECTOR_INDEX_VERSION,
    )
    vec_coordinator = VectorStoreCoordinator(
        vector_config=vec_config,
        embedding_coordinator=emb_coordinator,
    )

    print(f"\n[Embedding Model]  {emb_config.model_name} (dim={emb_config.dimension}) on [{emb_config.device}]")
    print(f"[Vector Store]     ChromaDB at {persist_directory}")
    print(f"[Collection]       {vec_config.collection_name} (metric={vec_config.distance_metric})")
    print(f"[Input Directory]  {input_dir}")
    print(f"[Options]          Rebuild: {rebuild} | Remove Stale: {remove_stale} | Verbose: {verbose}\n")

    report = vec_coordinator.index_corpus(
        input_dir=input_dir,
        rebuild=rebuild,
        remove_stale=remove_stale,
    )

    print("\n" + "=" * 115)
    print(" INDEXING SUMMARY")
    print("=" * 115)
    print(f"Total Discovered Documents : {report.documents_discovered}")
    print(f"Successfully Indexed Docs  : {report.documents_succeeded}")
    print(f"Failed Documents           : {report.documents_failed}")
    print(f"Total Chunks Discovered    : {report.chunks_discovered}")
    print(f"Total Chunks Embedded      : {report.chunks_embedded}")
    print(f"New Records Added          : {report.chunks_indexed}")
    print(f"Existing Records Updated   : {report.chunks_updated}")
    print(f"Identical Records Skipped  : {report.chunks_skipped}")
    print(f"Stale Records Detected     : {report.stale_records_detected}")
    print(f"Stale Records Removed      : {report.stale_records_removed}")
    print(f"Total Elapsed Time         : {report.total_elapsed_seconds:.3f}s")
    print(f"Index Validation Status    : [{report.validation_status.upper()}]")
    print(f"Report File Written To     : {persist_directory / 'index_report.json'}")
    print("=" * 115)

    if report.documents_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed and index Phase 3 chunks into ChromaDB")
    parser.add_argument("--input-dir", type=pathlib.Path, default=PROJECT_ROOT / "data" / "processed")
    parser.add_argument("--persist-directory", type=pathlib.Path, default=PROJECT_ROOT / "data" / "vector_store")
    parser.add_argument("--collection", dest="collection_name", type=str, default=settings.VECTOR_STORE_COLLECTION_NAME)
    parser.add_argument("--model-name", type=str, default=settings.EMBEDDING_MODEL_NAME)
    parser.add_argument("--device", type=str, default=settings.EMBEDDING_DEVICE)
    parser.add_argument("--batch-size", type=int, default=settings.EMBEDDING_BATCH_SIZE)
    parser.add_argument("--normalize", action="store_true", default=settings.EMBEDDING_NORMALIZE)
    parser.add_argument("--remove-stale", action="store_true", default=False)
    parser.add_argument("--rebuild", action="store_true", default=False)
    parser.add_argument("--verbose", action="store_true", default=False)
    args = parser.parse_args()

    run_index_corpus(
        input_dir=args.input_dir,
        persist_directory=args.persist_directory,
        collection_name=args.collection_name,
        model_name=args.model_name,
        device=args.device,
        batch_size=args.batch_size,
        normalize=args.normalize,
        remove_stale=args.remove_stale,
        rebuild=args.rebuild,
        verbose=args.verbose,
    )
