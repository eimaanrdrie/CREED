from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.api.domain import get_domain_db
from app.db.base import Base
from app.domain.models import (
    AdoptionReceipt,
    AgentRun,
    Client,
    DeliveryMethod,
    DependencyEdge,
    EvidenceDocument,
    HumanAuthority,
    Implementation,
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
    engine = create_engine(f"sqlite:///{tmp_path / 'r94_m08.db'}", connect_args={"check_same_thread": False})
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


def _seed(factory, suffix: str = "A"):
    with factory() as db:
        product = Product(name=f"Collections {suffix}", description="Collections", active=True)
        db.add(product); db.flush()
        module = Module(product_id=product.id, name="Promise-to-Pay", description="PTP", active=True)
        db.add(module); db.flush()
        method = DeliveryMethod(module_id=module.id, name="PTP Event Handling", description="Reusable event method")
        db.add(method); db.flush()
        source = MethodVersion(method_id=method.id, version="PTP-EVENT-v1", status="APPROVED", summary="Approved baseline")
        proposed = MethodVersion(method_id=method.id, version="PTP-EVENT-v2", status="PROPOSED", summary="Idempotent retry control")
        db.add_all([source, proposed]); db.flush()

        evidence = EvidenceDocument(
            source="LOCAL_REPOSITORY", title=f"CFG-PTP-{suffix}", document_type="CONFIG", version="1.0",
            content_hash=f"m08-evidence-{suffix}", extracted_text="Persisted replay evidence", char_count=25,
            parse_status="PARSED", index_status="INDEXED", metadata_json={}, chunk_count=1, embedding_degraded=False,
        )
        db.add(evidence); db.flush()

        implementations = []
        for client_name, impl_name in [
            ("Atlas Bank", "Atlas PTP Implementation"),
            ("Meridian Bank", "Meridian PTP Implementation"),
            ("Nova Finance", "Nova PTP Implementation"),
        ]:
            client = Client(name=f"{client_name} {suffix}", client_type="BANK" if "Finance" not in client_name else "FINANCIAL_INSTITUTION")
            db.add(client); db.flush()
            impl = Implementation(
                client_id=client.id, product_id=product.id, module_id=module.id,
                name=impl_name, release_version="R1", status="ACTIVE",
            )
            db.add(impl); db.flush()
            db.add(DependencyEdge(
                source_type="Implementation", source_id=impl.id,
                target_type="MethodVersion", target_id=source.id,
                relationship="USES_METHOD_VERSION", confidence=1.0,
                evidence_document_id=evidence.id,
            ))
            implementations.append(impl)

        issue = SupportIssue(
            client_id=None, external_ticket_id=f"SUP-M08-{suffix}", title="Retry replay",
            description="Replay issue", issue_type="BUG", severity="HIGH", status="OPEN",
        )
        db.add(issue); db.flush()
        run = AgentRun(graph_run_id=f"CREED-R94-M08-{suffix}", issue_id=issue.id, status="COMPLETED")
        db.add(run); db.flush()
        proposal = LearningProposal(
            source_issue_id=issue.id, proposed_method_version_id=proposed.id, status="PROPOSED",
            summary="Require idempotency validation before applying a Promise-to-Pay state mutation.",
            supporting_evidence_refs=[evidence.id],
        )
        db.add(proposal); db.flush()
        db.add(LearningProposalDetail(
            learning_id=proposal.id, agent_run_id=run.id, source_method_version_id=source.id,
            title="Idempotent Promise-to-Pay event handling", correction_input="Require idempotency before mutation.",
            applicability="Promise-to-Pay handlers receiving retries.", guardrails_json=["Use a stable idempotency key."],
            validation_steps_json=["Replay the same key and confirm one transition."], qwen_run_id=f"QWEN-M08-{suffix}",
            configured_model="qwen3.5:9b", actual_model="qwen3.5:9b", model_output_json={},
        ))
        principal=f"learning-{suffix.lower()}@creed.local"
        db.add(HumanAuthority(
            principal=principal, display_name="Learning Approver", role_title="Transformation Assurance Lead",
            active=True, can_submit_human_decision=False, can_approve_learning=True, can_authorize_recall=False,
        ))
        db.commit()
        return {
            "proposal_id": proposal.id,
            "source_id": source.id,
            "proposed_id": proposed.id,
            "implementation_ids": [item.id for item in implementations],
            "principal": principal,
        }


def _approve(http, proposal_id, scope, principal):
    return http.post(
        f"/api/v1/learning-proposals/{proposal_id}/decision",
        headers={"X-CREED-Principal": principal},
        json={
            "reviewer": principal,
            "decision": "APPROVE_LEARNING",
            "reason": "Evidence supports controlled adoption within the stated boundary.",
            "adoption_scope": scope,
        },
    )


def test_current_registered_scope_is_canonicalized_and_signed(context):
    http, factory = context
    seeded = _seed(factory, "A")
    response = _approve(http, seeded["proposal_id"], {"mode": "CURRENT_REGISTERED_IMPLEMENTATIONS", "implementation_ids": []}, seeded["principal"])
    assert response.status_code == 200, response.text
    receipt = response.json()["receipt"]
    scope = receipt["adoption_scope"]
    assert scope["scope_version"] == "1.0"
    assert scope["mode"] == "CURRENT_REGISTERED_IMPLEMENTATIONS"
    assert set(scope["implementation_ids"]) == set(seeded["implementation_ids"])
    assert len(scope["implementations"]) == 3
    assert scope["registered_adopter_count"] == 3
    assert scope["automatic_deployment_change"] is False
    assert scope["method"]["name"] == "PTP Event Handling"
    assert scope["source_method_version"]["version"] == "PTP-EVENT-v1"
    assert scope["adopted_method_version"]["version"] == "PTP-EVENT-v2"
    assert receipt["payload"]["adoption_scope"] == scope
    assert receipt["receipt_version"] == "1.1"
    assert receipt["integrity"] == "VALID"
    assert "3 currently registered" in receipt["attestation"]

    verified = http.get(f"/api/v1/adoption-receipts/{receipt['id']}/verify")
    assert verified.status_code == 200
    assert verified.json()["valid"] is True


def test_selected_scope_accepts_only_registered_abom_adopters(context):
    http, factory = context
    seeded = _seed(factory, "B")
    selected = seeded["implementation_ids"][:2]
    response = _approve(http, seeded["proposal_id"], {"mode": "SELECTED_IMPLEMENTATIONS", "implementation_ids": selected}, seeded["principal"])
    assert response.status_code == 200, response.text
    scope = response.json()["receipt"]["adoption_scope"]
    assert scope["mode"] == "SELECTED_IMPLEMENTATIONS"
    assert set(scope["implementation_ids"]) == set(selected)
    assert len(scope["implementations"]) == 2


def test_selected_scope_rejects_non_registered_implementation_and_does_not_adopt(context):
    http, factory = context
    seeded = _seed(factory, "C")
    response = _approve(http, seeded["proposal_id"], {"mode": "SELECTED_IMPLEMENTATIONS", "implementation_ids": ["not-an-abom-adopter"]}, seeded["principal"])
    assert response.status_code == 422
    assert response.json()["detail"] == "ADOPTION_SCOPE_IMPLEMENTATION_NOT_REGISTERED"
    with factory() as db:
        assert db.get(LearningProposal, seeded["proposal_id"]).status == "PROPOSED"
        assert db.get(MethodVersion, seeded["proposed_id"]).status == "PROPOSED"
        assert db.scalar(select(AdoptionReceipt).where(AdoptionReceipt.learning_id == seeded["proposal_id"])) is None


def test_approval_requires_explicit_scope_but_rejection_does_not(context):
    http, factory = context
    seeded = _seed(factory, "D")
    no_scope = _approve(http, seeded["proposal_id"], None, seeded["principal"])
    assert no_scope.status_code == 422
    assert no_scope.json()["detail"] == "ADOPTION_SCOPE_REQUIRED"

    seeded2 = _seed(factory, "E")
    rejected = http.post(
        f"/api/v1/learning-proposals/{seeded2['proposal_id']}/decision",
        headers={"X-CREED-Principal": seeded2["principal"]},
        json={
            "reviewer": seeded2["principal"],
            "decision": "REJECT_LEARNING",
            "reason": "Do not adopt this proposal.",
        },
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["learning"]["status"] == "REJECTED"
    assert rejected.json()["receipt"] is None
