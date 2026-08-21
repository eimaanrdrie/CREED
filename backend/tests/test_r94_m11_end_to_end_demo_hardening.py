from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.api.domain import get_domain_db
from app.core.ai_runtime import QwenExecutionRecord
from app.core.config import get_settings
from app.db.base import Base
from app.domain.models import (
    AgentRun,
    Client,
    EvidenceDocument,
    HumanAuthority,
    HumanDecision,
    Implementation,
    LearningProposal,
    MethodVersion,
    ResponsibilityAssignment,
    SupportIssue,
)
from app.main import app
from app.services.advanced import LearningOutput, discover_evidence, run_investigations, score_blast_radius
from app.services.demo import demo_readiness, reset_demo
import app.services.advanced as advanced_service
import app.services.analysis_runs as analysis_runs_service
import app.services.demo as demo_service


class _FakeReadyRuntime:
    def runtime_snapshot(self, *, refresh: bool = False):
        return {
            "status": "READY",
            "configured_model": "qwen3.5:9b",
            "actual_model": "qwen3.5:9b",
            "inference": "PASSED",
            "last_error": None,
        }


class _FakeLearningRuntime(_FakeReadyRuntime):
    def require_model_available(self, model):
        assert model == "qwen3.5:4b"

    def generate_structured(self, *, prompt, schema_model, node, **kwargs):
        assert kwargs["model"] == "qwen3.5:4b"
        assert kwargs["format_schema"]["type"] == "object"
        assert node == "learning_agent"
        evidence_ids = list(dict.fromkeys(re.findall(r"EVIDENCE_ID=([A-Za-z0-9-]+)", prompt)))
        output = LearningOutput(
            title="Replay-safe Promise-to-Pay handling",
            reusable_learning="Require a stable idempotency key before any Promise-to-Pay state mutation so a replay cannot apply a second transition.",
            applicability="Promise-to-Pay event handlers using the governed PTP Event Handling method.",
            guardrails=["Use a stable business-event key", "Do not suppress distinct legitimate updates"],
            validation_steps=["Replay the same key", "Submit a distinct update after replay"],
            evidence_ids=evidence_ids[:2],
        )
        record = QwenExecutionRecord(
            run_id="QWEN-R94-M11-LEARNING",
            node="learning_agent",
            configured_model="qwen3.5:4b",
            actual_model="qwen3.5:4b",
            started_at="2026-08-20T00:00:00+00:00",
            completed_at="2026-08-20T00:00:01+00:00",
            duration_ms=1000.0,
            prompt_eval_count=120,
            eval_count=80,
            total_duration_ns=None,
            load_duration_ns=None,
            success=True,
            structured_output_valid=True,
            error=None,
        )
        return output, record, output.model_dump()


