from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.domain.models import AgentRun, Finding, HumanDecision, Investigation
from app.services.advanced import learning_readiness, run_investigations, score_blast_radius
from test_r94_m01_abom_evidence_routing import _seed_ui_style_abom


def test_ui_dependency_supporting_evidence_reaches_investigation_and_learning(tmp_path: Path, monkeypatch):
    """Regression for the R94 FINAL screenshot failure.

    The seed contains no Implementation -> EvidenceDocument edges. The only
    implementation-specific provenance is evidence_document_id on
    USES_METHOD_VERSION, exactly like Registry > Dependencies creates it.
    """
    engine, factory, ids = _seed_ui_style_abom(tmp_path)
    try:
        settings = get_settings()
        monkeypatch.setattr(settings, "investigation_use_heuristic_fast_path", True)
        monkeypatch.setattr(settings, "investigation_top_k", 3)

        with factory() as db:
            run = db.get(AgentRun, ids["run"])
            assert run is not None
            impact = score_blast_radius(db, run)
            assert len(impact["results"]) == 3

            investigation = run_investigations(db, run)
            assert investigation["result_count"] == 3
            assert all(item["evidence_refs"] for item in investigation["results"])
            assert all(item["finding_type"] != "INSUFFICIENT_EVIDENCE" for item in investigation["results"])

            investigations = db.scalars(
                select(Investigation).where(Investigation.agent_run_id == run.id).order_by(Investigation.id)
            ).all()
            assert len(investigations) == 3
            for inv in investigations:
                finding = db.scalar(select(Finding).where(Finding.investigation_id == inv.id))
                assert finding is not None
                assert finding.evidence_refs

            db.add(HumanDecision(
                investigation_id=investigations[0].id,
                decision="AFFECTED",
                reviewer="aisha.rahman@creed.example",
                reason="Reviewed persisted A-BOM supporting evidence.",
            ))
            run.status = "COMPLETED"
            db.commit()

            readiness = learning_readiness(db, run)
            assert readiness["supporting_evidence_count"] >= 1
            assert readiness["reason"] == "READY"
            assert readiness["eligible"] is True
    finally:
        engine.dispose()


def test_r94_0_1_default_investigation_coverage_is_three():
    assert Settings(_env_file=None).investigation_top_k == 3
