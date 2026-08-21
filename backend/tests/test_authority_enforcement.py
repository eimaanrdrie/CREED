from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.domain import get_domain_db
from app.db.base import Base
from app.main import app
from app.services.authority_enforcement import AuthorityEnforcementError, require_human_authority


@pytest.fixture
def client(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'authority.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_domain_db] = override_db
    try:
        yield TestClient(app), factory
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def _authority(client: TestClient, principal: str, **overrides):
    payload = {
        "principal": principal,
        "display_name": overrides.pop("display_name", principal.split("@")[0].replace(".", " ").title()),
        "role_title": overrides.pop("role_title", "Assurance Reviewer"),
        "active": overrides.pop("active", True),
        "can_submit_human_decision": overrides.pop("can_submit_human_decision", False),
        "can_approve_learning": overrides.pop("can_approve_learning", False),
        "can_authorize_recall": overrides.pop("can_authorize_recall", False),
    }
    payload.update(overrides)
    response = client.post("/api/v1/domain/authorities", json=payload)
    assert response.status_code == 201
    return response.json()


def test_service_enforces_active_registered_capability(client):
    http, factory = client
    _authority(http, "decision@creed.local", can_submit_human_decision=True)
    _authority(http, "inactive@creed.local", active=False, can_submit_human_decision=True)
    _authority(http, "wrong@creed.local", can_approve_learning=True)

    with factory() as db:
        authority = require_human_authority(
            db,
            principal="decision@creed.local",
            capability="can_submit_human_decision",
            claimed_reviewer="decision@creed.local",
        )
        assert authority.principal == "decision@creed.local"

        with pytest.raises(AuthorityEnforcementError, match="AUTHORITY_PRINCIPAL_REQUIRED"):
            require_human_authority(db, principal=None, capability="can_submit_human_decision")
        with pytest.raises(AuthorityEnforcementError, match="AUTHORITY_PRINCIPAL_NOT_REGISTERED"):
            require_human_authority(db, principal="missing@creed.local", capability="can_submit_human_decision")
        with pytest.raises(AuthorityEnforcementError, match="AUTHORITY_PRINCIPAL_INACTIVE"):
            require_human_authority(db, principal="inactive@creed.local", capability="can_submit_human_decision")
        with pytest.raises(AuthorityEnforcementError, match="HUMAN_DECISION_AUTHORITY_REQUIRED"):
            require_human_authority(db, principal="wrong@creed.local", capability="can_submit_human_decision")
        with pytest.raises(AuthorityEnforcementError, match="AUTHORITY_PRINCIPAL_MISMATCH"):
            require_human_authority(
                db,
                principal="decision@creed.local",
                capability="can_submit_human_decision",
                claimed_reviewer="someone-else@creed.local",
            )


def test_governed_endpoints_reject_missing_or_wrong_authority_before_business_action(client):
    http, _ = client
    decision = _authority(http, "decision@creed.local", can_submit_human_decision=True)
    learning = _authority(http, "learning@creed.local", can_approve_learning=True)
    recall = _authority(http, "recall@creed.local", can_authorize_recall=True)

    review_payload = {"reviewer": decision["principal"], "decisions": []}
    response = http.post("/api/v1/analysis-runs/missing/human-review/resume", json=review_payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "AUTHORITY_PRINCIPAL_REQUIRED"

    response = http.post(
        "/api/v1/analysis-runs/missing/human-review/resume",
        json=review_payload,
        headers={"X-CREED-Principal": learning["principal"]},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "HUMAN_DECISION_AUTHORITY_REQUIRED"

    learning_payload = {
        "reviewer": learning["principal"],
        "decision": "APPROVE_LEARNING",
        "reason": "Evidence supports adoption.",
        "adoption_scope": {"mode": "METHOD_CATALOG", "implementation_ids": []},
    }
    response = http.post("/api/v1/learning-proposals/missing/decision", json=learning_payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "AUTHORITY_PRINCIPAL_REQUIRED"

    response = http.post(
        "/api/v1/learning-proposals/missing/decision",
        json=learning_payload,
        headers={"X-CREED-Principal": recall["principal"]},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "LEARNING_APPROVAL_AUTHORITY_REQUIRED"

    recall_payload = {
        "source_issue_id": "missing-issue",
        "reviewer": recall["principal"],
        "reason": "Approved method is no longer valid.",
    }
    response = http.post("/api/v1/method-versions/missing/revoke", json=recall_payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "AUTHORITY_PRINCIPAL_REQUIRED"

    response = http.post(
        "/api/v1/method-versions/missing/revoke",
        json=recall_payload,
        headers={"X-CREED-Principal": decision["principal"]},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "RECALL_AUTHORITY_REQUIRED"


def test_header_and_reviewer_identity_must_match(client):
    http, _ = client
    authority = _authority(http, "authority@creed.local", can_approve_learning=True)
    payload = {
        "reviewer": "other@creed.local",
        "decision": "REJECT_LEARNING",
        "reason": "Insufficient evidence.",
        "adoption_scope": {"mode": "METHOD_CATALOG", "implementation_ids": []},
    }
    response = http.post(
        "/api/v1/learning-proposals/missing/decision",
        json=payload,
        headers={"X-CREED-Principal": authority["principal"]},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "AUTHORITY_PRINCIPAL_MISMATCH"


def test_authorized_principal_reaches_governed_business_validation(client):
    http, _ = client
    decision = _authority(http, "decision-ok@creed.local", can_submit_human_decision=True)
    learning = _authority(http, "learning-ok@creed.local", can_approve_learning=True)
    recall = _authority(http, "recall-ok@creed.local", can_authorize_recall=True)

    response = http.post(
        "/api/v1/learning-proposals/missing/decision",
        json={
            "reviewer": learning["principal"],
            "decision": "REJECT_LEARNING",
            "reason": "Evidence does not support reuse.",
            "adoption_scope": {"mode": "METHOD_CATALOG", "implementation_ids": []},
        },
        headers={"X-CREED-Principal": learning["principal"]},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "LEARNING_PROPOSAL_NOT_FOUND"

    response = http.post(
        "/api/v1/method-versions/missing/revoke",
        json={
            "source_issue_id": "missing-issue",
            "reviewer": recall["principal"],
            "reason": "Method is no longer valid.",
        },
        headers={"X-CREED-Principal": recall["principal"]},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "ONLY_APPROVED_KNOWLEDGE_CAN_BE_REVOKED"

    response = http.post(
        "/api/v1/analysis-runs/missing/human-review/resume",
        json={"reviewer": decision["principal"], "decisions": []},
        headers={"X-CREED-Principal": decision["principal"]},
    )
    assert response.status_code in {404, 503}
    assert response.status_code != 403
