#!/usr/bin/env python3
"""
ChromaDB vs SQLite Vector Store Integrity Checker
Audits consistency between SQLite 'documents' table and ChromaDB vector collection.
Reports:
1. SQLite active documents and chunk counts
2. ChromaDB unique document IDs and vector counts
3. Orphan vectors (in ChromaDB but not in SQLite)
4. Missing vectors (in SQLite but not in ChromaDB)
5. Optional cleanup mode (--clean-orphans) to safely delete confirmed orphan vectors.
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import sqlite3
from app.core.config import settings
from app.services.vector_store.coordinator import VectorStoreCoordinator


def run_integrity_check(clean_orphans: bool = False):
    print("=" * 75)
    print("CHROMADB & SQLITE VECTOR STORE INTEGRITY AUDIT")
    print("=" * 75)

    # 1. Inspect SQLite Database
    db_path = settings.DATA_DIRECTORY / "app.db"
    if not db_path.exists():
        print(f"Error: SQLite database not found at {db_path}")
        return 1

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT doc_id, filename, status, chunk_count FROM documents WHERE is_active = 1")
    sqlite_rows = cursor.fetchall()
    conn.close()

    sqlite_doc_ids = {r[0] for r in sqlite_rows}
    print(f"SQLite Active Documents: {len(sqlite_doc_ids)}")

    # 2. Inspect ChromaDB Collection
    vsc = VectorStoreCoordinator()
    col = vsc.get_collection()
    data = col.get(include=["metadatas"])
    chroma_ids = data.get("ids") or []
    chroma_metas = data.get("metadatas") or []

    print(f"ChromaDB Total Vectors: {len(chroma_ids)}")

    # Map ChromaDB vectors by doc_id
    chroma_doc_chunks = {}
    for cid, meta in zip(chroma_ids, chroma_metas):
        # doc_id is in metadata or prefix of chunk_id before ':p'
        doc_id = meta.get("doc_id") if meta else None
        if not doc_id and ":" in cid:
            doc_id = cid.split(":")[0]
        if doc_id:
            chroma_doc_chunks.setdefault(doc_id, []).append(cid)

    chroma_doc_ids = set(chroma_doc_chunks.keys())
    print(f"ChromaDB Unique Document IDs: {len(chroma_doc_ids)}")

    # 3. Find Orphan Vectors (in ChromaDB but not in SQLite)
    orphan_doc_ids = chroma_doc_ids - sqlite_doc_ids
    orphan_vector_ids = []
    for odoc in orphan_doc_ids:
        orphan_vector_ids.extend(chroma_doc_chunks[odoc])

    # 4. Find Missing Vectors (in SQLite but not in ChromaDB)
    missing_doc_ids = sqlite_doc_ids - chroma_doc_ids

    print("-" * 75)
    print(f"Orphan Documents in ChromaDB: {len(orphan_doc_ids)}")
    for odoc in sorted(orphan_doc_ids):
        chunks = chroma_doc_chunks[odoc]
        print(f"  • {odoc} ({len(chunks)} chunks): {chunks[:5]}")

    print(f"Orphan Vectors Total: {len(orphan_vector_ids)}")

    print(f"Missing Documents in ChromaDB: {len(missing_doc_ids)}")
    for mdoc in sorted(missing_doc_ids):
        print(f"  • {mdoc}")

    # 5. Optional Cleanup of Confirmed Orphan Vectors
    if clean_orphans and orphan_vector_ids:
        print("-" * 75)
        print(f"CLEANING {len(orphan_vector_ids)} ORPHAN VECTORS...")
        col.delete(ids=orphan_vector_ids)
        # Verify
        remaining = col.get(ids=orphan_vector_ids).get("ids") or []
        if len(remaining) == 0:
            print(f"✓ Successfully deleted {len(orphan_vector_ids)} orphan vectors from ChromaDB.")
            from app.services.retrieval.coordinator import clear_bm25_cache
            clear_bm25_cache()
            print("✓ Active BM25 cache cleared.")
        else:
            print(f"Warning: {len(remaining)} vectors could not be deleted.")

    print("=" * 75)
    return len(orphan_vector_ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check vector store integrity")
    parser.add_argument("--clean-orphans", action="store_true", help="Remove confirmed orphan vectors")
    args = parser.parse_args()
    sys.exit(run_integrity_check(clean_orphans=args.clean_orphans))
