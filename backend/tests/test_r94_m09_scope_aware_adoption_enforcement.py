from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.api.domain import get_domain_db
from app.db.base import Base
from app.domain.models import (
    AdoptionReceipt,
    AdoptionReceiptDetail,
    AgentRun,
    AnalysisEvidenceHit,
    Client,
    DeliveryMethod,
    DependencyEdge,
    DocumentChunk,
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
from app.services.advanced import score_blast_radius


@pytest.fixture
def context(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'r94_m09.db'}", connect_args={"check_same_thread": False})
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
            content_hash=f"m09-{suffix}-cfg", extracted_text="duplicate_suppression = false", char_count=29,
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
            external_ticket_id=f"SUP-M09-{suffix}", title="Retry replay", description="Retry replay issue",
            issue_type="BUG", severity="HIGH", status="OPEN", client_id=impls[0].client_id,
        )
        db.add(issue); db.flush()
        run = AgentRun(graph_run_id=f"CREED-R94-M09-{suffix}", issue_id=issue.id, status="COMPLETED")
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
            validation_steps_json=["Replay same key"], qwen_run_id=f"QWEN-M09-{suffix}",
            configured_model="qwen3.5:9b", actual_model="qwen3.5:9b", model_output_json={},
        ))
        principal = f"learning-{suffix.lower()}@creed.local"
        db.add(HumanAuthority(
            principal=principal, display_name="Learning Approver", role_title="Assurance Lead", active=True,
            can_submit_human_decision=False, can_approve_learning=True, can_authorize_recall=False,
        ))
        db.commit()
        return {
            "product_id": product.id,
            "module_id": module.id,
            "method_id": method.id,
            "v1": v1.id,
            "v2": v2.id,
            "doc": doc.id,
            "proposal": proposal.id,
            "principal": principal,
            "impls": [item.id for item in impls],
            "issue": issue.id,
        }


def _approve(http: TestClient, seeded: dict, mode: str, ids=None):
    return http.post(
        f"/api/v1/learning-proposals/{seeded['proposal']}/decision",
        headers={"X-CREED-Principal": seeded["principal"]},
        json={
            "reviewer": seeded["principal"],
            "decision": "APPROVE_LEARNING",
            "reason": "Approve reusable learning within the stated boundary.",
            "adoption_scope": {"mode": mode, "implementation_ids": ids or []},
        },
    )


def _dependency(http: TestClient, seeded: dict, implementation_id: str):
    return http.post("/api/v1/domain/dependencies", json={
        "implementation_id": implementation_id,
        "method_version_id": seeded["v2"],
        "evidence_document_id": seeded["doc"],
    })


def _new_impl(factory, seeded: dict, suffix: str) -> str:
    with factory() as db:
        client = Client(name=f"Future Bank {suffix}", client_type="BANK")
        db.add(client); db.flush()
        impl = Implementation(
            client_id=client.id, product_id=seeded["product_id"], module_id=seeded["module_id"],
            name=f"Future PTP {suffix}", release_version="R2", status="ACTIVE",
        )
        db.add(impl); db.commit()
        return impl.id


def test_selected_scope_allows_only_signed_implementations(context):
    http, factory = context
    seeded = _seed(factory, "SEL")
    approved = _approve(http, seeded, "SELECTED_IMPLEMENTATIONS", seeded["impls"][:1])
    assert approved.status_code == 200, approved.text

    allowed = _dependency(http, seeded, seeded["impls"][0])
    assert allowed.status_code == 201, allowed.text
    blocked = _dependency(http, seeded, seeded["impls"][1])
    assert blocked.status_code == 422
    assert blocked.json()["detail"] == "ADOPTION_SCOPE_EXCLUDES_IMPLEMENTATION"

    versions = http.get("/api/v1/domain/method-versions").json()
    v2 = next(item for item in versions if item["id"] == seeded["v2"])
    assert v2["adoption_policy"]["scope_mode"] == "SELECTED_IMPLEMENTATIONS"
    assert v2["adoption_policy"]["receipt_integrity"] == "VALID"
    assert v2["adoption_policy"]["implementation_ids"] == [seeded["impls"][0]]


def test_current_registered_scope_is_frozen_at_approval_time(context):
    http, factory = context
    seeded = _seed(factory, "CUR")
    approved = _approve(http, seeded, "CURRENT_REGISTERED_IMPLEMENTATIONS")
    assert approved.status_code == 200, approved.text

    future_id = _new_impl(factory, seeded, "CUR")
    assert _dependency(http, seeded, seeded["impls"][2]).status_code == 201
    blocked = _dependency(http, seeded, future_id)
    assert blocked.status_code == 422
    assert blocked.json()["detail"] == "ADOPTION_SCOPE_EXCLUDES_IMPLEMENTATION"


