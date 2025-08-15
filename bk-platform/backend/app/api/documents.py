# app/api/documents.py

from typing import Optional, List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.api.auth import get_current_user
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.services.files import save_upload_file
from app.services.text_extract import extract_text_from_bytes
from app.services.ingest import ingest_text_for_document

router = APIRouter(prefix="/api/documents", tags=["documents"])

# ---- DB session dependency (local helper)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==============
# POST /upload
# ==============
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    me = Depends(get_current_user),
):
    """
    Accept a single file (PDF/DOCX/TXT/MD), save to /uploads, extract text,
    chunk+embed into Chroma, and persist chunks in DB.
    """
    # Save to disk with size guard and MIME
    path, size, mime, data = save_upload_file(file)

    # Create document row
    doc = Document(
        user_id=me.id,
        filename=file.filename,
        path=path,
        size=size,
        mime_type=mime,
        metadata_json={"original_name": file.filename},
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Extract text
    text = extract_text_from_bytes(data, file.filename, mime)

    ingested_chunks = 0
    if text and text.strip():
        # Persist chunks in DB and upsert to vectorstore
        ingested_chunks = ingest_text_for_document(
            db,
            text=text,
            document_id=doc.id,
            user_id=me.id,
            filename=file.filename,
        )

    return {
        "id": doc.id,
        "filename": doc.filename,
        "size": size,
        "mime_type": mime,
        "ingested_chunks": ingested_chunks,
    }


# ==============
# GET /
# ==============
@router.get("")
def list_documents(
    db: Session = Depends(get_db),
    me = Depends(get_current_user),
    q: Optional[str] = Query(None, description="search by filename substring"),
):
    """List documents owned by current user, with optional filename filter."""
    query = db.query(Document).filter(Document.user_id == me.id)
    if q:
        query = query.filter(Document.filename.ilike(f"%{q}%"))
    docs: List[Document] = query.order_by(Document.id.desc()).all()

    out = []
    for d in docs:
        has_text = bool(
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == d.id)
            .first()
        )
        out.append(
            {
                "id": d.id,
                "filename": d.filename,
                "size": d.size,
                "mime_type": d.mime_type,
                "created_at": d.created_at,
                "has_text": has_text,
            }
        )
    return out


# ==============
# GET /{id}
# ==============
@router.get("/{doc_id}")
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    me = Depends(get_current_user),
):
    """Return document metadata + a small text preview if available."""
    d = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.user_id == me.id)
        .first()
    )
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")

    first_chunk = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == d.id)
        .order_by(DocumentChunk.position.asc())
        .first()
    )
    preview = (
        (first_chunk.content[:500] + "…")
        if first_chunk and first_chunk.content
        else None
    )

    return {
        "id": d.id,
        "filename": d.filename,
        "size": d.size,
        "mime_type": d.mime_type,
        "created_at": d.created_at,
        "metadata": d.metadata_json,
        "preview": preview,
    }


# ==============
# DELETE /{id}
# ==============
@router.delete("/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    me = Depends(get_current_user),
):
    """
    Delete document and its chunks from DB.
    (Note: This MVP doesn’t remove from the vector DB; we can add that later.)
    """
    d = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.user_id == me.id)
        .first()
    )
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")

    db.query(DocumentChunk).filter(DocumentChunk.document_id == d.id).delete()
    db.delete(d)
    db.commit()
    return
