# app/api/search.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple
import re

from app.db import SessionLocal
from app.api.auth import get_current_user
from app.vector.chroma_client import get_collection
from app.services.embeddings import embed_texts
from app.models.document import Document

router = APIRouter(prefix="/api", tags=["search"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

_word = re.compile(r"[A-Za-z0-9]{3,}")

def _tokenize(s: str) -> List[str]:
    return [w.lower() for w in _word.findall(s or "")]

def _matches_keyword(text: str, q: str, require_all_terms: bool) -> bool:
    q_words = set(_tokenize(q))
    if not q_words:
        return False
    t_words = set(_tokenize(text))
    return (q_words <= t_words) if require_all_terms else bool(q_words & t_words)

@router.get("/search")
def semantic_search_grouped(
    q: str = Query(..., min_length=2, description="Keyword(s) to find"),
    doc_limit: int = Query(50, ge=1, le=200, description="Max number of documents to return"),
    chunks_per_doc: int = Query(3, ge=1, le=20, description="Top chunks to show per document"),
    require_all_terms: bool = Query(False, description="All query words must appear in a chunk"),
    db: Session = Depends(get_db),
    me = Depends(get_current_user),
):
    """
    Keyword-first, no similarity cutoff:
      • Return ALL documents that contain the keyword(s) in at least one chunk.
      • Rank documents by best semantic score (cosine similarity) among their chunks.
      • Within each document, return the top `chunks_per_doc` chunks by score.
    """
    col = get_collection()
    q_emb = embed_texts([q])[0]

    # Over-fetch a big pool; we'll do strict keyword filtering ourselves.
    overfetch = 500  # adjust if you expect more data
    res = col.query(
        query_embeddings=[q_emb],
        n_results=overfetch,
        where={"user_id": me.id},
        include=["documents", "metadatas", "distances"],  # no "ids"
    )

    docs:  List[str]           = (res.get("documents") or [[]])[0] or []
    metas: List[Dict[str,Any]] = (res.get("metadatas") or [[]])[0] or []
    dists: List[float]         = (res.get("distances") or [[]])[0] or []

    # Score (1 - distance) just for ranking; filter ONLY by keyword presence.
    rows: List[Tuple[float, str, Dict[str, Any]]] = []
    for text, meta, dist in zip(docs, metas, dists):
        if not meta:
            continue
        if not _matches_keyword(text or "", q, require_all_terms):
            continue
        score = 1.0 - float(dist)  # cosine similarity in [0..1]
        rows.append((score, text or "", meta))

    if not rows:
        return {"query": q, "documents": []}

    # Bucket by document and rank within
    buckets: Dict[int, List[Tuple[float, str, Dict[str, Any]]]] = {}
    for score, text, meta in rows:
        doc_id = int(meta["document_id"])
        buckets.setdefault(doc_id, []).append((score, text, meta))

    grouped = []
    for doc_id, items in buckets.items():
        items.sort(key=lambda x: x[0], reverse=True)
        best_score = items[0][0]
        total_matches = len(items)

        row = db.query(Document).get(doc_id)
        filename = items[0][2].get("filename") or getattr(row, "filename", None)
        created_at = getattr(row, "created_at", None)

        snippets = []
        for score, text, meta in items[:chunks_per_doc]:
            snippets.append({
                "chunk_index": meta.get("chunk_index"),
                "score": round(score, 4),
                "snippet": text[:300] + ("…" if len(text) > 300 else "")
            })

        grouped.append({
            "document_id": doc_id,
            "filename": filename,
            "document_created_at": created_at,
            "best_score": round(best_score, 4),   # for ranking only
            "total_matches": total_matches,
            "snippets": snippets,
        })

    # Rank documents by best_score; cap to doc_limit
    grouped.sort(key=lambda d: d["best_score"], reverse=True)
    return {"query": q, "documents": grouped[:doc_limit]}
