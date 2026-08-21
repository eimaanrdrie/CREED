from __future__ import annotations

from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.domain.models import AgentRun, AgentStep, AuditEvent, SupportIssue
import app.services.analysis_runs as analysis_runs


def _factory(tmp_path: Path):
    db_path = tmp_path / "r94_m02.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False), db_path


def _seed_zero_case_run(factory):
    with factory() as db:
        issue = SupportIssue(
            external_ticket_id="SUP-R94-M02",
            title="No routed implementation",
            description="Evidence was retrieved but no implementation investigation case was persisted.",
            issue_type="BUG",
            severity="HIGH",
            status="ANALYSING",
        )
        db.add(issue)
        db.flush()
        run = AgentRun(
            graph_run_id="CREED-R94-M02-ZERO",
            issue_id=issue.id,
            status="RUNNING",
            input_summary=issue.title,
        )
        db.add(run)
        db.flush()
        step = AgentStep(
            agent_run_id=run.id,
            agent_name="human_review_boundary",
            status="QUEUED",
            sequence=70,
            input_summary="Pause for human review and authority",
            metadata_json={"display_name": "Human Review", "runtime_source": "LANGGRAPH_NODE"},
        )
        db.add(step)
        db.commit()
        return issue.id, run.id, step.id


def test_zero_investigations_skip_human_review_without_waiting(tmp_path: Path):
    engine, factory, _ = _factory(tmp_path)
    try:
        issue_id, run_id, step_id = _seed_zero_case_run(factory)
        node = analysis_runs._instrument(
            factory,
            run_id,
            "human_review_boundary",
            analysis_runs._human_review_boundary_node(factory, run_id),
        )
        result = node({"run_id": "CREED-R94-M02-ZERO", "investigations": []})

        assert result["review_boundary"] == "SKIPPED_NO_CASES"
        with factory() as db:
            run = db.get(AgentRun, run_id)
            issue = db.get(SupportIssue, issue_id)
            step = db.get(AgentStep, step_id)
            assert run is not None and run.status == "RUNNING"
            assert issue is not None and issue.status == "ANALYSING"
            assert step is not None and step.status == "SKIPPED"
            assert step.metadata_json["skip_reason"] == "NO_INVESTIGATION_CASES"
            assert step.metadata_json["interrupt_executed"] is False
            assert db.scalar(
                select(AuditEvent).where(
                    AuditEvent.object_id == run_id,
                    AuditEvent.action == "HUMAN_REVIEW_SKIPPED_NO_CASES",
                )
            ) is not None
            assert db.scalar(
                select(AuditEvent).where(
                    AuditEvent.object_id == run_id,
                    AuditEvent.action == "HUMAN_REVIEW_CHECKPOINT_SAVED",
                )
            ) is None
    finally:
        engine.dispose()


def test_zero_case_run_completes_without_waiting_and_keeps_issue_open(tmp_path: Path, monkeypatch):
    engine, factory, db_path = _factory(tmp_path)
    try:
        issue_id, run_id, _ = _seed_zero_case_run(factory)

        class FakeGraph:
            def invoke(self, initial, config=None, durability=None):
                return {
                    **initial,
                    "candidate_implementations": [],
                    "investigations": [],
                    "review_boundary": "SKIPPED_NO_CASES",
                }

            def get_state(self, config):
                return SimpleNamespace(
                    next=(),
                    config={"configurable": {"checkpoint_id": "cp-r94-m02"}},
                )

        monkeypatch.setattr(analysis_runs, "langgraph_runtime_available", lambda: (True, None))
        monkeypatch.setattr(analysis_runs, "_build_graph", lambda *args, **kwargs: FakeGraph())

        # The CI/container used for source verification may not have LangGraph installed.
        # Provide only the import surface execute_analysis_run needs; the FakeGraph above
        # remains the execution subject of this finalization regression.
        langgraph_mod = ModuleType("langgraph")
        checkpoint_mod = ModuleType("langgraph.checkpoint")
        sqlite_mod = ModuleType("langgraph.checkpoint.sqlite")

        class DummySqliteSaver:
            def __init__(self, connection):
                self.connection = connection

        sqlite_mod.SqliteSaver = DummySqliteSaver
        monkeypatch.setitem(sys.modules, "langgraph", langgraph_mod)
        monkeypatch.setitem(sys.modules, "langgraph.checkpoint", checkpoint_mod)
        monkeypatch.setitem(sys.modules, "langgraph.checkpoint.sqlite", sqlite_mod)

        analysis_runs.execute_analysis_run(run_db_id=run_id, database_url=f"sqlite:///{db_path}")

        with factory() as db:
            run = db.get(AgentRun, run_id)
            issue = db.get(SupportIssue, issue_id)
            assert run is not None and run.status == "COMPLETED"
            assert "human review skipped" in (run.output_summary or "").lower()
            assert issue is not None and issue.status == "OPEN"
            audit = db.scalar(
                select(AuditEvent).where(
                    AuditEvent.object_id == run_id,
                    AuditEvent.action == "ANALYSIS_RUN_NO_REVIEW_CASES",
                )
            )
            assert audit is not None
            assert audit.metadata_json["candidate_count"] == 0
            assert audit.metadata_json["investigation_count"] == 0
            assert audit.metadata_json["human_review_skipped"] is True
            assert db.scalar(
                select(AuditEvent).where(
                    AuditEvent.object_id == run_id,
                    AuditEvent.action == "HUMAN_REVIEW_CHECKPOINT_SAVED",
                )
            ) is None
    finally:
        engine.dispose()
