from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.api.domain import get_domain_db
from app.db.base import Base
from app.domain.models import (
    AgentRun,
    AgentStep,
    AuditEvent,
    Client,
    Implementation,
    Investigation,
    InvestigationDetail,
    Module,
    Product,
    SupportIssue,
)
from app.main import app
import app.api.analysis_runs as analysis_api


@pytest.fixture
def context(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "r94_m04.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_domain_db] = override_db
    monkeypatch.setattr(analysis_api, "langgraph_runtime_available", lambda: (True, None))
    monkeypatch.setattr(analysis_api, "launch_analysis_run", lambda **kwargs: None)
    try:
        yield TestClient(app), factory
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def _seed_stale_waiting_run(factory):
    with factory() as db:
        issue = SupportIssue(
            external_ticket_id="SUP-R94-M04",
            title="Network retry replays Promise-to-Pay event",
            description="Stale zero-case run created before the routing guard fix.",
            issue_type="BUG",
            severity="HIGH",
            status="WAITING_HUMAN",
        )
        db.add(issue)
        db.flush()
        run = AgentRun(
            graph_run_id="CREED-R94-M04-STALE",
            issue_id=issue.id,
            status="WAITING_HUMAN",
            input_summary=issue.title,
            output_summary="AI investigation complete · waiting for human review",
        )
        db.add(run)
        db.flush()
        for sequence, name, status in [
            (10, "intake_agent", "COMPLETED"),
            (20, "retrieval_agent", "COMPLETED"),
            (30, "knowledge_link_agent", "COMPLETED"),
            (40, "impact_agent", "COMPLETED"),
            (50, "investigation_agent", "COMPLETED"),
            (60, "evidence_validator", "COMPLETED"),
            (70, "human_review_boundary", "WAITING_HUMAN"),
        ]:
            db.add(
                AgentStep(
                    agent_run_id=run.id,
                    agent_name=name,
                    status=status,
                    sequence=sequence,
                    input_summary=name,
                    metadata_json={"display_name": name, "runtime_source": "LANGGRAPH_NODE"},
                )
            )
        db.commit()
        return issue.id, run.id, run.graph_run_id


def test_recovery_supersedes_zero_case_waiting_run_and_starts_fresh_run(context):
    client, factory = context
    issue_id, old_run_id, old_graph_run_id = _seed_stale_waiting_run(factory)

    before = client.get(f"/api/v1/analysis-runs/{old_graph_run_id}")
    assert before.status_code == 200
    assert before.json()["recovery_eligible"] is True
    assert before.json()["recovery_reason"] == "STALE_ZERO_CASE_HUMAN_REVIEW"

    response = client.post(
        f"/api/v1/issues/{issue_id}/analysis-runs/recover",
        json={"reason": "Recover stale zero-case Human Review checkpoint after routing correction."},
    )
    assert response.status_code == 202, response.text
    fresh = response.json()
    assert fresh["id"] != old_run_id
    assert fresh["graph_run_id"] != old_graph_run_id
    assert fresh["status"] == "QUEUED"
    assert fresh["recovery_eligible"] is False

    with factory() as db:
        assert db.scalar(select(func.count()).select_from(AgentRun)) == 2
        old = db.get(AgentRun, old_run_id)
        assert old is not None and old.status == "CANCELLED"
        assert old.completed_at is not None
        assert "controlled zero-case recovery" in (old.output_summary or "").lower()
        old_human = db.scalar(
            select(AgentStep).where(
                AgentStep.agent_run_id == old_run_id,
                AgentStep.agent_name == "human_review_boundary",
            )
        )
        assert old_human is not None and old_human.status == "CANCELLED"
        assert old_human.metadata_json["recovery_superseded"] is True
        issue = db.get(SupportIssue, issue_id)
        assert issue is not None and issue.status == "ANALYSING"
        superseded = db.scalar(
            select(AuditEvent).where(
                AuditEvent.object_id == old_run_id,
                AuditEvent.action == "ANALYSIS_RUN_RECOVERY_SUPERSEDED",
            )
        )
        assert superseded is not None
        assert superseded.metadata_json["preserved_history"] is True
        assert superseded.metadata_json["preserved_checkpoint"] is True
        started = db.scalar(
            select(AuditEvent).where(
                AuditEvent.object_id == fresh["id"],
                AuditEvent.action == "ANALYSIS_RUN_RECOVERY_STARTED",
            )
        )
        assert started is not None
        assert started.metadata_json["previous_run_id"] == old_run_id
        assert started.metadata_json["previous_graph_run_id"] == old_graph_run_id


def test_recovery_refuses_to_bypass_real_human_review_cases(context):
    client, factory = context
    issue_id, old_run_id, old_graph_run_id = _seed_stale_waiting_run(factory)
    with factory() as db:
        product = Product(name="Collections", active=True)
        db.add(product); db.flush()
        module = Module(product_id=product.id, name="Promise-to-Pay", active=True)
        db.add(module); db.flush()
        bank = Client(name="Atlas Bank", client_type="BANK")
        db.add(bank); db.flush()
        impl = Implementation(
            client_id=bank.id,
            product_id=product.id,
            module_id=module.id,
            name="Atlas PTP Implementation",
            release_version="R1",
            status="ACTIVE",
        )
        db.add(impl); db.flush()
        inv = Investigation(
            issue_id=issue_id,
            implementation_id=impl.id,
            status="WAITING_HUMAN",
            risk_score=88.0,
        )
        db.add(inv); db.flush()
        db.add(
            InvestigationDetail(
                investigation_id=inv.id,
                agent_run_id=old_run_id,
                evidence_observations_json=[],
                missing_evidence_json=[],
                model_output_json={},
                evidence_validation_status="VALID",
            )
        )
        db.commit()

    detail = client.get(f"/api/v1/analysis-runs/{old_graph_run_id}")
    assert detail.status_code == 200
    assert detail.json()["recovery_eligible"] is False
    assert detail.json()["recovery_reason"] == "HUMAN_REVIEW_CASES_EXIST"

    response = client.post(
        f"/api/v1/issues/{issue_id}/analysis-runs/recover",
        json={"reason": "Attempted recovery"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "HUMAN_REVIEW_CASES_EXIST"
    with factory() as db:
        old = db.get(AgentRun, old_run_id)
        assert old is not None and old.status == "WAITING_HUMAN"
        assert db.scalar(select(func.count()).select_from(AgentRun)) == 1
        assert db.scalar(select(AuditEvent).where(AuditEvent.action == "ANALYSIS_RUN_RECOVERY_SUPERSEDED")) is None


def test_normal_start_still_reuses_waiting_run_until_explicit_recovery(context):
    client, factory = context
    issue_id, old_run_id, _ = _seed_stale_waiting_run(factory)
    response = client.post(f"/api/v1/issues/{issue_id}/analysis-runs")
    assert response.status_code == 202
    assert response.json()["id"] == old_run_id
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(AgentRun)) == 1
