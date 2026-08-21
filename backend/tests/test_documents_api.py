from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.domain import get_domain_db
from app.core.config import get_settings
from app.db.base import Base
from app.main import app


def make_client(tmp_path: Path) -> TestClient:
    engine = create_engine(f"sqlite:///{tmp_path / 'documents.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_domain_db] = override_db
    settings = get_settings()
    object.__setattr__(settings, "document_storage_path", str(tmp_path / "uploads"))
    return TestClient(app)


def test_upload_list_detail_and_duplicate(tmp_path: Path):
    client = make_client(tmp_path)
    response = client.post(
        "/api/v1/documents",
        data={"source": "LOCAL_DEMO", "title": "FSD-COL-104", "version": "1.0"},
        files={"file": ("FSD-COL-104.txt", b"Promise-to-Pay event processing and duplicate event control.", "text/plain")},
    )
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["title"] == "FSD-COL-104"
    assert created["document_type"] == "TXT"
    assert created["parse_status"] == "PARSED"
    assert "duplicate event" in created["extracted_text"]
    assert created["char_count"] > 20

    listed = client.get("/api/v1/documents")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert "extracted_text" not in listed.json()[0]

    detail = client.get(f"/api/v1/documents/{created['id']}")
    assert detail.status_code == 200
    assert detail.json()["content_hash"] == created["content_hash"]

    duplicate = client.post(
        "/api/v1/documents",
        data={"source": "LOCAL_DEMO"},
        files={"file": ("copy.txt", b"Promise-to-Pay event processing and duplicate event control.", "text/plain")},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "DUPLICATE_DOCUMENT"
    app.dependency_overrides.clear()


def test_rejects_invalid_extension(tmp_path: Path):
    client = make_client(tmp_path)
    response = client.post(
        "/api/v1/documents",
        files={"file": ("payload.exe", b"not allowed", "application/octet-stream")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "UNSUPPORTED_FILE_TYPE"
    app.dependency_overrides.clear()


def test_original_source_returns_exact_hash_verified_bytes(tmp_path: Path):
    client = make_client(tmp_path)
    payload = b"# Original source\n\nduplicate_suppression = false\nSpacing  stays  exact.\n"
    response = client.post(
        "/api/v1/documents",
        data={"source": "LOCAL_DEMO", "title": "CFG-ORIGINAL-01", "version": "1.0"},
        files={"file": ("CFG-ORIGINAL-01.md", payload, "text/markdown")},
    )
    assert response.status_code == 201, response.text
    created = response.json()

    original = client.get(f"/api/v1/documents/{created['id']}/original")
    assert original.status_code == 200, original.text
    assert original.content == payload
    assert original.headers["x-creed-original-verified"] == "true"
    assert original.headers["x-creed-content-sha256"] == created["content_hash"]
    assert original.headers["cache-control"] == "no-store"
    assert "inline" in original.headers["content-disposition"].lower()
    app.dependency_overrides.clear()


def test_original_source_fails_closed_after_storage_tamper(tmp_path: Path):
    client = make_client(tmp_path)
    payload = b"governed original"
    response = client.post(
        "/api/v1/documents",
        data={"source": "LOCAL_DEMO", "title": "TAMPER-CHECK", "version": "1.0"},
        files={"file": ("TAMPER-CHECK.txt", payload, "text/plain")},
    )
    assert response.status_code == 201, response.text
    created = response.json()
    stored = tmp_path / "uploads" / created["id"] / "TAMPER-CHECK.txt"
    stored.write_bytes(b"tampered bytes")

    original = client.get(f"/api/v1/documents/{created['id']}/original")
    assert original.status_code == 409
    assert original.json()["detail"] == "ORIGINAL_FILE_HASH_MISMATCH"
    app.dependency_overrides.clear()


def test_synthetic_demo_original_rebases_stale_package_path():
    import hashlib
    from types import SimpleNamespace
    from app.api.documents import _verified_original_path

    demo_file = Path(__file__).resolve().parents[1] / "demo_data" / "FSD-COL-104.md"
    payload = demo_file.read_bytes()
    item = SimpleNamespace(
        storage_path="/stale/previous-build/backend/demo_data/FSD-COL-104.md",
        original_filename="FSD-COL-104.md",
        metadata_json={"dataset": "CREED-DEMO-1.1", "synthetic": True},
        content_hash=hashlib.sha256(payload).hexdigest(),
    )
    assert _verified_original_path(item) == demo_file.resolve()


def test_original_source_cors_exposes_verification_headers(tmp_path: Path):
    client = make_client(tmp_path)
    payload = b"exact source bytes"
    response = client.post(
        "/api/v1/documents",
        data={"source": "LOCAL_DEMO", "title": "CORS-ORIGINAL", "version": "1.0"},
        files={"file": ("CORS-ORIGINAL.txt", payload, "text/plain")},
    )
    document_id = response.json()["id"]
    original = client.get(
        f"/api/v1/documents/{document_id}/original",
        headers={"Origin": "http://localhost:3000"},
    )
    assert original.status_code == 200
    exposed = original.headers.get("access-control-expose-headers", "").lower()
    assert "x-creed-original-verified" in exposed
    assert "x-creed-content-sha256" in exposed
    app.dependency_overrides.clear()


def test_original_source_recovers_canonical_upload_after_stale_relative_path(tmp_path: Path):
    import hashlib
    from types import SimpleNamespace
    from app.api.documents import _verified_original_path

    settings = get_settings()
    original_storage = settings.document_storage_path
    try:
        object.__setattr__(settings, "document_storage_path", str(tmp_path / "uploads"))
        document_id = "restart-safe-document"
        filename = "TEST-ATLAS-PTP-R1.pdf"
        payload = b"%PDF-1.4\nrestart-safe-original-bytes\n%%EOF\n"
        canonical = tmp_path / "uploads" / document_id / filename
        canonical.parent.mkdir(parents=True)
        canonical.write_bytes(payload)
        item = SimpleNamespace(
            id=document_id,
            storage_path=f".data/documents/{document_id}/{filename}",
            original_filename=filename,
            metadata_json={"knowledge_mode": "LOCAL_DEMO"},
            content_hash=hashlib.sha256(payload).hexdigest(),
        )
        assert _verified_original_path(item) == canonical.resolve()
    finally:
        object.__setattr__(settings, "document_storage_path", original_storage)


def test_relative_document_storage_is_anchored_to_backend_root():
    settings = get_settings()
    original_storage = settings.document_storage_path
    try:
        object.__setattr__(settings, "document_storage_path", ".data/documents")
        backend_root = Path(__file__).resolve().parents[1]
        assert settings.document_storage_dir == (backend_root / ".data/documents").resolve()
    finally:
        object.__setattr__(settings, "document_storage_path", original_storage)
