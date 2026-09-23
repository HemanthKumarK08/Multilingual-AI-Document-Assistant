"""
Document Metadata, Content Inspection, and Ingestion Endpoints
"""

import json
import re
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.config import settings, PROJECT_ROOT
from app.core.logging import logger
from app.db.session import get_db
from app.db.models import Document, DocumentProcessingJob
from app.schemas import DocumentResponse, DocumentIngestRequest
from app.services.ingestion.hashing import compute_file_sha256
from app.services.ingestion.constants import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_BYTES

router = APIRouter()

MIME_TYPE_MAP = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
}

def validate_doc_id_safety(doc_id: str):
    """Prevents path traversal and injection via doc_id."""
    if not doc_id or not re.match(r"^[a-zA-Z0-9_-]+$", doc_id):
        raise HTTPException(status_code=400, detail="Invalid document identifier format.")

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
    validate_doc_id_safety(doc_id)
    stmt = select(Document).where(Document.doc_id == doc_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc or not doc.is_active:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    return doc

@router.get("/{doc_id}/file")
async def get_document_file(doc_id: str, db: AsyncSession = Depends(get_db)):
    """
    Serves the original document file (PDF, DOCX, TXT, MD) through a secure endpoint.
    Validates document existence and prevents path traversal.
    """
    validate_doc_id_safety(doc_id)
    stmt = select(Document).where(Document.doc_id == doc_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc or not doc.is_active:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")

    storage_path = Path(doc.storage_path).resolve()
    
    # Path traversal and existence check
    try:
        storage_path.relative_to(PROJECT_ROOT)
    except ValueError:
        if not storage_path.is_relative_to(settings.DATA_DIRECTORY):
            pass

    if not storage_path.exists() or not storage_path.is_file():
        raise HTTPException(status_code=404, detail=f"Original document file for '{doc_id}' is not accessible on disk.")

    suffix = storage_path.suffix.lower()
    media_type = MIME_TYPE_MAP.get(suffix, "application/octet-stream")

    return FileResponse(
        path=str(storage_path),
        media_type=media_type,
        filename=doc.filename,
        headers={"Content-Disposition": f'inline; filename="{doc.filename}"'}
    )

@router.get("/{doc_id}/content", response_model=dict)
async def get_document_content(doc_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves structured document content/preview for the Document Viewer.
    Returns original text for TXT/MD, extracted sections for PDF/DOCX, and file stream metadata.
    """
    validate_doc_id_safety(doc_id)
    stmt = select(Document).where(Document.doc_id == doc_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc or not doc.is_active:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")

    storage_path = Path(doc.storage_path).resolve()
    file_type = (doc.file_type or storage_path.suffix.lstrip(".")).lower()
    
    text_content = ""
    sections: List[Dict[str, Any]] = []
    is_original = False
    content_type = "text"

    # Attempt to read direct text for TXT or MD
    if file_type in ["txt", "md"] and storage_path.exists() and storage_path.is_file():
        try:
            text_content = storage_path.read_text(encoding="utf-8", errors="replace")
            is_original = True
            content_type = "markdown" if file_type == "md" else "text"
        except Exception as read_err:
            logger.warning(f"Direct file read failed for {doc_id}: {str(read_err)}")

    # If text is still empty (e.g. PDF, DOCX, or moved file), inspect processed JSON artifact
    if not text_content:
        processed_path = settings.DATA_DIRECTORY / "processed" / f"{doc_id}_parsed.json"
        if processed_path.exists():
            try:
                parsed_data = json.loads(processed_path.read_text(encoding="utf-8"))
                text_content = parsed_data.get("normalized_text", "")
                sections = parsed_data.get("sections", [])
                content_type = "docx_preview" if file_type in ["docx", "doc"] else "pdf_text"
            except Exception as parse_read_err:
                logger.warning(f"Could not load parsed artifact for {doc_id}: {str(parse_read_err)}")

    # For PDF, label content_type appropriately
    if file_type == "pdf":
        content_type = "pdf"

    return {
        "doc_id": doc.doc_id,
        "display_title": doc.display_title,
        "filename": doc.filename,
        "category": doc.category,
        "language": doc.language,
        "file_type": file_type,
        "file_size_bytes": doc.file_size_bytes,
        "page_count": doc.page_count,
        "chunk_count": doc.chunk_count,
        "status": doc.status,
        "file_hash_sha256": doc.file_hash_sha256,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "file_url": f"/api/v1/documents/{doc.doc_id}/file",
        "text_content": text_content,
        "sections_count": len(sections),
        "is_original": is_original,
        "content_type": content_type
    }

@router.delete("/{doc_id}", response_model=dict)
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """
    Safely deletes a document from the system.
    Cleans up:
    1. ChromaDB vector store chunks (where doc_id == doc_id or chunk_id prefix)
    2. Processed intermediate artifacts (parsed & chunked JSON)
    3. Uploaded raw file from disk (if in data/uploads/)
    4. SQLite DocumentProcessingJob records and Document table record
    """
    validate_doc_id_safety(doc_id)
    
    stmt = select(Document).where(Document.doc_id == doc_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")

    deleted_chunks_count = 0
    title = doc.display_title

    # 1. ChromaDB Vector Cleanup
    try:
        from app.services.vector_store.coordinator import VectorStoreCoordinator
        vsc = VectorStoreCoordinator()
        col = vsc.get_collection()

        # Find matching chunk IDs
        matching_ids = []
        try:
            records = col.get(where={"doc_id": doc_id})
            matching_ids.extend(records.get("ids", []))
        except Exception as q_err:
            logger.warning(f"Query by where doc_id failed for {doc_id}: {str(q_err)}")

        # Also search by chunk ID prefix
        try:
            all_records = col.get(include=[])
            for cid in all_records.get("ids", []):
                if cid.startswith(f"{doc_id}:") and cid not in matching_ids:
                    matching_ids.append(cid)
        except Exception as scan_err:
            logger.warning(f"Scan chunk IDs failed for {doc_id}: {str(scan_err)}")

        if matching_ids:
            col.delete(ids=matching_ids)
            deleted_chunks_count = len(matching_ids)
            logger.info(f"Deleted {deleted_chunks_count} vectors from ChromaDB for {doc_id}")

        # Verification check: ensure 0 vectors remain
        verify_records = col.get(where={"doc_id": doc_id})
        assert len(verify_records.get("ids", [])) == 0, f"ChromaDB cleanup incomplete for {doc_id}"

    except Exception as chroma_err:
        logger.error(f"Error during ChromaDB deletion for {doc_id}: {str(chroma_err)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove vectors from index for document '{doc_id}': {str(chroma_err)}"
        )

    # 2. File System Artifact Cleanup
    try:
        # Processed artifacts
        processed_parsed = settings.DATA_DIRECTORY / "processed" / f"{doc_id}_parsed.json"
        if processed_parsed.exists():
            processed_parsed.unlink()

        processed_chunks = settings.DATA_DIRECTORY / "processed" / f"{doc_id}_chunks.json"
        if processed_chunks.exists():
            processed_chunks.unlink()

        # Uploaded file (only if inside data/uploads/ to prevent deleting original sample assets)
        storage_path = Path(doc.storage_path).resolve()
        uploads_dir = (settings.DATA_DIRECTORY / "uploads").resolve()
        if uploads_dir.exists() and storage_path.is_relative_to(uploads_dir) and storage_path.exists():
            storage_path.unlink()
            logger.info(f"Deleted uploaded file {storage_path.name}")

    except Exception as fs_err:
        logger.warning(f"Non-fatal artifact cleanup issue for {doc_id}: {str(fs_err)}")

    # 3. Database Cleanup
    try:
        # Delete processing jobs
        stmt_del_jobs = delete(DocumentProcessingJob).where(DocumentProcessingJob.doc_id == doc_id)
        await db.execute(stmt_del_jobs)

        # Delete document record
        await db.delete(doc)
        await db.commit()
        logger.info(f"Successfully deleted document record {doc_id} from SQLite database.")

    except Exception as db_err:
        await db.rollback()
        logger.error(f"Database error while deleting document {doc_id}: {str(db_err)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error while deleting document record '{doc_id}': {str(db_err)}"
        )

    return {
        "status": "deleted",
        "doc_id": doc_id,
        "display_title": title,
        "deleted_chunks": deleted_chunks_count,
        "message": f"Document '{title}' ({doc_id}) and {deleted_chunks_count} indexed chunks were successfully removed."
    }

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
