from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.api.advanced import ReviewDecision, ReviewRequest, human_resume, investigations as investigations_api
from app.domain.models import AgentRun, EvidenceDocument, HumanAuthority, HumanDecision
from app.services import advanced, analysis_runs
from app.services.advanced import assess_human_decision_consistency, run_investigations, score_blast_radius
from test_r94_0_6_m03_variable_change_findings import _add_test_evidence, _set_variable_change_issue
from test_r94_m01_abom_evidence_routing import _seed_ui_style_abom


def _comparison(result: str) -> dict:
    return {
        "variable": "duplicate_suppression",
        "requested_value": "true",
        "requested_state": "ENABLED",
        "current_state": "DISABLED" if result == "CHANGE_REVIEW_REQUIRED" else "PROTECTED",
        "technical_result": result,
        "deterministic": True,
    }


def test_consistency_guard_flags_only_clear_deterministic_contradictions():
    change = _comparison("CHANGE_REVIEW_REQUIRED")
    protected = _comparison("ALREADY_PROTECTED")

    assert assess_human_decision_consistency(change, "AFFECTED")["status"] == "ALIGNED_WITH_TECHNICAL_ADVISORY"
    mismatch = assess_human_decision_consistency(change, "NOT_AFFECTED")
    assert mismatch["contradiction"] is True
    assert mismatch["requires_explicit_rationale"] is True
    assert mismatch["minimum_rationale_chars"] == 24

    reverse = assess_human_decision_consistency(protected, "AFFECTED")
    assert reverse["contradiction"] is True
    assert assess_human_decision_consistency(protected, "NOT_AFFECTED")["contradiction"] is False
    assert assess_human_decision_consistency(change, "NEEDS_MORE_INVESTIGATION")["status"] == "DEFERRED_FOR_MORE_INVESTIGATION"


def test_contradicting_human_decision_requires_explicit_rationale_and_is_preserved(tmp_path: Path, monkeypatch):
    engine, factory, ids = _seed_ui_style_abom(tmp_path)
    try:
        settings = advanced.get_settings()
        monkeypatch.setattr(settings, "investigation_use_heuristic_fast_path", False)
        monkeypatch.setattr(settings, "investigation_top_k", 3)
        monkeypatch.setattr(
            advanced,
            "get_ollama_runtime",
            lambda: (_ for _ in ()).throw(AssertionError("Resolved configuration comparison must not require Qwen")),
        )
        monkeypatch.setattr(analysis_runs, "langgraph_runtime_available", lambda: (True, None))
        monkeypatch.setattr(analysis_runs, "resume_analysis_run", lambda **kwargs: {"status": "COMPLETED"})

        with factory() as db:
            run = db.get(AgentRun, ids["run"])
            assert run is not None
            _set_variable_change_issue(db, run)

            atlas_cfg = db.get(EvidenceDocument, ids["documents"]["Atlas Bank"])
            meridian_cfg = db.get(EvidenceDocument, ids["documents"]["Meridian Bank"])
            nova_cfg = db.get(EvidenceDocument, ids["documents"]["Nova Finance"])
            assert atlas_cfg and meridian_cfg and nova_cfg
            atlas_cfg.extracted_text = "This configuration does not enable duplicate suppression."
            meridian_cfg.extracted_text = "Duplicate Suppression\nFalse\nThis configuration does not enable duplicate suppression."
            nova_cfg.extracted_text = "Duplicate suppression protection is documented for the current implementation."
            _add_test_evidence(db, ids["implementations"]["Atlas Bank"], "TEST-ATLAS-PTP-R1", "duplicate_suppression = false. Recorded result: FAIL for duplicate replay.")
            _add_test_evidence(db, ids["implementations"]["Nova Finance"], "TEST-NOVA-PTP-R1", "Recorded result: PASS. Duplicate replay is suppressed by documented protection.")
            db.add(HumanAuthority(
                principal="reviewer@creed.local",
                display_name="Decision Reviewer",
                role_title="Transformation Assurance Reviewer",
                active=True,
                can_submit_human_decision=True,
                can_approve_learning=False,
                can_authorize_recall=False,
            ))
            db.commit()

            score_blast_radius(db, run)
            run_investigations(db, run)
            payload = investigations_api(run.graph_run_id, db)
            rows = {row["client_name"]: row for row in payload["results"]}
            assert rows["Atlas Bank"]["configuration_comparison"]["technical_result"] == "CHANGE_REVIEW_REQUIRED"
            assert rows["Nova Finance"]["configuration_comparison"]["technical_result"] == "ALREADY_PROTECTED"

            short = ReviewRequest(
                reviewer="reviewer@creed.local",
                decisions=[
                    ReviewDecision(investigation_id=rows["Atlas Bank"]["id"], decision="NOT_AFFECTED", reason="Override"),
                    ReviewDecision(investigation_id=rows["Meridian Bank"]["id"], decision="AFFECTED", reason="Configuration requires the requested change."),
                    ReviewDecision(investigation_id=rows["Nova Finance"]["id"], decision="NOT_AFFECTED", reason="Existing protection already satisfies the requested control."),
                ],
            )
            with pytest.raises(HTTPException) as exc:
                human_resume(run.graph_run_id, short, "reviewer@creed.local", db)
            assert exc.value.status_code == 422
            assert exc.value.detail == "TECHNICAL_ADVISORY_CONTRADICTION_RATIONALE_REQUIRED"
            db.rollback()

            explicit = ReviewRequest(
                reviewer="reviewer@creed.local",
                decisions=[
                    ReviewDecision(
                        investigation_id=rows["Atlas Bank"]["id"],
                        decision="NOT_AFFECTED",
                        reason="Human reviewer accepts a documented compensating control outside this technical comparison.",
                    ),
                    ReviewDecision(investigation_id=rows["Meridian Bank"]["id"], decision="AFFECTED", reason="Configuration requires the requested change."),
                    ReviewDecision(investigation_id=rows["Nova Finance"]["id"], decision="NOT_AFFECTED", reason="Existing protection already satisfies the requested control."),
                ],
            )
            response = human_resume(run.graph_run_id, explicit, "reviewer@creed.local", db)
            assert response["status"] == "COMPLETED"

            decisions = db.scalars(select(HumanDecision)).all()
            assert len(decisions) == 3
            atlas_decision = next(item for item in decisions if item.investigation_id == rows["Atlas Bank"]["id"])
            consistency = atlas_decision.metadata_json["decision_consistency"]
            assert consistency["status"] == "CONTRADICTS_TECHNICAL_ADVISORY"
            assert consistency["contradiction"] is True
            assert consistency["technical_result"] == "CHANGE_REVIEW_REQUIRED"

            db.expire_all()
            after = investigations_api(run.graph_run_id, db)
            after_rows = {row["client_name"]: row for row in after["results"]}
            persisted = after_rows["Atlas Bank"]["human_decision"]["decision_consistency"]
            assert persisted["contradiction"] is True
            assert persisted["human_decision"] == "NOT_AFFECTED"
    finally:
        engine.dispose()
