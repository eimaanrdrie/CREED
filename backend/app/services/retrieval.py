from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, select, text as sql_text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.models import DocumentChunk, EvidenceDocument
from app.services.embeddings import EmbeddingBatch, EmbeddingService

WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-/]{1,}")


@dataclass(frozen=True)
class TextChunk:
    index: int
    text: str
    start_char: int
    end_char: int


def chunk_text(text: str, *, size: int, overlap: int) -> list[TextChunk]:
    clean = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not clean:
        return []
    if overlap >= size:
        raise ValueError("CHUNK_OVERLAP_MUST_BE_SMALLER_THAN_SIZE")

    chunks: list[TextChunk] = []
    start = 0
    index = 0
    length = len(clean)
    while start < length:
        target_end = min(length, start + size)
        end = target_end
        if target_end < length:
            window_start = min(target_end, start + max(1, size // 2))
            candidates = [clean.rfind("\n\n", window_start, target_end), clean.rfind("\n", window_start, target_end), clean.rfind(". ", window_start, target_end)]
            best = max(candidates)
            if best > start:
                end = best + (2 if clean[best:best+2] == ". " else 1)
        fragment = clean[start:end].strip()
        if fragment:
            actual_start = clean.find(fragment, start, end + 1)
            actual_start = start if actual_start < 0 else actual_start
            chunks.append(TextChunk(index=index, text=fragment, start_char=actual_start, end_char=actual_start + len(fragment)))
            index += 1
        if end >= length:
            break
        start = max(start + 1, end - overlap)
    return chunks


def encode_vector(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.9f}" for value in vector) + "]"


def decode_vector(value: str) -> list[float]:
    stripped = value.strip()
    if not stripped.startswith("[") or not stripped.endswith("]"):
        return []
    try:
        return [float(part) for part in stripped[1:-1].split(",") if part]
    except ValueError:
        return []


def cosine(a: list[float], b: list[float]) -> float:
    if not a or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in WORD_RE.finditer(text)]


def bm25_scores(query: str, texts: list[str]) -> list[float]:
    qterms = list(dict.fromkeys(tokenize(query)))
    docs = [tokenize(text) for text in texts]
    if not qterms or not docs:
        return [0.0] * len(texts)
    avgdl = sum(len(d) for d in docs) / max(1, len(docs))
    dfs = {term: sum(1 for d in docs if term in set(d)) for term in qterms}
    n = len(docs)
    k1, b = 1.5, 0.75
    scores: list[float] = []
    for doc in docs:
        counts = Counter(doc)
        dl = len(doc)
        score = 0.0
        for term in qterms:
            df = dfs[term]
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            tf = counts[term]
            if tf:
                denom = tf + k1 * (1 - b + b * dl / max(avgdl, 1.0))
                score += idf * (tf * (k1 + 1)) / denom
        scores.append(score)
    return scores


