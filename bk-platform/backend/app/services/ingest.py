from app.services.chunking import simple_chunks
from app.services.embeddings import embed_texts
from app.vector.chroma_client import get_collection
from sqlalchemy.orm import Session
from app.models.chunk import DocumentChunk

def ingest_text_for_document(
    db: Session, *, text: str, document_id: int, user_id: int, filename: str
) -> int:
    chunks = simple_chunks(text)
    if not chunks:
        return 0

    # Save chunks to DB
    db_chunks = [DocumentChunk(document_id=document_id, content=ch, position=i)
                 for i, ch in enumerate(chunks)]
    db.add_all(db_chunks)
    db.commit()

    # Embed + upsert into Chroma, scoped by user_id
    embeddings = embed_texts(chunks)
    col = get_collection()
    ids = [f"doc{document_id}_chunk{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": document_id, "chunk_index": i, "user_id": user_id, "filename": filename}
        for i in range(len(chunks))
    ]
    col.upsert(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)
    return len(chunks)
