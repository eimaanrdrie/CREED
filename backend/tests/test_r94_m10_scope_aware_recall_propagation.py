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
    AgentStep,
    Client,
    DeliveryMethod,
    DependencyEdge,
    EvidenceDocument,
    HumanAuthority,
    Implementation,
    Investigation,
    IssueEvidenceLink,
    LearningProposal,
    LearningProposalDetail,
    MethodVersion,
    Module,
    Product,
    RecallCase,
    RecallNotice,
    SupportIssue,
)
from app.main import app


@pytest.fixture
def context(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'r94_m10.db'}", connect_args={"check_same_thread": False})
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


def _seed(factory, suffix: str):
    with factory() as db:
        product = Product(name=f"Collections {suffix}", active=True)
        db.add(product); db.flush()
        module = Module(product_id=product.id, name="Promise-to-Pay", active=True)
        db.add(module); db.flush()
        method = DeliveryMethod(module_id=module.id, name="PTP Event Handling")
        db.add(method); db.flush()
        v1 = MethodVersion(method_id=method.id, version="PTP-EVENT-v1", status="APPROVED", summary="Baseline")
        v2 = MethodVersion(method_id=method.id, version="PTP-EVENT-v2", status="PROPOSED", summary="Replay-safe")
        db.add_all([v1, v2]); db.flush()

        doc = EvidenceDocument(
            source="LOCAL_REPOSITORY", title=f"CFG-PTP-{suffix}", document_type="CONFIG", version="1.0",
            content_hash=f"m10-{suffix}-cfg", extracted_text="duplicate_suppression = false", char_count=29,
            parse_status="PARSED", index_status="INDEXED", metadata_json={}, chunk_count=1, embedding_degraded=False,
        )
        db.add(doc); db.flush()

        impls = []
        for client_name in ["Atlas Bank", "Meridian Bank", "Nova Finance"]:
            client = Client(name=f"{client_name} {suffix}", client_type="BANK")
            db.add(client); db.flush()
            impl = Implementation(
                client_id=client.id, product_id=product.id, module_id=module.id,
                name=f"{client_name.split()[0]} PTP Implementation", release_version="R1", status="ACTIVE",
            )
            db.add(impl); db.flush()
            db.add(DependencyEdge(
                source_type="Implementation", source_id=impl.id, target_type="MethodVersion", target_id=v1.id,
                relationship="USES_METHOD_VERSION", confidence=1.0, evidence_document_id=doc.id,
            ))
            impls.append(impl)

        issue = SupportIssue(
            external_ticket_id=f"SUP-M10-{suffix}", title="Retry replay invalidates prior learning",
            description="New evidence shows the approved replay handling must be recalled.",
            issue_type="BUG", severity="HIGH", status="OPEN", client_id=impls[0].client_id,
        )
        db.add(issue); db.flush()
        db.add(IssueEvidenceLink(issue_id=issue.id, document_id=doc.id, link_type="ATTACHMENT"))

        run = AgentRun(graph_run_id=f"CREED-R94-M10-{suffix}", issue_id=issue.id, status="COMPLETED")
        db.add(run); db.flush()
        proposal = LearningProposal(
            source_issue_id=issue.id, proposed_method_version_id=v2.id, status="PROPOSED",
            summary="Require idempotency before state mutation.", supporting_evidence_refs=[doc.id],
        )
        db.add(proposal); db.flush()
        db.add(LearningProposalDetail(
            learning_id=proposal.id, agent_run_id=run.id, source_method_version_id=v1.id,
            title="Replay-safe PTP", correction_input="Require idempotency before mutation.",
            applicability="PTP event handlers", guardrails_json=["Stable event key"],
            validation_steps_json=["Replay same key"], qwen_run_id=f"QWEN-M10-{suffix}",
            configured_model="qwen3.5:9b", actual_model="qwen3.5:9b", model_output_json={},
        ))

        learning_principal = f"learning-{suffix.lower()}@creed.local"
        recall_principal = f"recall-{suffix.lower()}@creed.local"
        db.add_all([
            HumanAuthority(
                principal=learning_principal, display_name="Learning Approver", role_title="Assurance Lead", active=True,
                can_submit_human_decision=False, can_approve_learning=True, can_authorize_recall=False,
            ),
            HumanAuthority(
                principal=recall_principal, display_name="Recall Authority", role_title="Risk Lead", active=True,
                can_submit_human_decision=False, can_approve_learning=False, can_authorize_recall=True,
            ),
        ])
        db.commit()
        return {
            "product_id": product.id,
            "module_id": module.id,
            "method_id": method.id,
            "v1": v1.id,
            "v2": v2.id,
            "doc": doc.id,
            "proposal": proposal.id,
            "learning_principal": learning_principal,
            "recall_principal": recall_principal,
            "impls": [item.id for item in impls],
            "issue": issue.id,
        }


