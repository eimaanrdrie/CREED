from pathlib import Path

import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.domain import get_domain_db
from app.db.base import Base
from app.domain.models import (
    AgentRun, AnalysisImpactAssessment, Client, DeliveryMethod, EvidenceDocument, Finding, HumanAuthority,
    HumanDecision, Implementation, Investigation, MethodVersion, Module, Product,
    SupportIssue,
)
from app.main import app
from app.core.ai_runtime import QwenExecutionRecord
from app.services.advanced import learning_readiness
import app.services.advanced as advanced_service


@pytest.fixture
def context(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'r94_m06.db'}", connect_args={"check_same_thread": False})
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


def _seed_ready_run(factory):
    with factory() as db:
        product = Product(name="Collections", description="Collections", active=True)
        db.add(product); db.flush()
        module = Module(product_id=product.id, name="Promise-to-Pay", description="PTP", active=True)
        db.add(module); db.flush()
        method = DeliveryMethod(module_id=module.id, name="PTP Event Handling", description="Reusable PTP event method")
        db.add(method); db.flush()
        version = MethodVersion(method_id=method.id, version="PTP-EVENT-v1", status="APPROVED", summary="Approved baseline")
        db.add(version); db.flush()
        client = Client(name="Atlas Bank", client_type="BANK")
        db.add(client); db.flush()
        impl = Implementation(client_id=client.id, product_id=product.id, module_id=module.id, name="Atlas PTP Implementation", release_version="R1", status="ACTIVE")
        db.add(impl); db.flush()
        issue = SupportIssue(client_id=client.id, external_ticket_id="SUP-M06", title="Network retry replays Promise-to-Pay event", description="Replay issue", issue_type="BUG", severity="HIGH", status="OPEN")
        db.add(issue); db.flush()
        run = AgentRun(graph_run_id="CREED-R94-M06", issue_id=issue.id, status="COMPLETED")
        db.add(run); db.flush()
        inv = Investigation(issue_id=issue.id, agent_run_id=run.id, implementation_id=impl.id, status="COMPLETED", risk_score=.8)
        db.add(inv); db.flush()
        db.add(AnalysisImpactAssessment(agent_run_id=run.id, issue_id=issue.id, implementation_id=impl.id, method_version_id=version.id, impact_score=.8, impact_band="HIGH", reported_source=True, signals_json={}, weights_json={}, explanation_json=[], evidence_refs_json=[]))
        db.commit()
        return run.id, inv.id


def test_learning_readiness_requires_affected_decision_and_suggests_next_version(context):
    _http, factory = context
    run_id, inv_id = _seed_ready_run(factory)
    with factory() as db:
        run = db.get(AgentRun, run_id)
        before = learning_readiness(db, run)
        assert before["eligible"] is False
        assert before["reason"] == "FINAL_AFFECTED_DECISION_REQUIRED"
        assert before["source_method_version"]["version"] == "PTP-EVENT-v1"
        assert before["suggested_new_version"] == "PTP-EVENT-v2"

        db.add(HumanDecision(investigation_id=inv_id, decision="AFFECTED", reviewer="aisha.rahman@creed.example", reason="Evidence supports impact", metadata_json={"graph_run_id": run.graph_run_id}))
        db.commit()
        without_evidence = learning_readiness(db, run)
        assert without_evidence["eligible"] is False
        assert without_evidence["reason"] == "LEARNING_SUPPORTING_EVIDENCE_REQUIRED"

        doc = EvidenceDocument(source="LOCAL_REPOSITORY", title="CFG-READINESS", document_type="CONFIG", version="1.0", content_hash="readiness-hash", extracted_text="Replay behavior evidence", char_count=24, parse_status="PARSED", index_status="INDEXED", metadata_json={}, chunk_count=1, embedding_degraded=False)
        db.add(doc); db.flush()
        db.add(Finding(investigation_id=inv_id, finding_type="POTENTIALLY_AFFECTED", statement="Evidence supports impact.", confidence=.9, evidence_refs=[doc.id]))
        db.commit()
        after = learning_readiness(db, run)
        assert after["eligible"] is True
        assert after["reason"] == "READY"
        assert after["affected_decision_count"] == 1
        assert after["affected_reviewers"] == ["aisha.rahman@creed.example"]
        assert after["supporting_evidence_count"] == 1


