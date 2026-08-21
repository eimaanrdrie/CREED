from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.domain import get_domain_db
from app.core.config import get_settings
from app.db.base import Base
from app.main import app


def make_client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'search.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    def override_db():
        with factory() as session:
            yield session
    app.dependency_overrides[get_domain_db] = override_db
    settings = get_settings()
    object.__setattr__(settings, "document_storage_path", str(tmp_path / "uploads"))
    object.__setattr__(settings, "embedding_provider", "hashing")
    object.__setattr__(settings, "embedding_dimensions", 384)
    return TestClient(app), engine


def test_upload_auto_indexes_and_search_returns_citation(tmp_path):
    client, engine = make_client(tmp_path)
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("fsd.txt", b"Promise-to-Pay duplicate event handling uses an idempotency key to prevent repeated state transitions.", "text/plain")},
        data={"title": "FSD-COL-104", "version": "1.0"},
    )
    assert upload.status_code == 201, upload.text
    body = upload.json()
    assert body["index_status"] == "INDEXED_DEGRADED"
    assert body["chunk_count"] >= 1

    search = client.post("/api/v1/retrieval/search", json={"query": "duplicate PTP state transition", "top_k": 5})
    assert search.status_code == 200, search.text
    payload = search.json()
    assert payload["results"]
    assert payload["results"][0]["document_title"] == "FSD-COL-104"
    assert "chunk" in payload["results"][0]["citation"]

    status = client.get("/api/v1/retrieval/status")
    assert status.status_code == 200
    assert status.json()["chunks"] >= 1
    app.dependency_overrides.clear()
    engine.dispose()
