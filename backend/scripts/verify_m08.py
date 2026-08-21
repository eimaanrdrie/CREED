#!/usr/bin/env python3
from __future__ import annotations

import importlib.metadata
import sqlite3
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.domain.models import (
    AgentEvent, AgentRun, AgentStep, AuditEvent, Client, EvidenceDocument, Implementation,
    IssueEvidenceLink, IssueUnderstanding, Module, Product, SupportIssue, uuid_str,
)
from app.services.analysis_runs import create_analysis_run, execute_analysis_run, langgraph_runtime_available


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    available, reason = langgraph_runtime_available()
    if not available:
        fail(f"real LangGraph runtime is unavailable; M08 cannot pass acceptance. DETAIL: {reason}")

    print(f"LangGraph: {importlib.metadata.version('langgraph')}")
    print(f"Checkpoint SQLite: {importlib.metadata.version('langgraph-checkpoint-sqlite')}")

    with tempfile.TemporaryDirectory(prefix="creed-m08-") as tmp:
        db_path = Path(tmp) / "acceptance.db"
        database_url = f"sqlite:///{db_path}"
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        factory = sessionmaker(bind=engine, expire_on_commit=False)

        with factory() as db:
            atlas = Client(id=uuid_str(), name="Atlas Bank", client_type="BANK")
            meridian = Client(id=uuid_str(), name="Meridian Bank", client_type="BANK")
            nova = Client(id=uuid_str(), name="Nova Finance", client_type="FINANCIAL_INSTITUTION")
            product = Product(id=uuid_str(), name="Collections", description="Synthetic M08 product")
            module = Module(id=uuid_str(), product_id=product.id, name="Promise-to-Pay", description="Synthetic M08 module")
            db.add_all([atlas, meridian, nova, product, module]); db.flush()
            implementations = [
                Implementation(id=uuid_str(), client_id=c.id, product_id=product.id, module_id=module.id, name=f"{c.name} PTP", release_version="R1", status="ACTIVE")
                for c in (atlas, meridian, nova)
            ]
            issue = SupportIssue(
                id=uuid_str(), external_ticket_id="SUP-M08-VERIFY", client_id=atlas.id,
                title="Duplicate PTP event changes collection state",
                description="Atlas Bank reports duplicate Promise-to-Pay events changing collection state.",
                issue_type="BUG", severity="HIGH", status="OPEN",
            )
            evidence = EvidenceDocument(
                id=uuid_str(), source="LOCAL_DEMO", title="FSD-COL-104", document_type="FSD", version="1.0",
                content_hash="m08-verify-hash", extracted_text="Promise-to-Pay event processing specification.", char_count=45,
                parse_status="PARSED", index_status="INDEXED", chunk_count=1,
            )
            db.add_all([*implementations, issue, evidence]); db.flush()
            db.add(IssueEvidenceLink(id=uuid_str(), issue_id=issue.id, document_id=evidence.id, link_type="ATTACHMENT"))
            db.add(IssueUnderstanding(
                id=uuid_str(), issue_id=issue.id, qwen_run_id="QWEN-M07-VERIFIED", input_hash="a"*64,
                configured_model="qwen3.5:9b", actual_model="qwen3.5:9b", duration_ms=800,
                client_name="Atlas Bank", product="Collections", module="Promise-to-Pay", issue_type="BUG",
                summary="Duplicate Promise-to-Pay events can produce an incorrect collection state.",
                suspected_function="PTP event handling", keywords_json=["duplicate event", "PTP"], severity="HIGH",
                confidence=0.94, model_output_json={"product":"Collections","module":"Promise-to-Pay"}, status="AI_GENERATED",
            ))
            db.commit()
            run = create_analysis_run(db, issue)
            run_id = run.id
            graph_run_id = run.graph_run_id

        execute_analysis_run(run_db_id=run_id, database_url=database_url)

        with factory() as db:
            run = db.get(AgentRun, run_id)
            if run is None or run.status != "COMPLETED":
                fail(f"LangGraph run did not complete: {run.status if run else 'missing'} / {run.error if run else ''}")
            steps = db.scalars(select(AgentStep).where(AgentStep.agent_run_id == run_id).order_by(AgentStep.sequence)).all()
            expected = ["COMPLETED"] * 6 + ["SKIPPED"]
            actual = [s.status for s in steps]
            if actual != expected:
                fail(f"unexpected node statuses: {actual}")
            events = db.scalars(select(AgentEvent).where(AgentEvent.agent_run_id == run_id).order_by(AgentEvent.event_seq)).all()
            event_pairs = {(e.agent_name, e.status) for e in events}
            for step in steps[:6]:
                if (step.agent_name, "RUNNING") not in event_pairs or (step.agent_name, "COMPLETED") not in event_pairs:
                    fail(f"missing durable RUNNING/COMPLETED lifecycle for {step.agent_name}")
            if ("human_review_boundary", "SKIPPED") not in event_pairs:
                fail("M13 human boundary was not explicitly recorded as SKIPPED")
            impact = next(s for s in steps if s.agent_name == "impact_agent")
            if impact.metadata_json.get("candidate_count") != 3 or impact.metadata_json.get("scoring_performed") is not False:
                fail(f"M08 impact boundary incorrect: {impact.metadata_json}")
            audit = db.scalar(select(AuditEvent).where(AuditEvent.action == "ANALYSIS_RUN_COMPLETED", AuditEvent.object_id == run_id))
            if audit is None or not audit.metadata_json.get("checkpoint_id"):
                fail("LangGraph completion audit lacks persistent checkpoint proof")

        checkpoint_path = db_path.with_name(f"{db_path.stem}.langgraph-checkpoints.sqlite")
        if not checkpoint_path.exists():
            fail("persistent LangGraph checkpoint file was not created")
        conn = sqlite3.connect(checkpoint_path)
        try:
            tables = {r[0] for r in conn.execute("select name from sqlite_master where type='table'").fetchall()}
            if "checkpoints" not in tables:
                fail(f"checkpoint table not found; tables={sorted(tables)}")
            count = conn.execute("select count(*) from checkpoints where thread_id=?", (graph_run_id,)).fetchone()[0]
            if count < 2:
                fail(f"expected multiple persisted LangGraph checkpoints, found {count}")
        finally:
            conn.close()
            engine.dispose()

        print("PASS: actual LangGraph StateGraph executed all M08 nodes.")
        print("PASS: RUNNING/COMPLETED/SKIPPED lifecycle events persisted for SSE replay.")
        print("PASS: graph checkpoints persisted to SQLite and are addressable by graph_run_id/thread_id.")
        print("PASS: M08 kept retrieval, blast-radius scoring, investigation, and human interrupt inside their later-module boundaries.")
        print("PASS: M08 real LangGraph orchestration acceptance verified.")


if __name__ == "__main__":
    main()