def test_learning_proposal_create_requires_registered_human_decision_authority(context):
    http, factory = context
    with factory() as db:
        db.add(HumanAuthority(principal="decision@creed.local", display_name="Decision Reviewer", role_title="Reviewer", active=True, can_submit_human_decision=True, can_approve_learning=False, can_authorize_recall=False))
        db.add(HumanAuthority(principal="learning@creed.local", display_name="Learning Approver", role_title="Approver", active=True, can_submit_human_decision=False, can_approve_learning=True, can_authorize_recall=False))
        db.commit()

    payload = {"new_version": "PTP-EVENT-v2", "corrected_method": "Require idempotency before applying any state mutation.", "author": "decision@creed.local"}
    missing = http.post("/api/v1/analysis-runs/missing/learning-proposal", json=payload)
    assert missing.status_code == 403
    assert missing.json()["detail"] == "AUTHORITY_PRINCIPAL_REQUIRED"

    wrong = http.post("/api/v1/analysis-runs/missing/learning-proposal", json={**payload, "author": "learning@creed.local"}, headers={"X-CREED-Principal": "learning@creed.local"})
    assert wrong.status_code == 403
    assert wrong.json()["detail"] == "HUMAN_DECISION_AUTHORITY_REQUIRED"

    mismatch = http.post("/api/v1/analysis-runs/missing/learning-proposal", json={**payload, "author": "learning@creed.local"}, headers={"X-CREED-Principal": "decision@creed.local"})
    assert mismatch.status_code == 403
    assert mismatch.json()["detail"] == "AUTHORITY_PRINCIPAL_MISMATCH"

    authorized = http.post("/api/v1/analysis-runs/missing/learning-proposal", json=payload, headers={"X-CREED-Principal": "decision@creed.local"})
    assert authorized.status_code == 404
    assert authorized.json()["detail"] == "ANALYSIS_RUN_NOT_FOUND"


class LearningFakeRuntime:
    def require_model_available(self, model):
        assert model == "qwen3.5:4b"

    def generate_structured(self, *, prompt, schema_model, node, system_prompt, timeout=None, **kwargs):
        assert kwargs["model"] == "qwen3.5:4b"
        assert kwargs["format_schema"]["type"] == "object"
        evidence_ids = re.findall(r"EVIDENCE_ID=([^\n]+)", prompt)
        parsed = schema_model.model_validate({
            "title": "Idempotent Promise-to-Pay event handling",
            "reusable_learning": "Require idempotency validation before applying a Promise-to-Pay state mutation.",
            "applicability": "Promise-to-Pay event handlers that can receive network retries.",
            "guardrails": ["Use a stable idempotency key before mutating collection state."],
            "validation_steps": ["Replay the same event key and confirm only one state transition."],
            "evidence_ids": evidence_ids[:1],
        })
        record = QwenExecutionRecord(
            run_id="QWEN-R94-M06", node=node, configured_model="qwen3.5:4b", actual_model="qwen3.5:4b",
            started_at="2026-08-20T10:00:00+00:00", completed_at="2026-08-20T10:00:01+00:00", duration_ms=820.0,
            prompt_eval_count=240, eval_count=70, total_duration_ns=820000000, load_duration_ns=10000000,
            success=True, structured_output_valid=True, error=None,
        )
        return parsed, record, {"model": "qwen3.5:4b"}


def test_authorized_human_correction_creates_run_scoped_qwen_learning_proposal(context, monkeypatch):
    http, factory = context
    run_id, inv_id = _seed_ready_run(factory)
    correction = "Require an idempotency-key check before any Promise-to-Pay state mutation; duplicate event keys return the existing result without a second transition."
    with factory() as db:
        run = db.get(AgentRun, run_id)
        doc = EvidenceDocument(
            source="LOCAL_REPOSITORY", title="CFG-ATLAS-PTP-01", document_type="CONFIG", version="1.0",
            content_hash="m06-evidence-hash", extracted_text="The current handler applies a state transition after a retry without a durable idempotency guard.",
            char_count=98, parse_status="PARSED", index_status="INDEXED", metadata_json={}, chunk_count=1, embedding_degraded=False,
        )
        db.add(doc); db.flush()
        db.add(Finding(investigation_id=inv_id, finding_type="POTENTIALLY_AFFECTED", statement="Replay can apply a duplicate state transition.", confidence=.9, evidence_refs=[doc.id]))
        db.add(HumanDecision(investigation_id=inv_id, decision="AFFECTED", reviewer="aisha.rahman@creed.example", reason="Persisted evidence supports impact.", metadata_json={"graph_run_id": run.graph_run_id}))
        db.add(HumanAuthority(principal="aisha.rahman@creed.example", display_name="Aisha Rahman", role_title="Transformation Assurance Lead", active=True, can_submit_human_decision=True, can_approve_learning=True, can_authorize_recall=True))
        graph_run_id = run.graph_run_id
        db.commit()

    monkeypatch.setattr(advanced_service, "get_ollama_runtime", lambda: LearningFakeRuntime())
    created = http.post(
        f"/api/v1/analysis-runs/{graph_run_id}/learning-proposal",
        headers={"X-CREED-Principal": "aisha.rahman@creed.example"},
        json={"new_version": "PTP-EVENT-v2", "corrected_method": correction, "author": "aisha.rahman@creed.example"},
    )
    assert created.status_code == 200, created.text
    payload = created.json()
    assert payload["status"] == "PROPOSED"
    assert payload["source_method_version"]["version"] == "PTP-EVENT-v1"
    assert payload["proposed_method_version"]["version"] == "PTP-EVENT-v2"
    assert payload["correction_input"] == correction
    assert payload["qwen"]["run_id"] == "QWEN-R94-M06"
    assert payload["supporting_evidence_refs"]

    fetched = http.get(f"/api/v1/analysis-runs/{graph_run_id}/learning-proposal")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == payload["id"]
