from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.domain import get_domain_db
from app.core.config import get_settings
from app.db.base import Base
from app.main import app


@pytest.fixture
def client(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'issues.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_domain_db] = override_db
    object.__setattr__(get_settings(), "document_storage_path", str(tmp_path / "uploads"))
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_issue_capsule_create_list_detail(client: TestClient):
    bank = client.post("/api/v1/domain/clients", json={"name": "Atlas Bank", "client_type": "BANK"}).json()
    created = client.post(
        "/api/v1/issues",
        json={
            "external_ticket_id": "SUP-2317",
            "client_id": bank["id"],
            "title": "Duplicate Promise-to-Pay event changes collection state",
            "description": "Atlas Bank reports the same PTP event can be received twice and produce an incorrect collection state.",
            "issue_type": "BUG",
            "severity": "HIGH",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["client_name"] == "Atlas Bank"
    assert body["external_ticket_id"] == "SUP-2317"
    assert body["issue_type"] == "BUG"
    assert body["severity"] == "HIGH"
    assert body["status"] == "OPEN"
    assert body["attachment_count"] == 0

    listed = client.get("/api/v1/issues")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == body["id"]

    detail = client.get(f"/api/v1/issues/{body['id']}")
    assert detail.status_code == 200
    assert detail.json()["attachments"] == []


def test_issue_attachment_is_real_evidence_link(client: TestClient):
    bank = client.post("/api/v1/domain/clients", json={"name": "Meridian Bank", "client_type": "BANK"}).json()
    issue = client.post(
        "/api/v1/issues",
        json={
            "client_id": bank["id"],
            "title": "PTP processing investigation",
            "description": "Client reported a delivery issue and supplied an implementation note for review.",
            "issue_type": "INCIDENT",
            "severity": "MEDIUM",
        },
    ).json()

    uploaded = client.post(
        "/api/v1/documents",
        data={"source": "ISSUE_ATTACHMENT", "issue_id": issue["id"], "title": "Ticket evidence"},
        files={"file": ("support-note.txt", b"Duplicate PTP event observed in production trace.", "text/plain")},
    )
    assert uploaded.status_code == 201, uploaded.text

    detail = client.get(f"/api/v1/issues/{issue['id']}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["attachment_count"] == 1
    assert payload["attachments"][0]["document_id"] == uploaded.json()["id"]
    assert payload["attachments"][0]["original_filename"] == "support-note.txt"


def test_same_document_can_link_to_second_issue_without_duplicate_evidence(client: TestClient):
    bank = client.post("/api/v1/domain/clients", json={"name": "Nova Finance", "client_type": "FINANCIAL_INSTITUTION"}).json()
    issue1 = client.post("/api/v1/issues", json={"client_id": bank["id"], "title": "First issue", "description": "First issue has enough descriptive content."}).json()
    issue2 = client.post("/api/v1/issues", json={"client_id": bank["id"], "title": "Second issue", "description": "Second issue has enough descriptive content."}).json()
    file_bytes = b"Shared functional evidence for PTP expiry handling."

    first = client.post(
        "/api/v1/documents",
        data={"source": "ISSUE_ATTACHMENT", "issue_id": issue1["id"]},
        files={"file": ("shared.txt", file_bytes, "text/plain")},
    )
    second = client.post(
        "/api/v1/documents",
        data={"source": "ISSUE_ATTACHMENT", "issue_id": issue2["id"]},
        files={"file": ("shared-copy.txt", file_bytes, "text/plain")},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert client.get(f"/api/v1/issues/{issue2['id']}").json()["attachment_count"] == 1


def test_invalid_client_is_rejected(client: TestClient):
    response = client.post(
        "/api/v1/issues",
        json={"client_id": "missing", "title": "Invalid client issue", "description": "Description is long enough to validate."},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "CLIENT_NOT_FOUND"
