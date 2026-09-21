"""
Corpus Ingestion & Verification Runner
Parses all 24 raw documents in data/raw/, generates processed intermediate JSONs,
and verifies database records and metadata integrity.
"""

import sys
import json
import time
import asyncio
import pathlib

# Ensure project root is in sys.path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import AsyncSessionLocal, init_db, close_db
from app.services.ingestion.coordinator import default_ingestion_coordinator
from app.services.ingestion.exceptions import IngestionError

async def run_corpus_ingestion():
    print("=" * 80)
    print(" MULTILINGUAL AI DOCUMENT ASSISTANT — CORPUS INGESTION PIPELINE")
    print("=" * 80)

    manifest_path = PROJECT_ROOT / "data" / "raw" / "corpus_manifest.json"
    if not manifest_path.exists():
        print(f"[FAIL] Manifest file not found: {manifest_path}")
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Initialize database tables
    await init_db()

    results = []
    total_start = time.time()
    successful = 0
    failed = 0

    print(f"\n[1] Ingesting {len(manifest_data)} documents through IngestionCoordinator...\n")
    print(f"{'DOC ID':<15} | {'CATEGORY':<22} | {'PAGES':<5} | {'CHARS':<7} | {'LANG':<4} | {'SCRIPT':<10} | {'TIME (ms)':<9} | {'STATUS'}")
    print("-" * 95)

    async with AsyncSessionLocal() as db:
        for doc_meta in manifest_data:
            doc_id = doc_meta["document_id"]
            rel_path = doc_meta["file_path"]
            file_path = PROJECT_ROOT / rel_path
            category = doc_meta["category"]
            title = doc_meta["title"]
            version = doc_meta.get("version", "1.0")

            try:
                ingest_res = await default_ingestion_coordinator.ingest_document(
                    db=db,
                    file_path=file_path,
                    doc_id=doc_id,
                    display_title=title,
                    category=category,
                    version=version,
                    allow_reingest=True,
                    metadata={"source_type": doc_meta.get("source_type", "synthetic")}
                )
                successful += 1
                results.append(ingest_res.model_dump())
                print(
                    f"{ingest_res.doc_id:<15} | "
                    f"{ingest_res.category:<22} | "
                    f"{ingest_res.page_count:<5} | "
                    f"{ingest_res.character_count:<7} | "
                    f"{ingest_res.language:<4} | "
                    f"{ingest_res.detected_script:<10} | "
                    f"{ingest_res.duration_ms:<9.2f} | "
                    f"[PASS] {ingest_res.status}"
                )
            except IngestionError as e:
                failed += 1
                print(f"{doc_id:<15} | {category:<22} | {'-':<5} | {'-':<7} | {'-':<4} | {'-':<10} | {'-':<9} | [FAIL] {e.message}")
            except Exception as e:
                failed += 1
                print(f"{doc_id:<15} | {category:<22} | {'-':<5} | {'-':<7} | {'-':<4} | {'-':<10} | {'-':<9} | [ERROR] {str(e)}")

    total_duration = round(time.time() - total_start, 3)

    # Verify processed JSON artifacts exist
    processed_dir = PROJECT_ROOT / "data" / "processed"
    artifact_count = len(list(processed_dir.glob("*_parsed.json")))

    # Save summary report
    report = {
        "execution_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_documents_discovered": len(manifest_data),
        "total_successful": successful,
        "total_failed": failed,
        "total_duration_seconds": total_duration,
        "processed_artifacts_on_disk": artifact_count,
        "documents": results
    }

    report_file = processed_dir / "corpus_ingestion_report.json"
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 80)
    print(" CORPUS INGESTION SUMMARY")
    print("=" * 80)
    print(f"Total Discovered Documents : {len(manifest_data)}")
    print(f"Successfully Ingested      : {successful}")
    print(f"Failed Ingestions          : {failed}")
    print(f"Processed JSON Artifacts   : {artifact_count} in {processed_dir}")
    print(f"Total Ingestion Time       : {total_duration}s")
    print(f"Report File Written To     : {report_file}")
    print("=" * 80)

    await close_db()

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_corpus_ingestion())
