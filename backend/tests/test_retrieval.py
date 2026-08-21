from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.domain.models import DocumentChunk, EvidenceDocument
from app.services.embeddings import EmbeddingService, hashing_embedding
from app.services.retrieval import RetrievalService, chunk_text


def make_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'retrieval.db'}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def configure_hashing():
    settings = get_settings()
    object.__setattr__(settings, "embedding_provider", "hashing")
    object.__setattr__(settings, "embedding_dimensions", 384)
    object.__setattr__(settings, "chunk_size_chars", 260)
    object.__setattr__(settings, "chunk_overlap_chars", 40)
    object.__setattr__(settings, "retrieval_keyword_only_max_chunks", 0)


def test_chunking_is_overlapping_and_stable():
    text = "A" * 500 + "\n\nPromise to Pay duplicate events." + "B" * 500
    chunks = chunk_text(text, size=300, overlap=50)
    assert len(chunks) >= 3
    assert chunks[0].start_char == 0
    assert chunks[1].start_char < chunks[0].end_char
    assert all(chunk.text for chunk in chunks)


def test_hashing_embedding_is_deterministic_and_normalized():
    a = hashing_embedding("duplicate PTP event", 384)
    b = hashing_embedding("duplicate PTP event", 384)
    assert a == b
    assert len(a) == 384
    norm = sum(v * v for v in a) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_index_and_hybrid_search_rank_relevant_document_first(tmp_path):
    configure_hashing()
    engine, factory = make_factory(tmp_path)
    with factory() as db:
        relevant = EvidenceDocument(
            source="LOCAL_DEMO", title="FSD-COL-104", document_type="TXT", version="1.0",
            content_hash="a" * 64, extracted_text=("Promise-to-Pay event processing. Duplicate PTP events must be handled idempotently. " * 10),
            char_count=900, parse_status="PARSED", metadata_json={}, index_status="PENDING",
        )
        irrelevant = EvidenceDocument(
            source="LOCAL_DEMO", title="Customer Onboarding", document_type="TXT", version="2.0",
            content_hash="b" * 64, extracted_text=("Customer identity verification, address capture and onboarding workflow. " * 10),
            char_count=700, parse_status="PARSED", metadata_json={}, index_status="PENDING",
        )
        db.add_all([relevant, irrelevant]); db.commit()
        service = RetrievalService()
        service.index_document(db, relevant)
        service.index_document(db, irrelevant)
        response = service.search(db, query="duplicate Promise-to-Pay event handling", top_k=5)
        assert response["searched_chunks"] >= 2
        assert response["results"][0]["document_title"] == "FSD-COL-104"
        assert response["results"][0]["keyword_score"] > 0
        assert response["results"][0]["semantic_score"] > 0
        assert response["embedding"]["degraded"] is True
        assert db.query(DocumentChunk).count() >= 2
    engine.dispose()
