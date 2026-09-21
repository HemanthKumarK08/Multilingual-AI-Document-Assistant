"""
Document Metadata and Ingestion Endpoints
"""

import re
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_db
from app.db.models import Document
from app.schemas import DocumentResponse, DocumentIngestRequest
from app.services.ingestion.hashing import compute_file_sha256

router = APIRouter()


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Filter active documents only"),
    db: AsyncSession = Depends(get_db)
):
    """Lists all registered institutional documents."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        from app.main import serve_frontend_or_landing
        return serve_frontend_or_landing()

    stmt = select(Document)
    if active_only:
        stmt = stmt.where(Document.is_active.is_(True))
    if category:
        stmt = stmt.where(Document.category == category)
    stmt = stmt.order_by(Document.display_title.asc())

    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves document details by doc_id."""
    stmt = select(Document).where(Document.doc_id == doc_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    return doc

@router.post("/ingest", response_model=dict)
async def ingest_document(
    payload: DocumentIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests a document file from disk into the system.
    Parses content, computes SHA-256, extracts structure, and persists metadata.
    """
    from app.services.ingestion.coordinator import default_ingestion_coordinator
    from app.services.ingestion.exceptions import IngestionError

    try:
        result = await default_ingestion_coordinator.ingest_document(
            db=db,
            file_path=payload.file_path,
            doc_id=payload.doc_id,
            display_title=payload.display_title,
            category=payload.category,
            version=payload.version,
            allow_reingest=payload.allow_reingest,
        )
        return result.model_dump()
    except IngestionError as ie:
        raise HTTPException(status_code=400, detail=ie.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal ingestion error: {str(e)}")

@router.post("/upload", response_model=dict)
async def upload_document(
    file: UploadFile = File(...),
    display_title: Optional[str] = Form(None),
    category: str = Form("academic_regulations"),
    version: str = Form("1.0"),
    allow_reingest: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts multipart document file upload (PDF, DOCX, TXT, MD), saves to raw storage,
    and runs the document ingestion, chunking, and ChromaDB indexing pipeline.
    """
    from app.services.ingestion.coordinator import default_ingestion_coordinator
    from app.services.ingestion.exceptions import IngestionError
    from app.services.ingestion.constants import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_BYTES

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{suffix}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum permitted limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )

    upload_dir = settings.DATA_DIRECTORY / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    clean_name = re.sub(r"[^a-zA-Z0-9._-]", "_", file.filename or "uploaded_file.txt")
    target_path = upload_dir / f"{uuid.uuid4().hex[:8]}_{clean_name}"
    target_path.write_bytes(content)

    # Compute hash to detect duplicates or determine stable doc_id
    sha256_hash = compute_file_sha256(target_path)
    stmt_hash = select(Document).where(Document.file_hash_sha256 == sha256_hash)
    res_hash = await db.execute(stmt_hash)
    existing_by_hash = res_hash.scalar_one_or_none()

    if existing_by_hash:
        doc_id = existing_by_hash.doc_id
    else:
        raw_stem = Path(file.filename or "DOC").stem
        clean_stem = re.sub(r"[^a-zA-Z0-9]", "-", raw_stem).upper()[:16].strip("-") or "DOC"
        doc_id = f"DOC-UP-{clean_stem}-{uuid.uuid4().hex[:6].upper()}"

    try:
        result = await default_ingestion_coordinator.ingest_document(
            db=db,
            file_path=str(target_path),
            doc_id=doc_id,
            display_title=display_title or file.filename,
            category=category,
            version=version,
            allow_reingest=allow_reingest,
        )

        # Automatic chunking & ChromaDB vector indexing
        if result.status == "parsed":
            try:
                from app.services.chunking.coordinator import default_chunking_coordinator
                from app.services.vector_store.coordinator import VectorStoreCoordinator

                parsed_artifact_path = result.details.get("artifact_path")
                if parsed_artifact_path and Path(parsed_artifact_path).exists():
                    chunked_artifact = default_chunking_coordinator.chunk_parsed_file(
                        parsed_artifact_path,
                        doc_metadata={"category": category, "file_hash_sha256": result.file_hash_sha256},
                        save_artifact=True
                    )
                    vsc = VectorStoreCoordinator()
                    vsc.index_document_artifact(chunked_artifact)

                    stmt_update = select(Document).where(Document.doc_id == doc_id)
                    res_update = await db.execute(stmt_update)
                    doc_rec = res_update.scalar_one_or_none()
                    if doc_rec:
                        doc_rec.status = "indexed"
                        doc_rec.chunk_count = len(chunked_artifact.chunks)
                        await db.commit()
                        result.status = "indexed"
            except Exception as index_err:
                logger.warning(f"Vector indexing skipped/failed for {doc_id}: {str(index_err)}")

        return result.model_dump()
    except IngestionError as ie:
        raise HTTPException(status_code=400, detail=ie.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal ingestion error: {str(e)}")
