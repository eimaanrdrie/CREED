from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.domain.models import (
    AgentRun, AgentStep, AnalysisEvidenceHit, AnalysisImpactAssessment, Client,
    DocumentChunk, EvidenceDocument, Finding, HumanDecision, Implementation,
    Investigation, InvestigationDetail, IssueUnderstanding, SupportIssue,
)
from app.services.advanced import audit_trace
from app.services.demo import reset_demo


def context(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path/'audit-r08.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def test_audit_trace_reconstructs_glass_box_run(tmp_path):
    engine, factory = context(tmp_path)
    with factory() as db:
        reset_demo(db)
        atlas = db.scalar(select(Client).where(Client.name == "Atlas Bank"))
        impl = db.scalar(select(Implementation).where(Implementation.client_id == atlas.id))
        doc = db.scalar(select(EvidenceDocument).where(EvidenceDocument.title == "FSD-COL-104"))
        chunk = db.scalar(select(DocumentChunk).where(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index))

        issue = SupportIssue(
            external_ticket_id="SUP-R08-1", client_id=atlas.id, title="Duplicate PTP replay",
            description="The same Promise-to-Pay event was replayed after a retry.",
            issue_type="BUG", severity="HIGH", status="WAITING_HUMAN",
        )
        db.add(issue); db.flush()
        run = AgentRun(graph_run_id="CREED-R08-TRACE", issue_id=issue.id, status="WAITING_HUMAN", input_summary=issue.title)
        db.add(run); db.flush()
        db.add(AgentStep(agent_run_id=run.id, agent_name="retrieval_agent", status="COMPLETED", sequence=20,
                         input_summary="Search evidence", output_summary="1 evidence item",
                         metadata_json={"display_name": "Retrieval Agent"}))
        understanding = IssueUnderstanding(
            issue_id=issue.id, qwen_run_id="QWEN-R08-UNDERSTAND", input_hash="a"*64,
            configured_model="qwen3.5:9b", actual_model="qwen3.5:9b", duration_ms=410.0,
            prompt_eval_count=120, eval_count=44, client_name="Atlas Bank", product="Collections",
            module="Promise-to-Pay", issue_type="BUG", summary="Duplicate PTP replay after retry.",
            suspected_function="PTP event handler", keywords_json=["PTP", "replay"], severity="HIGH",
            confidence=0.91, model_output_json={"summary": "Duplicate PTP replay after retry."}, status="AI_GENERATED",
        )
        db.add(understanding)
        db.add(AnalysisEvidenceHit(
            agent_run_id=run.id, issue_id=issue.id, document_id=doc.id, chunk_id=chunk.id, rank=1,
            matched_queries_json=["PTP replay"], base_score=.8, query_coverage_bonus=0, issue_link_boost=0,
            final_score=.8, semantic_score=.7, keyword_score=.9, metadata_score=.5,
            citation="FSD-COL-104", excerpt=chunk.text[:200], embedding_model="qwen3-embedding:0.6b", embedding_degraded=False,
        ))
        db.add(AnalysisImpactAssessment(
            agent_run_id=run.id, issue_id=issue.id, implementation_id=impl.id, method_version_id=None,
            impact_score=.82, impact_band="REPORTED_SOURCE", reported_source=True,
            signals_json={"method_version": 1.0}, weights_json={"method_version": .35},
            explanation_json=[{"signal": "method_version", "contribution": .35}], evidence_refs_json=["FSD-COL-104"],
        ))
        inv = Investigation(issue_id=issue.id, implementation_id=impl.id, status="WAITING_HUMAN", risk_score=.82)
        db.add(inv); db.flush()
        finding = Finding(investigation_id=inv.id, finding_type="POTENTIALLY_AFFECTED", statement="Evidence supports review.", confidence=.86, evidence_refs=[doc.id])
        db.add(finding); db.flush()
        db.add(InvestigationDetail(
            investigation_id=inv.id, agent_run_id=run.id, finding_id=finding.id, qwen_run_id="QWEN-R08-INVESTIGATE",
            configured_model="qwen3.5:9b", actual_model="qwen3.5:9b", duration_ms=920.0,
            prompt_eval_count=240, eval_count=72, evidence_observations_json=[], missing_evidence_json=[],
            model_output_json={"finding_type": "POTENTIALLY_AFFECTED"}, evidence_validation_status="VALID",
        ))
        db.add(HumanDecision(investigation_id=inv.id, decision="AFFECTED", reviewer="Assurance Lead", reason="Evidence supports remediation."))
        db.commit()

        trace = audit_trace(db, "CREED-R08-TRACE")
        assert trace["scope"]["mode"] == "RUN"
        assert trace["scope"]["issue"]["ticket"] == "SUP-R08-1"
        assert trace["summary"]["qwen_calls"] == 2
        assert trace["summary"]["evidence_accesses"] == 1
        assert trace["summary"]["impact_assessments"] == 1
        assert trace["summary"]["human_decisions"] == 1
        assert {row["category"] for row in trace["timeline"]} >= {"ISSUE", "AGENT", "AI", "EVIDENCE", "IMPACT", "HUMAN"}
        assert trace["evidence"][0]["content_hash"] == doc.content_hash
        assert all("chain" not in str(row).lower() for row in trace["qwen_calls"])
    engine.dispose()
