from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.api.domain import get_domain_db
from app.db.base import Base
from app.domain.models import (
    AdoptionReceiptDetail,
    AgentRun,
    Client,
    DeliveryMethod,
    EvidenceDocument,
    HumanAuthority,
    LearningProposal,
    LearningProposalDetail,
    MethodVersion,
    Module,
    Product,
    SupportIssue,
)
from app.main import app


@pytest.fixture
def context(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'r94_m07.db'}", connect_args={"check_same_thread": False})
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


def _seed_proposal(factory, *, suffix: str = "A"):
    with factory() as db:
        product = Product(name=f"Collections {suffix}", description="Collections", active=True)
        db.add(product); db.flush()
        module = Module(product_id=product.id, name="Promise-to-Pay", description="PTP", active=True)
        db.add(module); db.flush()
        method = DeliveryMethod(module_id=module.id, name="PTP Event Handling", description="Reusable event method")
        db.add(method); db.flush()
        source = MethodVersion(method_id=method.id, version="PTP-EVENT-v1", status="APPROVED", summary="Approved baseline")
        proposed = MethodVersion(method_id=method.id, version="PTP-EVENT-v2", status="PROPOSED", summary="Require idempotency before mutation")
        db.add_all([source, proposed]); db.flush()
        client = Client(name=f"Atlas Bank {suffix}", client_type="BANK")
        db.add(client); db.flush()
        issue = SupportIssue(client_id=client.id, external_ticket_id=f"SUP-M07-{suffix}", title="Retry replay", description="Replay issue", issue_type="BUG", severity="HIGH", status="OPEN")
        db.add(issue); db.flush()
        run = AgentRun(graph_run_id=f"CREED-R94-M07-{suffix}", issue_id=issue.id, status="COMPLETED")
        db.add(run); db.flush()
        evidence = EvidenceDocument(
            source="LOCAL_REPOSITORY", title=f"CFG-ATLAS-PTP-{suffix}", document_type="CONFIG", version="1.0",
            content_hash=f"m07-evidence-{suffix}", extracted_text="Persisted replay evidence", char_count=25,
            parse_status="PARSED", index_status="INDEXED", metadata_json={}, chunk_count=1, embedding_degraded=False,
        )
        db.add(evidence); db.flush()
        learning = LearningProposal(
            source_issue_id=issue.id,
            proposed_method_version_id=proposed.id,
            status="PROPOSED",
            summary="Require idempotency validation before applying a Promise-to-Pay state mutation.",
            supporting_evidence_refs=[evidence.id],
        )
        db.add(learning); db.flush()
        db.add(LearningProposalDetail(
            learning_id=learning.id,
            agent_run_id=run.id,
            source_method_version_id=source.id,
            title="Idempotent Promise-to-Pay event handling",
            correction_input="Require idempotency before mutation.",
            applicability="Promise-to-Pay handlers receiving retries.",
            guardrails_json=["Use a stable idempotency key."],
            validation_steps_json=["Replay the same key and confirm one transition."],
            qwen_run_id=f"QWEN-M07-{suffix}",
            configured_model="qwen3.5:9b",
            actual_model="qwen3.5:9b",
            model_output_json={},
        ))
        db.add(HumanAuthority(
            principal="learning@creed.local", display_name="Learning Approver", role_title="Transformation Assurance Lead",
            active=True, can_submit_human_decision=False, can_approve_learning=True, can_authorize_recall=False,
        ))
        db.commit()
        return learning.id, run.graph_run_id, proposed.id


def test_approved_learning_embeds_signed_receipt_and_survives_refresh(context):
    http, factory = context
    proposal_id, graph_run_id, proposed_id = _seed_proposal(factory)
    response = http.post(
        f"/api/v1/learning-proposals/{proposal_id}/decision",
        headers={"X-CREED-Principal": "learning@creed.local"},
        json={
            "reviewer": "learning@creed.local",
            "decision": "APPROVE_LEARNING",
            "reason": "Evidence and validation steps support controlled adoption.",
            "adoption_scope": {"mode": "METHOD_CATALOG", "implementation_ids": []},
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    receipt = payload["receipt"]
    embedded = payload["learning"]["adoption_receipt"]
    assert payload["learning"]["status"] == "APPROVED"
    assert payload["learning"]["proposed_method_version"]["status"] == "APPROVED"
    assert receipt is not None
    assert embedded is not None
    assert embedded["id"] == receipt["id"]
    assert embedded["integrity"] == "VALID"
    assert embedded["hash_algorithm"] == "SHA-256"
    assert embedded["approval_reason"] == "Evidence and validation steps support controlled adoption."
    assert len(embedded["evidence"]) == 1
    assert len(embedded["content_hash"]) == 64

    refreshed = http.get(f"/api/v1/analysis-runs/{graph_run_id}/learning-proposal")
    assert refreshed.status_code == 200, refreshed.text
    refreshed_receipt = refreshed.json()["adoption_receipt"]
    assert refreshed_receipt["id"] == receipt["id"]
    assert refreshed_receipt["integrity"] == "VALID"

    verified = http.get(f"/api/v1/adoption-receipts/{receipt['id']}/verify")
    assert verified.status_code == 200
    assert verified.json() == {
        "valid": True,
        "status": "VALID",
        "hash_algorithm": "SHA-256",
        "content_hash": receipt["content_hash"],
    }

    with factory() as db:
        detail = db.scalar(select(AdoptionReceiptDetail).where(AdoptionReceiptDetail.receipt_id == receipt["id"]))
        assert detail is not None
        detail.receipt_payload_json = {**detail.receipt_payload_json, "approval_reason": "tampered after signing"}
        db.commit()

    tampered = http.get(f"/api/v1/adoption-receipts/{receipt['id']}/verify")
    assert tampered.status_code == 200
    assert tampered.json()["valid"] is False
    assert tampered.json()["status"] == "INVALID"

    with factory() as db:
        assert db.get(MethodVersion, proposed_id).status == "APPROVED"


def test_rejected_learning_has_no_adoption_receipt(context):
    http, _factory = context
    proposal_id, graph_run_id, _ = _seed_proposal(_factory, suffix="B")
    response = http.post(
        f"/api/v1/learning-proposals/{proposal_id}/decision",
        headers={"X-CREED-Principal": "learning@creed.local"},
        json={
            "reviewer": "learning@creed.local",
            "decision": "REJECT_LEARNING",
            "reason": "Validation evidence is not sufficient for reusable adoption.",
            "adoption_scope": {"mode": "METHOD_CATALOG", "implementation_ids": []},
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["receipt"] is None
    assert response.json()["learning"]["status"] == "REJECTED"
    assert response.json()["learning"]["adoption_receipt"] is None

    refreshed = http.get(f"/api/v1/analysis-runs/{graph_run_id}/learning-proposal")
    assert refreshed.status_code == 200
    assert refreshed.json()["status"] == "REJECTED"
    assert refreshed.json()["adoption_receipt"] is None
