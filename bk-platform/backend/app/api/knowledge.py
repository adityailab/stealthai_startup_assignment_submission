# app/api/knowledge.py
from __future__ import annotations
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import re

from app.api.auth import get_current_user
from app.db import SessionLocal
from app.services.embeddings import embed_texts
from app.vector.chroma_client import get_collection
from app.models.document import Document
from app.services.llm import chat

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- tokenization & matching gates ----------
_word = re.compile(r"[A-Za-z0-9]{2,}")

def _tokens(s: str) -> List[str]:
    return [w.lower() for w in _word.findall(s or "")]

def _has_query_word(text: str, q: str) -> bool:
    qset = set(_tokens(q))
    if not qset:
        return False
    tset = set(_tokens(text))
    return bool(qset & tset)

def _has_all_terms(text: str, q: str) -> bool:
    qset = set(_tokens(q))
    if not qset:
        return False
    tset = set(_tokens(text))
    return qset <= tset

def _has_phrase(text: str, phrase: str) -> bool:
    if not phrase:
        return True
    return phrase.lower() in (text or "").lower()

# ---------- request/response models ----------
class AskRequest(BaseModel):
    question: str = Field(..., min_length=2)
    k: int = Field(8, ge=1, le=20, description="Top chunks to pass to the model after filtering")
    max_context_tokens: int = Field(800, ge=200, le=4000)
    # strict gating (set to True for very precise queries)
    require_all_terms: bool = Field(False, description="All query words must appear in a kept chunk")
    phrase: str | None = Field(None, description="Optional phrase that must appear verbatim in a kept chunk")
    # runtime overrides (optional)
    provider: str | None = Field(None, description="Force 'openai' or 'ollama' (default auto)")
    model: str | None = Field(None, description="Override model name (e.g., 'phi3:3.8b')")
    # output shaping
    max_answer_chars: int = Field(140, ge=30, le=600, description="Trim output to this many characters")

class AskResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]

# ---------- very strict system prompt ----------
SYSTEM_PROMPT = (
    "You are a retrieval QA assistant.\n"
    "Follow ALL rules:\n"
    "1) Use ONLY the provided context. If the context does not contain the answer, reply exactly: "
    "'Not found in the provided documents.'\n"
    "2) Do NOT repeat or paraphrase the question.\n"
    "3) Do NOT repeat or paraphrase the context.\n"
    "4) Answer with a single short sentence or phrase. No preamble, no extra commentary.\n"
    
)

def _build_context(chunks: List[Dict[str, Any]], token_limit: int) -> str:
    # naive budget: ~4 chars per token
    budget = token_limit * 4
    out, used = [], 0
    for c in chunks:
        block = f"[{c['filename']} #{c['chunk_index']}]\n{c['content']}\n---\n"
        if used + len(block) > budget:
            break
        out.append(block)
        used += len(block)
    return "".join(out).strip()

def _post_process(answer: str, max_chars: int) -> str:
    """Strip echoes and compress to a single, short line."""
    # remove any leading 'Question:' or 'Context:' dumps
    for pat in (r"^Question:.*?\n\n", r"^Context:.*"):
        answer = re.sub(pat, "", answer, flags=re.DOTALL).strip()
    # replace newlines with spaces, collapse spaces
    answer = re.sub(r"\s+", " ", answer).strip()
    # hard cap length
    if len(answer) > max_chars:
        answer = answer[: max_chars - 1].rstrip() + "…"
    return answer

@router.post("/ask", response_model=AskResponse)
def ask_knowledge(
    payload: AskRequest = Body(...),
    db: Session = Depends(get_db),
    me = Depends(get_current_user),
):
    q = payload.question.strip()

    # 1) Retrieve a pool from vector DB
    col = get_collection()
    q_emb = embed_texts([q])[0]
    res = col.query(
        query_embeddings=[q_emb],
        n_results=max(payload.k * 4, 20),   # over-fetch for better recall
        where={"user_id": me.id},
        include=["documents", "metadatas", "distances"],
    )

    docs = (res.get("documents") or [[]])[0] or []
    metas = (res.get("metadatas") or [[]])[0] or []
    dists = (res.get("distances") or [[]])[0] or []

    # 2) Strict keyword/phrase gates; keep for ranking
    rows = []
    for text, meta, dist in zip(docs, metas, dists):
        if not meta:
            continue
        t = text or ""
        if payload.require_all_terms:
            ok = _has_all_terms(t, q)
        else:
            ok = _has_query_word(t, q)
        if not ok:
            continue
        if payload.phrase and not _has_phrase(t, payload.phrase):
            continue
        score = 1.0 - float(dist)  # rank only
        rows.append({
            "score": score,
            "content": t,
            "document_id": int(meta["document_id"]),
            "filename": meta.get("filename"),
            "chunk_index": meta.get("chunk_index"),
        })

    # 3) If no chunks pass the gate: hard fail (no LLM call)
    if not rows:
        return AskResponse(answer="Not found in the provided documents.", citations=[])

    # 4) Take top-k by score
    rows.sort(key=lambda r: r["score"], reverse=True)
    top = rows[: payload.k]

    # 5) Build compact context
    context = _build_context(top, payload.max_context_tokens)

    # 6) Ask the LLM (defaults to Ollama + your .env model, e.g., phi3:3.8b)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",  "content": f"Question: {q}\n\nContext:\n{context}"},
    ]
    raw = chat(messages, provider=payload.provider or "hf", model=payload.model).strip()
    answer = _post_process(raw, payload.max_answer_chars)

    # If the model ignored instructions and didn't answer, force the fallback
    if not answer or answer.lower().startswith("question:") or answer.lower().startswith("context:"):
        answer = "Not found in the provided documents."

    # 7) Citations for the exact chunks used
    citations: List[Dict[str, Any]] = []
    for r in top:
        doc = db.query(Document).get(r["document_id"])
        citations.append({
            "document_id": r["document_id"],
            "filename": r["filename"] or (doc.filename if doc else None),
            "chunk_index": r["chunk_index"],
            "score": round(r["score"], 4),
            "snippet": r["content"][:240] + ("…" if len(r["content"]) > 240 else ""),
        })

    return AskResponse(answer=answer, citations=citations)