@pytest.fixture
def context(tmp_path: Path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'r94_m11.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_domain_db] = override_db
    settings = get_settings()
    monkeypatch.setattr(settings, "document_storage_path", str(tmp_path / "documents"))
    monkeypatch.setattr(settings, "investigation_use_heuristic_fast_path", True)
    monkeypatch.setattr(settings, "investigation_top_k", 3)
    monkeypatch.setattr(demo_service, "get_settings", lambda: type("DemoSettings", (), {"demo_mode_enabled": True})())
    monkeypatch.setattr(demo_service, "get_ollama_runtime", lambda: _FakeReadyRuntime())
    monkeypatch.setattr(analysis_runs_service, "langgraph_runtime_available", lambda: (True, None))
    monkeypatch.setattr(analysis_runs_service, "resume_analysis_run", lambda **kwargs: {"status": "COMPLETED"})
    try:
        yield TestClient(app), factory, monkeypatch
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_demo_reset_is_complete_repeatable_and_judge_ready(context):
    _http, factory, _monkeypatch = context
    with factory() as db:
        first = reset_demo(db)
        second = reset_demo(db)
        assert first["ready"] is True
        assert second["ready"] is True
        assert second["dataset"] == "CREED-DEMO-1.1"
        assert second["documents"] == 10
        assert second["indexed_documents"] == 10
        assert second["clients"] == 3
        assert second["implementations"] == 3
        assert second["dependency_edges"] == 11
        assert second["active_authorities"] == 5
        assert second["decision_authorities"] == 2
        assert second["learning_authorities"] == 2
        assert second["recall_authorities"] == 1
        assert second["production_deployments"] == 3
        assert second["ownership_assignments"] == 10
        assert db.scalar(select(HumanAuthority).where(HumanAuthority.principal == "aisha.rahman@creed.example")) is not None
        assert len(db.scalars(select(ResponsibilityAssignment)).all()) == 10

        readiness = demo_readiness(db, refresh_runtime=True)
        assert readiness["ready"] is True
        assert readiness["blocking_checks"] == []
        assert all(check["status"] != "BLOCKED" for check in readiness["checks"])
        assert any(check["key"] == "recall_fixture" and check["status"] == "PASS" for check in readiness["checks"])


def test_readiness_fails_closed_if_live_issue_or_governance_baseline_is_dirty(context):
    _http, factory, _monkeypatch = context
    with factory() as db:
        reset_demo(db)
        atlas = db.scalar(select(Client).where(Client.name == "Atlas Bank"))
        db.add(SupportIssue(
            external_ticket_id="SUP-PTP-001",
            client_id=atlas.id,
            title="Network retry replays Promise-to-Pay event",
            description="Live demo issue should not exist before judging.",
            issue_type="BUG",
            severity="HIGH",
            status="OPEN",
        ))
        authority = db.scalar(select(HumanAuthority).where(HumanAuthority.principal == "aisha.rahman@creed.example"))
        authority.can_authorize_recall = False
        db.commit()

        readiness = demo_readiness(db, refresh_runtime=False)
        assert readiness["ready"] is False
        blocked = {item["key"] for item in readiness["checks"] if item["status"] == "BLOCKED"}
        assert "baseline" in blocked
        assert "authority" in blocked
        assert "clean_case" in blocked


def test_full_judge_path_issue_to_receipt_to_scope_aware_recall(context):
    http, factory, monkeypatch = context
    monkeypatch.setattr(advanced_service, "get_ollama_runtime", lambda: _FakeLearningRuntime())

    with factory() as db:
        reset_demo(db)
        atlas = db.scalar(select(Client).where(Client.name == "Atlas Bank"))
        atlas_id = atlas.id

    # 1. Live issue is created through the real issue API.
    issue_response = http.post("/api/v1/issues", json={
        "external_ticket_id": "SUP-PTP-001",
        "client_id": atlas_id,
        "title": "Network retry replays Promise-to-Pay event",
        "description": "Atlas Bank reports that a network retry can replay the same Promise-to-Pay event. The repeated event appears to apply another collection-state transition. The issue occurs when the original request times out and the upstream system retries the same event. Please investigate whether the event-processing method is idempotent and whether the same implementation approach has been reused for other clients.",
        "issue_type": "BUG",
        "severity": "HIGH",
    })
    assert issue_response.status_code == 201, issue_response.text
    issue = issue_response.json()

    # 2. Real retrieval / routing services operate on the reset dataset. Investigation is
    # deterministic in this regression, while production keeps the Qwen investigation path.
    with factory() as db:
        run = AgentRun(graph_run_id="CREED-R94-M11-E2E", issue_id=issue["id"], status="RUNNING", input_summary=issue["title"])
        db.add(run); db.commit(); run_id = run.id
        evidence = discover_evidence(db, run)
        impact = score_blast_radius(db, run)
        investigations = run_investigations(db, run)
        assert evidence["result_count"] > 0
        assert len(impact["results"]) == 3
        assert {item["client_name"] for item in impact["results"]} == {"Atlas Bank", "Meridian Bank", "Nova Finance"}
        assert investigations["result_count"] == 3
        run.status = "WAITING_HUMAN"
        db.commit()
        review_items = investigations["results"]

    # 3. Human Authority decides every run-scoped review case.
    decision_payload = []
    with factory() as db:
        for item in review_items:
            impl = db.get(Implementation, item["implementation_id"])
            decision_payload.append({
                "investigation_id": item["investigation_id"],
                "decision": "NOT_AFFECTED" if impl.client.name == "Nova Finance" else "AFFECTED",
                "reason": "Reviewed the implementation-specific configuration and test evidence for this run.",
            })
    review_response = http.post(
        "/api/v1/analysis-runs/CREED-R94-M11-E2E/human-review/resume",
        headers={"X-CREED-Principal": "aisha.rahman@creed.example"},
        json={"reviewer": "aisha.rahman@creed.example", "decisions": decision_payload},
    )
    assert review_response.status_code == 200, review_response.text
    with factory() as db:
        run = db.get(AgentRun, run_id)
        run.status = "COMPLETED"
        db.commit()
        assert len(db.scalars(select(HumanDecision)).all()) == 3

    # 4. Human correction -> real learning service contract -> run-scoped proposal.
    readiness = http.get("/api/v1/analysis-runs/CREED-R94-M11-E2E/learning-readiness")
    assert readiness.status_code == 200
    assert readiness.json()["eligible"] is True
    learning_response = http.post(
        "/api/v1/analysis-runs/CREED-R94-M11-E2E/learning-proposal",
        headers={"X-CREED-Principal": "aisha.rahman@creed.example"},
        json={
            "new_version": "PTP-EVENT-v2",
            "corrected_method": "Require an idempotency-key check before any Promise-to-Pay state mutation. If the same event key has already been processed, return the existing result without applying another state transition.",
            "author": "aisha.rahman@creed.example",
        },
    )
    assert learning_response.status_code == 200, learning_response.text
    proposal = learning_response.json()
    assert proposal["status"] == "PROPOSED"

    # 5. Separate Learning Authority decision creates a signed, scoped Adoption Receipt.
    approval = http.post(
        f"/api/v1/learning-proposals/{proposal['id']}/decision",
        headers={"X-CREED-Principal": "aisha.rahman@creed.example"},
        json={
            "reviewer": "aisha.rahman@creed.example",
            "decision": "APPROVE_LEARNING",
            "reason": "Approve the replay-safe correction for the current registered PTP implementations.",
            "adoption_scope": {"mode": "CURRENT_REGISTERED_IMPLEMENTATIONS", "implementation_ids": []},
        },
    )
    assert approval.status_code == 200, approval.text
    receipt = approval.json()["receipt"]
    assert receipt["integrity"] == "VALID"
    assert receipt["adoption_scope"]["registered_adopter_count"] == 3
    verify_receipt = http.get(f"/api/v1/adoption-receipts/{receipt['id']}/verify")
    assert verify_receipt.status_code == 200 and verify_receipt.json()["valid"] is True

    # 6. Adoption is explicit, never automatic: register Atlas on v2 before recalling v2.
    with factory() as db:
        atlas_impl = db.scalar(select(Implementation).join(Client).where(Client.name == "Atlas Bank"))
        cfg = db.scalar(select(EvidenceDocument).where(EvidenceDocument.title == "CFG-ATLAS-PTP-01"))
        v2 = db.scalar(select(MethodVersion).where(MethodVersion.version == "PTP-EVENT-v2"))
        atlas_impl_id, cfg_id, v2_id = atlas_impl.id, cfg.id, v2.id
    adoption = http.post("/api/v1/domain/dependencies", json={
        "implementation_id": atlas_impl_id,
        "method_version_id": v2_id,
        "evidence_document_id": cfg_id,
    })
    assert adoption.status_code == 201, adoption.text

    # 7. Optional recall extension uses a separate evidence-bearing issue, uploaded through
    # the normal ingestion path, then routes only the explicit in-scope v2 adopter.
    recall_issue_response = http.post("/api/v1/issues", json={
        "external_ticket_id": "SUP-PTP-RECALL-001",
        "client_id": atlas_id,
        "title": "Post-adoption idempotency key collision suppresses a valid update",
        "description": "Regression evidence shows the v2 replay key can collide across two distinct legitimate Promise-to-Pay updates after gateway recovery.",
        "issue_type": "INCIDENT",
        "severity": "HIGH",
    })
    assert recall_issue_response.status_code == 201
    recall_issue = recall_issue_response.json()
    recall_file = Path(__file__).resolve().parents[1] / "demo_data" / "RECALL-PTP-V2-001.md"
    with recall_file.open("rb") as fh:
        upload = http.post(
            "/api/v1/documents",
            data={"source": "ISSUE_ATTACHMENT", "title": "RECALL-PTP-V2-001", "version": "1.0", "issue_id": recall_issue["id"]},
            files={"file": (recall_file.name, fh, "text/markdown")},
        )
    assert upload.status_code == 201, upload.text

    recall_response = http.post(
        f"/api/v1/method-versions/{v2_id}/revoke",
        headers={"X-CREED-Principal": "aisha.rahman@creed.example"},
        json={
            "source_issue_id": recall_issue["id"],
            "reviewer": "aisha.rahman@creed.example",
            "reason": "Post-adoption regression evidence invalidates the current v2 idempotency-key derivation rule.",
        },
    )
    assert recall_response.status_code == 200, recall_response.text
    recall = recall_response.json()
    assert recall["integrity"] == "VALID"
    assert recall["routing_scope"]["enforced"] is True
    assert recall["routing_scope"]["routed_count"] == 1
    assert recall["cases"][0]["implementation_id"] == atlas_impl_id
    verify_recall = http.get(f"/api/v1/recalls/{recall['id']}/verify")
    assert verify_recall.status_code == 200 and verify_recall.json()["valid"] is True

    # 8. The governed outputs remain persisted and independently inspectable.
    with factory() as db:
        assert db.scalar(select(LearningProposal).where(LearningProposal.id == proposal["id"])) is not None
        assert db.scalar(select(MethodVersion).where(MethodVersion.id == v2_id)).status == "REVOKED"
