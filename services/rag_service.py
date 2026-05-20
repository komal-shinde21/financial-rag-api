"""
RAG Pipeline (FAISS version - 100% offline, no Docker, no internet needed)
==========================================================================
Document -> PDF text extraction -> Chunking -> Embeddings -> FAISS index (local file)
Query    -> Embed -> FAISS search (top 20) -> Cross-encoder rerank -> Top 5
"""

from __future__ import annotations

import json
import os
import pickle
import uuid
from pathlib import Path

import faiss
import numpy as np
import pdfplumber
from sentence_transformers import SentenceTransformer, CrossEncoder
from sqlalchemy.orm import Session

from config import get_settings
from models.document import Document
from schemas.rag import ChunkResult

settings = get_settings()

CHUNK_SIZE    = 500
CHUNK_OVERLAP = 100
FAISS_DIR     = "./faiss_db"
INDEX_FILE    = os.path.join(FAISS_DIR, "index.faiss")
META_FILE     = os.path.join(FAISS_DIR, "metadata.pkl")
VECTOR_DIM    = 384   # all-MiniLM-L6-v2 output size

_embedder  = None
_reranker  = None
_index     = None      # faiss index
_metadata  = []        # list of dicts, one per vector


# ── Model loaders ─────────────────────────────────────────────────────────────

def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embedder


def _get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(settings.RERANKER_MODEL)
    return _reranker


# ── FAISS index helpers ───────────────────────────────────────────────────────

def _load_index():
    global _index, _metadata
    Path(FAISS_DIR).mkdir(parents=True, exist_ok=True)
    if os.path.exists(INDEX_FILE) and os.path.exists(META_FILE):
        _index = faiss.read_index(INDEX_FILE)
        with open(META_FILE, "rb") as f:
            _metadata = pickle.load(f)
    else:
        _index = faiss.IndexFlatIP(VECTOR_DIM)   # Inner Product = cosine on normalised vecs
        _metadata = []


def _save_index():
    faiss.write_index(_index, INDEX_FILE)
    with open(META_FILE, "wb") as f:
        pickle.dump(_metadata, f)


def _get_index():
    global _index
    if _index is None:
        _load_index()
    return _index


# ── Step 1: PDF text extraction ───────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> str:
    parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
    return "\n".join(parts)


# ── Step 2: Chunking ──────────────────────────────────────────────────────────

def chunk_text(text: str) -> list[str]:
    sentences = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        for part in line.replace(". ", ".|").split("|"):
            sentences.append(part.strip())

    chunks, current = [], ""
    for sentence in sentences:
        if not sentence:
            continue
        if len(current) + len(sentence) + 1 <= CHUNK_SIZE:
            current += (" " if current else "") + sentence
        else:
            if current:
                chunks.append(current.strip())
            current = (current[-CHUNK_OVERLAP:] + " " + sentence) if len(current) > CHUNK_OVERLAP else sentence
    if current:
        chunks.append(current.strip())
    return chunks


# ── Step 3 & 4: Embed + store in FAISS ───────────────────────────────────────

def index_document(doc: Document, db: Session) -> int:
    raw_text = extract_text_from_pdf(doc.file_path)
    if not raw_text.strip():
        raise ValueError("PDF is empty or has no extractable text")

    chunks = chunk_text(raw_text)
    if not chunks:
        raise ValueError("No chunks could be generated")

    embedder = _get_embedder()
    vectors  = embedder.encode(chunks, show_progress_bar=False, normalize_embeddings=True)

    idx = _get_index()
    idx.add(np.array(vectors, dtype="float32"))

    for i, chunk in enumerate(chunks):
        _metadata.append({
            "document_id":   doc.id,
            "title":         doc.title,
            "company_name":  doc.company_name,
            "document_type": doc.document_type,
            "chunk_index":   i,
            "chunk_text":    chunk,
        })

    _save_index()
    doc.is_indexed = True
    db.commit()
    return len(chunks)


def remove_document_embeddings(document_id: str) -> None:
    global _metadata, _index
    # Rebuild index without the removed document
    keep = [(i, m) for i, m in enumerate(_metadata) if m["document_id"] != document_id]
    if not keep:
        _index    = faiss.IndexFlatIP(VECTOR_DIM)
        _metadata = []
        _save_index()
        return

    keep_indices = [i for i, _ in keep]
    embedder     = _get_embedder()

    # Re-embed kept chunks (simple rebuild approach)
    texts   = [m["chunk_text"] for _, m in keep]
    vectors = embedder.encode(texts, normalize_embeddings=True)

    _index    = faiss.IndexFlatIP(VECTOR_DIM)
    _metadata = [m for _, m in keep]
    _index.add(np.array(vectors, dtype="float32"))
    _save_index()


# ── Step 5: Search + rerank ───────────────────────────────────────────────────

def semantic_search(query: str, top_k: int = 5, pre_rerank_k: int = 20) -> list[ChunkResult]:
    idx = _get_index()
    if idx.ntotal == 0:
        return []

    embedder  = _get_embedder()
    query_vec = embedder.encode([query], normalize_embeddings=True)

    k       = min(pre_rerank_k, idx.ntotal)
    scores, indices = idx.search(np.array(query_vec, dtype="float32"), k)

    hits = []
    for score, i in zip(scores[0], indices[0]):
        if i == -1:
            continue
        hits.append((_metadata[i], float(score)))

    if not hits:
        return []

    reranker      = _get_reranker()
    pairs         = [(query, m["chunk_text"]) for m, _ in hits]
    rerank_scores = reranker.predict(pairs).tolist()

    scored = sorted(zip(hits, rerank_scores), key=lambda x: x[1], reverse=True)

    return [
        ChunkResult(
            document_id  = meta["document_id"],
            title        = meta["title"],
            company_name = meta["company_name"],
            document_type= meta["document_type"],
            chunk_text   = meta["chunk_text"],
            score        = round(float(score), 4),
        )
        for (meta, _), score in scored[:top_k]
    ]


def get_document_context(document_id: str) -> list[str]:
    _get_index()
    chunks = [m for m in _metadata if m["document_id"] == document_id]
    chunks.sort(key=lambda m: m.get("chunk_index", 0))
    return [m["chunk_text"] for m in chunks]
