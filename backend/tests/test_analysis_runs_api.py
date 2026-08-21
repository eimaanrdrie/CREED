from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.api.domain import get_domain_db
from app.db.base import Base
from app.domain.models import AgentEvent, AgentRun, AgentStep, AuditEvent
from app.main import app
import app.api.analysis_runs as analysis_api


@pytest.fixture
def context(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "m08.db"
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
        yield TestClient(app), factory, monkeypatch
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def create_issue(client: TestClient):
    bank = client.post("/api/v1/domain/clients", json={"name": "Atlas Bank", "client_type": "BANK"}).json()
    response = client.post(
        "/api/v1/issues",
        json={
            "external_ticket_id": "SUP-M08-1",
            "client_id": bank["id"],
            "title": "Duplicate PTP event",
            "description": "Atlas Bank reports duplicate Promise-to-Pay events changing collection state.",
            "issue_type": "BUG",
            "severity": "HIGH",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_start_run_persists_real_agent_lifecycle_rows(context):
    client, factory, _ = context
    issue = create_issue(client)
    response = client.post(f"/api/v1/issues/{issue['id']}/analysis-runs")
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["graph_run_id"].startswith("CREED-")
    assert body["status"] == "QUEUED"
    assert body["checkpoint_backend"] == "SQLITE"
    assert [step["agent_name"] for step in body["steps"]] == [
        "intake_agent", "retrieval_agent", "knowledge_link_agent", "impact_agent",
        "investigation_agent", "evidence_validator", "human_review_boundary",
    ]
    assert all(step["status"] == "QUEUED" for step in body["steps"])
    assert all(step["metadata"]["runtime_source"] == "LANGGRAPH_NODE" for step in body["steps"])

    with factory() as db:
        assert db.scalar(select(func.count()).select_from(AgentRun)) == 1
        assert db.scalar(select(func.count()).select_from(AgentStep)) == 7
        assert db.scalar(select(func.count()).select_from(AgentEvent)) == 7
        assert db.scalar(select(AuditEvent).where(AuditEvent.action == "ANALYSIS_RUN_QUEUED")) is not None


def test_second_start_returns_active_run_instead_of_duplicate(context):
    client, factory, _ = context
    issue = create_issue(client)
    first = client.post(f"/api/v1/issues/{issue['id']}/analysis-runs").json()
    second = client.post(f"/api/v1/issues/{issue['id']}/analysis-runs").json()
    assert second["id"] == first["id"]
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(AgentRun)) == 1


def test_latest_and_run_detail_survive_refresh(context):
    client, _, _ = context
    issue = create_issue(client)
    created = client.post(f"/api/v1/issues/{issue['id']}/analysis-runs").json()
    latest = client.get(f"/api/v1/issues/{issue['id']}/analysis-runs/latest")
    assert latest.status_code == 200
    assert latest.json()["graph_run_id"] == created["graph_run_id"]
    detail = client.get(f"/api/v1/analysis-runs/{created['graph_run_id']}")
    assert detail.status_code == 200
    assert len(detail.json()["steps"]) == 7


def test_sse_emits_persisted_terminal_snapshot(context):
    client, factory, _ = context
    issue = create_issue(client)
    created = client.post(f"/api/v1/issues/{issue['id']}/analysis-runs").json()
    with factory() as db:
        run = db.get(AgentRun, created["id"])
        run.status = "COMPLETED"
        for step in db.scalars(select(AgentStep).where(AgentStep.agent_run_id == run.id)).all():
            step.status = "COMPLETED" if step.agent_name != "human_review_boundary" else "SKIPPED"
        db.commit()
    response = client.get(f"/api/v1/analysis-runs/{created['graph_run_id']}/events")
    assert response.status_code == 200
    assert "event: agent_step" in response.text
    assert "event: snapshot" in response.text
    assert '"status":"COMPLETED"' in response.text
    assert "event: terminal" in response.text


def test_langgraph_missing_fails_closed_without_run(context, monkeypatch):
    client, factory, _ = context
    issue = create_issue(client)
    monkeypatch.setattr(analysis_api, "langgraph_runtime_available", lambda: (False, "ModuleNotFoundError: langgraph"))
    response = client.post(f"/api/v1/issues/{issue['id']}/analysis-runs")
    assert response.status_code == 503
    assert response.json()["detail"].startswith("LANGGRAPH_RUNTIME_UNAVAILABLE")
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(AgentRun)) == 0
