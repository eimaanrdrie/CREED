from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.domain import get_domain_db
from app.domain.models import DocumentChunk, EvidenceDocument
from app.services.embeddings import EmbeddingError, EmbeddingService
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1200)
    top_k: int = Field(default=8, ge=1, le=25)
    source: str | None = None
    document_type: str | None = None
    version: str | None = None


@router.get("/status")
def retrieval_status(db: Session = Depends(get_domain_db)) -> dict:
    engine = EmbeddingService().health()
    chunk_count = db.scalar(select(func.count(DocumentChunk.id))) or 0
    indexed_docs = db.scalar(select(func.count(EvidenceDocument.id)).where(EvidenceDocument.index_status.in_(["INDEXED", "INDEXED_DEGRADED"]))) or 0
    pending_docs = db.scalar(select(func.count(EvidenceDocument.id)).where(EvidenceDocument.index_status == "PENDING")) or 0
    return {"embedding_engine": engine, "chunks": chunk_count, "indexed_documents": indexed_docs, "pending_documents": pending_docs}


@router.post("/index/{document_id}")
def index_document(document_id: str, db: Session = Depends(get_domain_db)) -> dict:
    doc = db.get(EvidenceDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="DOCUMENT_NOT_FOUND")
    try:
        return RetrievalService().index_document(db, doc)
    except (EmbeddingError, ValueError) as exc:
        raise HTTPException(status_code=503 if isinstance(exc, EmbeddingError) else 422, detail=str(exc)) from exc


@router.post("/index-pending")
def index_pending(db: Session = Depends(get_domain_db)) -> dict:
    results = RetrievalService().index_pending(db)
    return {"indexed": len(results), "documents": results}


@router.post("/search")
def search(request: SearchRequest, db: Session = Depends(get_domain_db)) -> dict:
    try:
        return RetrievalService().search(db, **request.model_dump())
    except EmbeddingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
