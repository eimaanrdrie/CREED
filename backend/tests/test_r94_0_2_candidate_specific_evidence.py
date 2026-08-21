from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.domain.models import (
    AgentRun,
    AnalysisEvidenceHit,
    DependencyEdge,
    DocumentChunk,
    EvidenceDocument,
    Finding,
    HumanDecision,
    Investigation,
)
from app.services.advanced import learning_readiness, run_investigations, score_blast_radius
from test_r94_m01_abom_evidence_routing import _seed_ui_style_abom


def _add_run_hit(db, run: AgentRun, doc: EvidenceDocument, rank: int) -> None:
    chunk = db.scalar(select(DocumentChunk).where(DocumentChunk.document_id == doc.id).limit(1))
    assert chunk is not None
    if db.scalar(select(AnalysisEvidenceHit).where(AnalysisEvidenceHit.agent_run_id == run.id, AnalysisEvidenceHit.document_id == doc.id)):
        return
    db.add(AnalysisEvidenceHit(
        agent_run_id=run.id,
        issue_id=run.issue_id,
        document_id=doc.id,
        chunk_id=chunk.id,
        rank=rank,
        matched_queries_json=["Promise-to-Pay retry replay"],
        base_score=0.8,
        final_score=0.8,
        semantic_score=0.8,
        keyword_score=0.8,
        metadata_score=0.0,
        citation=doc.title,
        excerpt=doc.extracted_text or "",
    ))


def test_legacy_missing_edge_evidence_is_bound_per_candidate(tmp_path: Path, monkeypatch):
    """Regression for the user's R94.0.1 runtime result: 3 candidates but 1/0/0 evidence.

    Atlas keeps normal USES_METHOD_VERSION supporting evidence. Meridian and Nova mimic
    legacy dependency rows whose evidence_document_id was never persisted. Their client-
    specific CFG documents exist in Knowledge and are retrieved in the current run.
    R94.0.2 must bind those documents to the matching candidate deterministically.
    """
    engine, factory, ids = _seed_ui_style_abom(tmp_path)
    try:
        settings = get_settings()
        monkeypatch.setattr(settings, "investigation_use_heuristic_fast_path", True)
        monkeypatch.setattr(settings, "investigation_top_k", 3)

        with factory() as db:
            run = db.get(AgentRun, ids["run"])
            assert run is not None

            # Reproduce a mixed legacy database: only Atlas retained edge provenance.
            for client_name in ["Meridian Bank", "Nova Finance"]:
                edge = db.scalar(select(DependencyEdge).where(
                    DependencyEdge.source_type == "Implementation",
                    DependencyEdge.source_id == ids["implementations"][client_name],
                    DependencyEdge.relationship == "USES_METHOD_VERSION",
                ))
                assert edge is not None
                edge.evidence_document_id = None
                doc = db.get(EvidenceDocument, ids["documents"][client_name])
                assert doc is not None
                _add_run_hit(db, run, doc, 2 if client_name == "Meridian Bank" else 3)
            db.commit()

            impact = score_blast_radius(db, run)
            assert len(impact["results"]) == 3

            investigation = run_investigations(db, run)
            assert investigation["result_count"] == 3
            by_impl = {row["implementation_id"]: row for row in investigation["results"]}
            for client_name in ["Atlas Bank", "Meridian Bank", "Nova Finance"]:
                row = by_impl[ids["implementations"][client_name]]
                assert row["evidence_refs"], client_name
                assert ids["documents"][client_name] in row["evidence_refs"], client_name

            invs = db.scalars(select(Investigation).where(Investigation.agent_run_id == run.id)).all()
            assert len(invs) == 3
            inv_by_impl = {inv.implementation_id: inv for inv in invs}
            db.add(HumanDecision(
                investigation_id=inv_by_impl[ids["implementations"]["Atlas Bank"]].id,
                decision="NOT_AFFECTED",
                reviewer="aisha.rahman@creed.example",
                reason="Reviewed candidate evidence.",
            ))
            for client_name in ["Meridian Bank", "Nova Finance"]:
                db.add(HumanDecision(
                    investigation_id=inv_by_impl[ids["implementations"][client_name]].id,
                    decision="AFFECTED",
                    reviewer="aisha.rahman@creed.example",
                    reason="Reviewed candidate evidence.",
                ))
            run.status = "COMPLETED"
            db.commit()

            readiness = learning_readiness(db, run)
            assert readiness["eligible"] is True
            assert readiness["reason"] == "READY"
            assert readiness["supporting_evidence_count"] >= 2
    finally:
        engine.dispose()


def test_not_affected_evidence_cannot_unlock_learning(tmp_path: Path, monkeypatch):
    """Evidence from NOT_AFFECTED cases must not satisfy the reusable-learning gate."""
    engine, factory, ids = _seed_ui_style_abom(tmp_path)
    try:
        settings = get_settings()
        monkeypatch.setattr(settings, "investigation_use_heuristic_fast_path", True)
        monkeypatch.setattr(settings, "investigation_top_k", 3)

        with factory() as db:
            run = db.get(AgentRun, ids["run"])
            assert run is not None

            # Make Meridian/Nova evidence unavailable and impossible to identity-match.
            for client_name in ["Meridian Bank", "Nova Finance"]:
                edge = db.scalar(select(DependencyEdge).where(
                    DependencyEdge.source_type == "Implementation",
                    DependencyEdge.source_id == ids["implementations"][client_name],
                    DependencyEdge.relationship == "USES_METHOD_VERSION",
                ))
                assert edge is not None
                edge.evidence_document_id = None
                doc = db.get(EvidenceDocument, ids["documents"][client_name])
                assert doc is not None
                doc.title = "GENERIC-DOC"
                doc.original_filename = None
            db.commit()

            score_blast_radius(db, run)
            run_investigations(db, run)
            invs = db.scalars(select(Investigation).where(Investigation.agent_run_id == run.id)).all()
            inv_by_impl = {inv.implementation_id: inv for inv in invs}

            db.add(HumanDecision(
                investigation_id=inv_by_impl[ids["implementations"]["Atlas Bank"]].id,
                decision="NOT_AFFECTED",
                reviewer="aisha.rahman@creed.example",
                reason="Atlas evidence does not support impact.",
            ))
            for client_name in ["Meridian Bank", "Nova Finance"]:
                db.add(HumanDecision(
                    investigation_id=inv_by_impl[ids["implementations"][client_name]].id,
                    decision="AFFECTED",
                    reviewer="aisha.rahman@creed.example",
                    reason="Affected, but no persisted evidence is available.",
                ))
            run.status = "COMPLETED"
            db.commit()

            atlas_finding = db.scalar(select(Finding).where(Finding.investigation_id == inv_by_impl[ids["implementations"]["Atlas Bank"]].id))
            assert atlas_finding is not None and atlas_finding.evidence_refs

            readiness = learning_readiness(db, run)
            assert readiness["eligible"] is False
            assert readiness["reason"] == "LEARNING_SUPPORTING_EVIDENCE_REQUIRED"
            assert readiness["supporting_evidence_count"] == 0
    finally:
        engine.dispose()