def test_method_catalog_scope_allows_future_same_module_implementation(context):
    http, factory = context
    seeded = _seed(factory, "CAT")
    approved = _approve(http, seeded, "METHOD_CATALOG")
    assert approved.status_code == 200, approved.text

    future_id = _new_impl(factory, seeded, "CAT")
    created = _dependency(http, seeded, future_id)
    assert created.status_code == 201, created.text


def test_receipt_tampering_blocks_future_reuse(context):
    http, factory = context
    seeded = _seed(factory, "TAMPER")
    approved = _approve(http, seeded, "SELECTED_IMPLEMENTATIONS", seeded["impls"][:1])
    assert approved.status_code == 200, approved.text
    receipt_id = approved.json()["receipt"]["id"]

    with factory() as db:
        detail = db.scalar(select(AdoptionReceiptDetail).where(AdoptionReceiptDetail.receipt_id == receipt_id))
        payload = dict(detail.receipt_payload_json)
        payload["approval_reason"] = "tampered after signing"
        detail.receipt_payload_json = payload
        db.commit()

    blocked = _dependency(http, seeded, seeded["impls"][0])
    assert blocked.status_code == 422
    assert blocked.json()["detail"] == "ADOPTION_RECEIPT_INTEGRITY_INVALID"


def test_blast_radius_filters_preexisting_out_of_scope_edges(context):
    http, factory = context
    seeded = _seed(factory, "ROUTE")
    approved = _approve(http, seeded, "SELECTED_IMPLEMENTATIONS", seeded["impls"][:1])
    assert approved.status_code == 200, approved.text

    with factory() as db:
        route_doc = EvidenceDocument(
            source="LOCAL_REPOSITORY", title="FSD-PTP-V2", document_type="FSD", version="2.0",
            content_hash="m09-route-doc", extracted_text="PTP-EVENT-v2 replay handling", char_count=28,
            parse_status="PARSED", index_status="INDEXED", metadata_json={}, chunk_count=1, embedding_degraded=False,
        )
        db.add(route_doc); db.flush()
        chunk = DocumentChunk(
            document_id=route_doc.id, chunk_index=0, text=route_doc.extracted_text,
            start_char=0, end_char=len(route_doc.extracted_text), chunk_hash="m09-route-chunk",
            embedding_vector="[0.0]", embedding_provider="TEST", embedding_model="TEST", embedding_dimensions=1,
        )
        db.add(chunk); db.flush()
        db.add(DependencyEdge(
            source_type="MethodVersion", source_id=seeded["v2"], target_type="EvidenceDocument", target_id=route_doc.id,
            relationship="SPECIFIED_BY", confidence=1.0,
        ))
        # Simulate legacy/direct DB edges that predate M09 enforcement.
        for impl_id in seeded["impls"][:2]:
            db.add(DependencyEdge(
                source_type="Implementation", source_id=impl_id, target_type="MethodVersion", target_id=seeded["v2"],
                relationship="USES_METHOD_VERSION", confidence=1.0, evidence_document_id=seeded["doc"],
            ))
        issue = db.get(SupportIssue, seeded["issue"])
        run = AgentRun(graph_run_id="CREED-R94-M09-ROUTING", issue_id=issue.id, status="RUNNING")
        db.add(run); db.flush()
        db.add(AnalysisEvidenceHit(
            agent_run_id=run.id, issue_id=issue.id, document_id=route_doc.id, chunk_id=chunk.id,
            rank=1, matched_queries_json=["PTP-EVENT-v2"], base_score=1.0, final_score=1.0,
            semantic_score=1.0, keyword_score=1.0, metadata_score=0.0, citation=route_doc.title,
            excerpt=route_doc.extracted_text,
        ))
        db.commit()
        impact = score_blast_radius(db, run)

    assert [item["implementation_id"] for item in impact["results"]] == [seeded["impls"][0]]
    assert impact["routing"]["adoption_scope"]["enforced"] is True
    assert impact["routing"]["adoption_scope"]["mode"] == "SELECTED_IMPLEMENTATIONS"
    assert impact["routing"]["adoption_scope"]["blocked_candidate_count"] == 1
    assert impact["routing"]["adoption_scope"]["blocked_candidates"][0]["implementation_id"] == seeded["impls"][1]