def _approve(http: TestClient, seeded: dict, mode: str, ids=None):
    response = http.post(
        f"/api/v1/learning-proposals/{seeded['proposal']}/decision",
        headers={"X-CREED-Principal": seeded["learning_principal"]},
        json={
            "reviewer": seeded["learning_principal"],
            "decision": "APPROVE_LEARNING",
            "reason": "Approve reusable learning within the stated boundary.",
            "adoption_scope": {"mode": mode, "implementation_ids": ids or []},
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _direct_v2_edge(factory, seeded: dict, implementation_id: str):
    with factory() as db:
        edge = DependencyEdge(
            source_type="Implementation", source_id=implementation_id,
            target_type="MethodVersion", target_id=seeded["v2"],
            relationship="USES_METHOD_VERSION", confidence=1.0, evidence_document_id=seeded["doc"],
        )
        db.add(edge); db.commit()
        return edge.id


def _revoke(http: TestClient, seeded: dict, version_id: str | None = None):
    return http.post(
        f"/api/v1/method-versions/{version_id or seeded['v2']}/revoke",
        headers={"X-CREED-Principal": seeded["recall_principal"]},
        json={
            "source_issue_id": seeded["issue"],
            "reviewer": seeded["recall_principal"],
            "reason": "New evidence invalidates the approved replay-handling knowledge.",
        },
    )


def test_selected_scope_routes_only_intersection_and_creates_run_scoped_review_obligations(context):
    http, factory = context
    seeded = _seed(factory, "SEL")
    approved = _approve(http, seeded, "SELECTED_IMPLEMENTATIONS", seeded["impls"][:1])
    _direct_v2_edge(factory, seeded, seeded["impls"][0])
    _direct_v2_edge(factory, seeded, seeded["impls"][1])  # simulate legacy/direct-DB out-of-scope edge

    versions = http.get("/api/v1/knowledge-graph/method-versions").json()
    selected = next(item for item in versions if item["id"] == seeded["v2"])
    assert selected["adoption_policy"]["scope_mode"] == "SELECTED_IMPLEMENTATIONS"
    assert selected["adoption_policy"]["receipt_integrity"] == "VALID"

    response = _revoke(http, seeded)
    assert response.status_code == 200, response.text
    recall = response.json()
    assert recall["integrity"] == "VALID"
    assert recall["notice_version"] == "1.1"
    assert [case["implementation_id"] for case in recall["cases"]] == [seeded["impls"][0]]
    assert recall["routing_scope"]["enforced"] is True
    assert recall["routing_scope"]["mode"] == "SELECTED_IMPLEMENTATIONS"
    assert recall["routing_scope"]["adoption_receipt_id"] == approved["receipt"]["id"]
    assert recall["routing_scope"]["explicit_dependency_count"] == 2
    assert recall["routing_scope"]["routed_count"] == 1
    assert recall["routing_scope"]["blocked_count"] == 1
    assert recall["routing_scope"]["blocked_implementations"][0]["implementation_id"] == seeded["impls"][1]
    assert recall["routing_scope"]["blocked_implementations"][0]["reason"] == "ADOPTION_SCOPE_EXCLUDES_IMPLEMENTATION"

    with factory() as db:
        case = db.scalar(select(RecallCase).where(RecallCase.recall_notice_id == recall["id"]))
        investigation = db.get(Investigation, case.investigation_id)
        run = db.get(AgentRun, investigation.agent_run_id)
        step = db.scalar(select(AgentStep).where(AgentStep.agent_run_id == run.id, AgentStep.agent_name == "recall_agent"))
        assert run.id == recall["recall_run_id"]
        assert investigation.agent_run_id == recall["recall_run_id"]
        assert investigation.implementation_id == seeded["impls"][0]
        assert case.status == "QUEUED"
        assert step.metadata_json["scope_enforced"] is True
        assert step.metadata_json["blocked_count"] == 1


def test_tampered_adoption_receipt_blocks_recall_before_revocation_mutation(context):
    http, factory = context
    seeded = _seed(factory, "TAMPER")
    approved = _approve(http, seeded, "SELECTED_IMPLEMENTATIONS", seeded["impls"][:1])
    _direct_v2_edge(factory, seeded, seeded["impls"][0])

    with factory() as db:
        detail = db.scalar(select(AdoptionReceiptDetail).where(AdoptionReceiptDetail.receipt_id == approved["receipt"]["id"]))
        payload = dict(detail.receipt_payload_json)
        payload["approval_reason"] = "tampered after signing"
        detail.receipt_payload_json = payload
        db.commit()

    response = _revoke(http, seeded)
    assert response.status_code == 422
    assert response.json()["detail"] == "ADOPTION_RECEIPT_INTEGRITY_INVALID"

    with factory() as db:
        assert db.get(MethodVersion, seeded["v2"]).status == "APPROVED"
        assert db.get(LearningProposal, seeded["proposal"]).status == "APPROVED"
        assert db.scalar(select(RecallNotice).where(RecallNotice.revoked_version_id == seeded["v2"])) is None


def test_method_catalog_scope_routes_future_explicit_same_module_adopter(context):
    http, factory = context
    seeded = _seed(factory, "CAT")
    _approve(http, seeded, "METHOD_CATALOG")
    _direct_v2_edge(factory, seeded, seeded["impls"][0])

    with factory() as db:
        client = Client(name="Future Bank CAT", client_type="BANK")
        db.add(client); db.flush()
        future = Implementation(
            client_id=client.id, product_id=seeded["product_id"], module_id=seeded["module_id"],
            name="Future PTP CAT", release_version="R2", status="ACTIVE",
        )
        db.add(future); db.flush()
        future_id = future.id
        db.commit()
    _direct_v2_edge(factory, seeded, future_id)

    response = _revoke(http, seeded)
    assert response.status_code == 200, response.text
    recall = response.json()
    assert recall["routing_scope"]["mode"] == "METHOD_CATALOG"
    assert recall["routing_scope"]["blocked_count"] == 0
    assert set(case["implementation_id"] for case in recall["cases"]) == {seeded["impls"][0], future_id}


def test_baseline_recall_preserves_explicit_abom_behavior_without_learning_scope(context):
    http, factory = context
    seeded = _seed(factory, "BASE")

    response = _revoke(http, seeded, seeded["v1"])
    assert response.status_code == 200, response.text
    recall = response.json()
    assert recall["routing_scope"]["enforced"] is False
    assert recall["routing_scope"]["basis"] == "CURRENT_EXPLICIT_A_BOM"
    assert recall["routing_scope"]["blocked_count"] == 0
    assert set(case["implementation_id"] for case in recall["cases"]) == set(seeded["impls"])


def test_recall_accepts_direct_evidence_repository_selection(context):
    http, factory = context
    seeded = _seed(factory, "DIRECT")
    _approve(http, seeded, "SELECTED_IMPLEMENTATIONS", seeded["impls"][:1])
    _direct_v2_edge(factory, seeded, seeded["impls"][0])

    with factory() as db:
        direct_doc = EvidenceDocument(
            source="LOCAL_REPOSITORY", title="TEST-PTP-DIRECT-RECALL", document_type="TEST", version="2.0",
            content_hash="m10-direct-recall-evidence", extracted_text="Replay regression invalidates v2.", char_count=31,
            parse_status="PARSED", index_status="INDEXED", metadata_json={}, chunk_count=1, embedding_degraded=False,
        )
        db.add(direct_doc); db.commit(); direct_doc_id = direct_doc.id

    response = http.post(
        f"/api/v1/method-versions/{seeded['v2']}/revoke",
        headers={"X-CREED-Principal": seeded["recall_principal"]},
        json={
            "source_issue_id": seeded["issue"],
            "evidence_document_ids": [direct_doc_id],
            "reviewer": seeded["recall_principal"],
            "reason": "Repository test evidence directly invalidates the approved replay-handling knowledge.",
        },
    )
    assert response.status_code == 200, response.text
    recall = response.json()
    assert recall["integrity"] == "VALID"
    assert [item["id"] for item in recall["evidence"]] == [direct_doc_id]
    assert recall["evidence"][0]["title"] == "TEST-PTP-DIRECT-RECALL"
    assert recall["cases"][0]["implementation_id"] == seeded["impls"][0]
