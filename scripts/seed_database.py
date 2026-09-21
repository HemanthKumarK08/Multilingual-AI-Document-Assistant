#!/usr/bin/env python3
"""
Database Seeding & Initialization Script
Initializes SQLite database tables, seeds the default administrator account,
and synchronizes document metadata from data/raw/corpus_manifest.json.
"""

import sys
import asyncio
import json
import uuid
from pathlib import Path
from sqlalchemy import select

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import engine, AsyncSessionLocal, init_db
from app.db.models import User, Document

async def seed_admin(session) -> None:
    """Seeds default administrator account if none exists."""
    stmt = select(User).where(User.username == settings.ADMIN_DEFAULT_USERNAME)
    result = await session.execute(stmt)
    existing_admin = result.scalar_one_or_none()

    if not existing_admin:
        admin_user = User(
            user_id=f"usr_{uuid.uuid4().hex[:12]}",
            username=settings.ADMIN_DEFAULT_USERNAME,
            role="admin",
            password_hash=hash_password(settings.ADMIN_DEFAULT_PASSWORD),
            is_active=True
        )
        session.add(admin_user)
        await session.commit()
        print(f"  [+] Created default admin user: '{settings.ADMIN_DEFAULT_USERNAME}'")
    else:
        print(f"  [i] Admin user '{settings.ADMIN_DEFAULT_USERNAME}' already exists.")

async def seed_documents_from_manifest(session) -> None:
    """Synchronizes document metadata from corpus_manifest.json into SQLite database."""
    manifest_path = PROJECT_ROOT / "data" / "raw" / "corpus_manifest.json"
    if not manifest_path.exists():
        print(f"  [!] Corpus manifest not found at {manifest_path}. Skipping document seeding.")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_docs = json.load(f)

    seeded_count = 0
    updated_count = 0

    for doc_data in manifest_docs:
        doc_id = doc_data["document_id"]
        stmt = select(Document).where(Document.doc_id == doc_id)
        result = await session.execute(stmt)
        existing_doc = result.scalar_one_or_none()

        rel_path = doc_data["file_path"]
        abs_file = PROJECT_ROOT / rel_path
        file_size = abs_file.stat().st_size if abs_file.exists() else 0

        if not existing_doc:
            new_doc = Document(
                doc_id=doc_id,
                filename=Path(rel_path).name,
                display_title=doc_data["title"],
                category=doc_data["category"],
                description=doc_data.get("description", ""),
                language=doc_data.get("language", "en"),
                file_type=doc_data.get("file_type", "pdf"),
                file_size_bytes=file_size,
                file_hash_sha256=doc_data.get("checksum_sha256", f"hash_{doc_id}"),
                storage_path=rel_path,
                page_count=doc_data.get("expected_page_count", 1),
                chunk_count=0,
                version=doc_data.get("version", "1.0"),
                status="uploaded",
                is_active=doc_data.get("is_active", True)
            )
            session.add(new_doc)
            seeded_count += 1
        else:
            existing_doc.display_title = doc_data["title"]
            existing_doc.category = doc_data["category"]
            existing_doc.is_active = doc_data.get("is_active", True)
            updated_count += 1

    await session.commit()
    print(f"  [+] Document sync: {seeded_count} inserted, {updated_count} verified/updated.")

async def main() -> int:
    print("=" * 70)
    print(" MULTILINGUAL AI DOCUMENT ASSISTANT — DATABASE SEED & INIT")
    print("=" * 70)
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"SQLite Path : {settings.absolute_db_path}")
    print("-" * 70)

    try:
        print("[1] Initializing database tables...")
        await init_db()
        print("  [+] All SQLAlchemy tables created successfully.")

        print("\n[2] Seeding admin credentials & corpus metadata...")
        async with AsyncSessionLocal() as session:
            await seed_admin(session)
            await seed_documents_from_manifest(session)

        print("\n" + "=" * 70)
        print(" DATABASE INITIALIZATION & SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 70)
        return 0
    except Exception as e:
        print(f"\n[!] Database seeding failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await engine.dispose()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
