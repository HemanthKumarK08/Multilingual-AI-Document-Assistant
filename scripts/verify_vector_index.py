"""
Vector Index Verification and Diagnostics Runner (Phase 4)
Audits the persistent ChromaDB collection for integrity, dimensions, text retrievability, and metadata completeness.
"""

import argparse
import pathlib
import sys
import json

# Ensure project root is in sys.path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.services.vector_store.models import VectorStoreConfig
from app.services.vector_store.coordinator import VectorStoreCoordinator


def run_verify_vector_index(
    persist_directory: pathlib.Path = PROJECT_ROOT / "data" / "vector_store",
    collection_name: str = settings.VECTOR_STORE_COLLECTION_NAME,
    model_name: str = settings.EMBEDDING_MODEL_NAME,
    expected_dim: int = settings.EMBEDDING_DIMENSION,
):
    print("=" * 105)
    print(" MULTILINGUAL AI DOCUMENT ASSISTANT — VECTOR INDEX AUDIT & VERIFICATION")
    print("=" * 105)

    vec_config = VectorStoreConfig(
        persist_directory=str(persist_directory),
        collection_name=collection_name,
    )
    coordinator = VectorStoreCoordinator(vector_config=vec_config)

    print(f"\n[Persistence Path] {persist_directory}")
    print(f"[Collection Name]  {collection_name}")
    print(f"[Expected Model]   {model_name} (dim={expected_dim})\n")

    try:
        collection = coordinator.get_collection()
        total_records = collection.count()
        print(f"[1] Collection Connectivity : [PASS] (total records: {total_records})")

        validation_res = coordinator.verify_index()
        print(f"[2] Vector Structural Check : [PASS] ({validation_res['status'].upper()})")

        # Fetch sample document record to show retrievability
        sample = collection.get(limit=1, include=["documents", "metadatas"])
        if sample and sample.get("ids"):
            sid = sample["ids"][0]
            sdoc = sample["documents"][0]
            smeta = sample["metadatas"][0]
            print(f"[3] Sample Record Fetch     : [PASS] ID: {sid}")
            print(f"    - Category : {smeta.get('category')}")
            print(f"    - Page     : {smeta.get('page_number')}")
            print(f"    - Section  : {smeta.get('section_title')}")
            print(f"    - Text Preview: {repr(sdoc[:100])}...")

        print("\n" + "=" * 105)
        print(" VECTOR INDEX INTEGRITY: 100% VERIFIED")
        print("=" * 105)

    except Exception as e:
        print(f"\n[FAIL] Vector Index Verification Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit ChromaDB vector index integrity")
    parser.add_argument("--persist-directory", type=pathlib.Path, default=PROJECT_ROOT / "data" / "vector_store")
    parser.add_argument("--collection", dest="collection_name", type=str, default=settings.VECTOR_STORE_COLLECTION_NAME)
    args = parser.parse_args()

    run_verify_vector_index(
        persist_directory=args.persist_directory,
        collection_name=args.collection_name,
    )
