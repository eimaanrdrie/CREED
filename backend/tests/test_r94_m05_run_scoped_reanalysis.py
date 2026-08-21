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
    Client,
    DeliveryMethod,
    Finding,
    HumanAuthority,
    HumanDecision,
    Implementation,
    Investigation,
    InvestigationDetail,
    LearningProposal,
    LearningProposalDetail,
    MethodVersion,
    Module,
    Product,
    SupportIssue,
)
from app.main import app
import app.api.analysis_runs as analysis_api
import app.services.analysis_runs as analysis_service


@pytest.fixture
def context(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "r94_m05.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_domain_db] = override_db
    monkeypatch.setattr(analysis_api, "langgraph_runtime_available", lambda: (True, None))
    monkeypatch.setattr(analysis_api, "launch_analysis_run", lambda **kwargs: None)
    monkeypatch.setattr(analysis_service, "langgraph_runtime_available", lambda: (True, None))
    monkeypatch.setattr(
        analysis_service,
        "resume_analysis_run",
        lambda **kwargs: {"status": "COMPLETED", "graph_run_id": kwargs.get("run_db_id")},
    )
    try:
        yield TestClient(app), factory
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def _seed(factory):
    with factory() as db:
        product = Product(name="Collections", active=True)
        db.add(product); db.flush()
        module = Module(product_id=product.id, name="Promise-to-Pay", active=True)
        db.add(module); db.flush()
        client = Client(name="Atlas Bank", client_type="BANK")
        db.add(client); db.flush()
        impl = Implementation(
            client_id=client.id,
            product_id=product.id,
            module_id=module.id,
            name="Atlas PTP Implementation",
            release_version="R1",
            status="ACTIVE",
        )
        db.add(impl); db.flush()
        issue = SupportIssue(
            client_id=client.id,
            external_ticket_id="SUP-R94-M05",
            title="Network retry replays Promise-to-Pay event",
            description="Same issue is deliberately analysed more than once.",
            issue_type="BUG",
            severity="HIGH",
            status="OPEN",
        )
        db.add(issue); db.flush()
        authority = HumanAuthority(
            principal="aisha.rahman@creed.example",
            display_name="Aisha Rahman",
            role_title="Transformation Assurance Lead",
            active=True,
            can_submit_human_decision=True,
            can_approve_learning=True,
            can_authorize_recall=True,
        )
        db.add(authority); db.flush()

        old_run = AgentRun(
            graph_run_id="CREED-R94-M05-OLD",
            issue_id=issue.id,
            status="COMPLETED",
            input_summary=issue.title,
            output_summary="Prior governed analysis",
        )
        db.add(old_run); db.flush()
        old_inv = Investigation(
            issue_id=issue.id,
            agent_run_id=old_run.id,
            implementation_id=impl.id,
            status="COMPLETED",
            risk_score=.82,
        )
        db.add(old_inv); db.flush()
        old_finding = Finding(
            investigation_id=old_inv.id,
            finding_type="POTENTIALLY_AFFECTED",
            statement="Prior run finding",
            confidence=.8,
            evidence_refs=[],
        )
        db.add(old_finding); db.flush()
        db.add(
            InvestigationDetail(
                investigation_id=old_inv.id,
                agent_run_id=old_run.id,
                finding_id=old_finding.id,
                evidence_observations_json=[],
                missing_evidence_json=[],
                model_output_json={},
                evidence_validation_status="VALID",
            )
        )
        db.add(
            HumanDecision(
                investigation_id=old_inv.id,
                decision="AFFECTED",
                reviewer=authority.principal,
                reason="Prior run decision",
                metadata_json={"graph_run_id": old_run.graph_run_id},
            )
        )
        db.commit()
        return issue.id, impl.id, old_run.id, old_run.graph_run_id, old_inv.id, authority.principal


def test_normal_run_again_can_create_fresh_investigation_for_same_implementation(context):
    client, factory = context
    issue_id, impl_id, old_run_id, old_graph_id, old_inv_id, _ = _seed(factory)

    response = client.post(f"/api/v1/issues/{issue_id}/analysis-runs")
    assert response.status_code == 202, response.text
    new_run = response.json()
    assert new_run["id"] != old_run_id
    assert new_run["graph_run_id"] != old_graph_id

    with factory() as db:
        new_inv = Investigation(
            issue_id=issue_id,
            agent_run_id=new_run["id"],
            implementation_id=impl_id,
            status="WAITING_HUMAN",
            risk_score=.61,
        )
        db.add(new_inv)
        db.commit()
        assert db.scalar(select(func.count()).select_from(Investigation).where(Investigation.issue_id == issue_id)) == 2
        assert db.get(Investigation, old_inv_id).agent_run_id == old_run_id


def test_run_endpoints_do_not_leak_prior_investigations_or_decisions(context):
    client, factory = context
    issue_id, impl_id, _old_run_id, old_graph_id, old_inv_id, _ = _seed(factory)

    with factory() as db:
        new_run = AgentRun(graph_run_id="CREED-R94-M05-NEW", issue_id=issue_id, status="WAITING_HUMAN")
        db.add(new_run); db.flush()
        new_inv = Investigation(
            issue_id=issue_id,
            agent_run_id=new_run.id,
            implementation_id=impl_id,
            status="WAITING_HUMAN",
            risk_score=.61,
        )
        db.add(new_inv); db.flush()
        db.commit()
        new_graph_id = new_run.graph_run_id
        new_inv_id = new_inv.id

    old_view = client.get(f"/api/v1/analysis-runs/{old_graph_id}/investigations")
    assert old_view.status_code == 200
    assert [item["id"] for item in old_view.json()["results"]] == [old_inv_id]
    assert old_view.json()["results"][0]["human_decision"]["decision"] == "AFFECTED"

    new_view = client.get(f"/api/v1/analysis-runs/{new_graph_id}/investigations")
    assert new_view.status_code == 200
    assert [item["id"] for item in new_view.json()["results"]] == [new_inv_id]
    assert new_view.json()["results"][0]["human_decision"] is None

    human = client.get(f"/api/v1/analysis-runs/{new_graph_id}/human-review")
    assert human.status_code == 200
    assert human.json()["pending_count"] == 1
    assert [item["id"] for item in human.json()["items"]] == [new_inv_id]


def test_human_review_rejects_investigation_from_another_run(context):
    client, factory = context
    issue_id, impl_id, _old_run_id, _old_graph_id, old_inv_id, principal = _seed(factory)

    with factory() as db:
        new_run = AgentRun(graph_run_id="CREED-R94-M05-DECISION", issue_id=issue_id, status="WAITING_HUMAN")
        db.add(new_run); db.flush()
        new_inv = Investigation(
            issue_id=issue_id,
            agent_run_id=new_run.id,
            implementation_id=impl_id,
            status="WAITING_HUMAN",
            risk_score=.63,
        )
        db.add(new_inv); db.flush(); db.commit()
        graph_id = new_run.graph_run_id
        new_inv_id = new_inv.id

    wrong = client.post(
        f"/api/v1/analysis-runs/{graph_id}/human-review/resume",
        headers={"X-CREED-Principal": principal},
        json={
            "reviewer": principal,
            "decisions": [{"investigation_id": old_inv_id, "decision": "AFFECTED", "reason": "Wrong run"}],
        },
    )
    assert wrong.status_code == 422
    assert wrong.json()["detail"] == "COMPLETE_REVIEW_REQUIRED"

    correct = client.post(
        f"/api/v1/analysis-runs/{graph_id}/human-review/resume",
        headers={"X-CREED-Principal": principal},
        json={
            "reviewer": principal,
            "decisions": [{"investigation_id": new_inv_id, "decision": "NOT_AFFECTED", "reason": "Current run evidence"}],
        },
    )
    assert correct.status_code == 200, correct.text

    with factory() as db:
        old = db.get(Investigation, old_inv_id)
        new = db.get(Investigation, new_inv_id)
        assert len(old.decisions) == 1
        assert old.decisions[0].reason == "Prior run decision"
        assert len(new.decisions) == 1
        assert new.decisions[0].decision == "NOT_AFFECTED"
        assert new.decisions[0].metadata_json["graph_run_id"] == graph_id


def test_learning_proposal_lookup_is_run_scoped(context):
    client, factory = context
    issue_id, _impl_id, old_run_id, old_graph_id, _old_inv_id, _principal = _seed(factory)

    with factory() as db:
        module = db.scalar(select(Module).where(Module.name == "Promise-to-Pay"))
        method = DeliveryMethod(module_id=module.id, name="PTP Event Handling", description="Run-scoped learning test")
        db.add(method); db.flush()
        v1 = MethodVersion(method_id=method.id, version="PTP-EVENT-v1", status="APPROVED", summary="Baseline")
        v2 = MethodVersion(method_id=method.id, version="PTP-EVENT-v2", status="PROPOSED", summary="Prior run proposal")
        db.add_all([v1, v2]); db.flush()
        proposal = LearningProposal(
            source_issue_id=issue_id,
            proposed_method_version_id=v2.id,
            status="PROPOSED",
            summary="Prior run reusable learning",
            supporting_evidence_refs=[],
        )
        db.add(proposal); db.flush()
        db.add(
            LearningProposalDetail(
                learning_id=proposal.id,
                agent_run_id=old_run_id,
                source_method_version_id=v1.id,
                title="Prior run proposal",
                correction_input="Prior human correction input",
                applicability="Promise-to-Pay event handling",
                guardrails_json=[],
                validation_steps_json=[],
                model_output_json={},
            )
        )
        new_run = AgentRun(graph_run_id="CREED-R94-M05-LEARNING", issue_id=issue_id, status="COMPLETED")
        db.add(new_run); db.flush(); db.commit()
        new_graph_id = new_run.graph_run_id

    old_view = client.get(f"/api/v1/analysis-runs/{old_graph_id}/learning-proposal")
    assert old_view.status_code == 200
    assert old_view.json()["title"] == "Prior run proposal"

    new_view = client.get(f"/api/v1/analysis-runs/{new_graph_id}/learning-proposal")
    assert new_view.status_code == 200
    assert new_view.json() is None