class RetrievalService:
    def __init__(self, embedding_service: EmbeddingService | None = None):
        self.settings = get_settings()
        self.embedding_service = embedding_service or EmbeddingService()

    def index_document(self, db: Session, document: EvidenceDocument) -> dict[str, object]:
        chunks = chunk_text(
            document.extracted_text or "",
            size=self.settings.chunk_size_chars,
            overlap=self.settings.chunk_overlap_chars,
        )
        if not chunks:
            document.index_status = "FAILED"
            db.commit()
            raise ValueError("DOCUMENT_HAS_NO_INDEXABLE_TEXT")

        batch: EmbeddingBatch = self.embedding_service.embed([chunk.text for chunk in chunks])
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        for chunk, vector in zip(chunks, batch.vectors):
            db.add(DocumentChunk(
                document_id=document.id,
                chunk_index=chunk.index,
                text=chunk.text,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                chunk_hash=hashlib.sha256(chunk.text.encode("utf-8")).hexdigest(),
                embedding_vector=encode_vector(vector),
                embedding_provider=batch.provider,
                embedding_model=batch.model,
                embedding_dimensions=batch.dimensions,
                embedding_degraded=batch.degraded,
                metadata_json={"source": document.source, "document_type": document.document_type, "version": document.version},
            ))
        document.index_status = "INDEXED_DEGRADED" if batch.degraded else "INDEXED"
        document.indexed_at = datetime.now(timezone.utc)
        document.chunk_count = len(chunks)
        document.embedding_model = batch.model
        document.embedding_degraded = batch.degraded
        db.commit()
        return {
            "document_id": document.id,
            "chunk_count": len(chunks),
            "provider": batch.provider,
            "model": batch.model,
            "dimensions": batch.dimensions,
            "degraded": batch.degraded,
        }

    def index_pending(self, db: Session) -> list[dict[str, object]]:
        docs = list(db.scalars(select(EvidenceDocument).where(EvidenceDocument.parse_status == "PARSED").order_by(EvidenceDocument.uploaded_at)))
        results = []
        for doc in docs:
            if doc.index_status in {"INDEXED", "INDEXED_DEGRADED"}:
                continue
            try:
                results.append(self.index_document(db, doc))
            except Exception:
                db.rollback()
                doc = db.get(EvidenceDocument, doc.id)
                if doc:
                    doc.index_status = "FAILED"
                    db.commit()
        return results

    def search(
        self,
        db: Session,
        *,
        query: str,
        top_k: int = 8,
        source: str | None = None,
        document_type: str | None = None,
        version: str | None = None,
    ) -> dict[str, object]:
        query = query.strip()
        if not query:
            raise ValueError("EMPTY_SEARCH_QUERY")
        stmt = select(DocumentChunk, EvidenceDocument).join(EvidenceDocument, EvidenceDocument.id == DocumentChunk.document_id)
        if source:
            stmt = stmt.where(EvidenceDocument.source == source.strip().upper())
        if document_type:
            stmt = stmt.where(EvidenceDocument.document_type == document_type.strip().upper())
        if version:
            stmt = stmt.where(EvidenceDocument.version == version.strip())
        rows = list(db.execute(stmt))
        if not rows:
            return {"query": query, "results": [], "searched_chunks": 0, "embedding": None}

        use_keyword_only = len(rows) <= self.settings.retrieval_keyword_only_max_chunks
        qbatch = None if use_keyword_only else self.embedding_service.embed([query])
        qvector = [] if qbatch is None else qbatch.vectors[0]
        pg_semantic: dict[str, float] = {}
        bind = db.get_bind()
        if qbatch is not None and bind is not None and bind.dialect.name == "postgresql":
            # On PostgreSQL M05 uses pgvector's cosine distance operator. SQLite/test
            # environments use the mathematically equivalent application-side fallback.
            vector_literal = encode_vector(qvector)
            scored = db.execute(sql_text(
                "SELECT id, 1 - (embedding_vector <=> CAST(:query_vector AS vector)) AS semantic_score FROM document_chunks"
            ), {"query_vector": vector_literal})
            pg_semantic = {str(row.id): float(row.semantic_score or 0.0) for row in scored}
        texts = [chunk.text for chunk, _doc in rows]
        keyword_raw = bm25_scores(query, texts)
        max_keyword = max(keyword_raw) if keyword_raw else 0.0
        results = []
        qtokens = set(tokenize(query))
        for position, ((chunk, doc), kw_raw) in enumerate(zip(rows, keyword_raw)):
            semantic = 0.0 if qbatch is None else max(0.0, pg_semantic.get(chunk.id, cosine(qvector, decode_vector(chunk.embedding_vector))))
            keyword = kw_raw / max_keyword if max_keyword > 0 else 0.0
            meta_text = " ".join(filter(None, [doc.title, doc.document_type, doc.version or "", doc.source])).lower()
            metadata = 1.0 if any(token in meta_text for token in qtokens) else 0.0
            if qbatch is None:
                score = (0.85 * keyword) + (0.15 * metadata)
            else:
                score = (
                    self.settings.retrieval_semantic_weight * semantic
                    + self.settings.retrieval_keyword_weight * keyword
                    + self.settings.retrieval_metadata_weight * metadata
                )
            results.append({
                "rank_seed": position,
                "chunk_id": chunk.id,
                "document_id": doc.id,
                "document_title": doc.title,
                "document_type": doc.document_type,
                "source": doc.source,
                "version": doc.version,
                "chunk_index": chunk.chunk_index,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "excerpt": chunk.text[:650],
                "score": round(score, 6),
                "semantic_score": round(semantic, 6),
                "keyword_score": round(keyword, 6),
                "metadata_score": round(metadata, 6),
                "embedding_model": chunk.embedding_model,
                "embedding_degraded": chunk.embedding_degraded,
                "citation": f"{doc.title} · chunk {chunk.chunk_index + 1} · chars {chunk.start_char}-{chunk.end_char}",
            })
        results.sort(key=lambda item: (-item["score"], item["rank_seed"]))
        for item in results:
            item.pop("rank_seed", None)
        return {
            "query": query,
            "results": results[: max(1, min(top_k, 25))],
            "searched_chunks": len(rows),
            "embedding": None if qbatch is None else {
                "provider": qbatch.provider,
                "model": qbatch.model,
                "dimensions": qbatch.dimensions,
                "degraded": qbatch.degraded,
            },
            "weights": {
                "semantic": 0.0 if qbatch is None else self.settings.retrieval_semantic_weight,
                "keyword": 0.85 if qbatch is None else self.settings.retrieval_keyword_weight,
                "metadata": 0.15 if qbatch is None else self.settings.retrieval_metadata_weight,
            },
        }
