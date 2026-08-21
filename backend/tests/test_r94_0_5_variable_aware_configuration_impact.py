from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.domain.models import AgentRun, AnalysisEvidenceHit, EvidenceDocument, Finding, SupportIssue
from app.services import advanced
from app.services.advanced import _extract_configuration_change_request, run_investigations, score_blast_radius
from test_r94_m01_abom_evidence_routing import _seed_ui_style_abom


def _set_variable_change_issue(db, run: AgentRun) -> SupportIssue:
    issue = db.get(SupportIssue, run.issue_id)
    assert issue is not None
    issue.external_ticket_id = "SUP-PTP-CONFIG-001"
    issue.title = "Enable duplicate suppression for Atlas Promise-to-Pay events"
    issue.description = (
        "Atlas Bank requests that the `duplicate_suppression` configuration for Promise-to-Pay event processing "
        "be changed from `false` to `true` after repeated network retries were found to re-submit the same event "
        "to the state transition handler. Please assess whether the same configuration is used by any other "
        "registered Promise-to-Pay implementations using the same delivery method and identify which "
        "implementations also require this configuration change."
    )
    issue.issue_type = "CHANGE_REQUEST"
    issue.severity = "HIGH"
    db.flush()
    return issue


def test_variable_change_uses_full_authoritative_config_and_never_false_insufficient(tmp_path: Path, monkeypatch):
    """Exact regression for the R94.0.4 screenshots.

    Discovery/routing finds Atlas, Meridian and Nova. Retrieval snippets are deliberately
    truncated, but the authoritative CFG documents contain exact values. R94.0.5 must
    compare those full persisted values deterministically instead of asking Qwen to infer
    from snippets, so no candidate is marked INSUFFICIENT_EVIDENCE.
    """
    engine, factory, ids = _seed_ui_style_abom(tmp_path)
    try:
        settings = advanced.get_settings()
        monkeypatch.setattr(settings, "investigation_use_heuristic_fast_path", False)
        monkeypatch.setattr(settings, "investigation_top_k", 3)

        # If the deterministic configuration path is correct, Investigation does not need
        # a Qwen call to decide an exact scalar equality comparison.
        monkeypatch.setattr(advanced, "get_ollama_runtime", lambda: (_ for _ in ()).throw(AssertionError("Qwen should not adjudicate exact config equality")))

        with factory() as db:
            run = db.get(AgentRun, ids["run"])
            assert run is not None
            _set_variable_change_issue(db, run)

            # Reproduce the user's failure mode: discovery excerpts do not contain the
            # complete duplicate_suppression line even though Knowledge does.
            for hit in db.scalars(select(AnalysisEvidenceHit).where(AnalysisEvidenceHit.agent_run_id == run.id)).all():
                hit.excerpt = "# CFG-ATLAS-PTP-01\nmethod_version = PTP-EVENT-v1\nidempotency_key_required = false\ndu"
            db.commit()

            impact = score_blast_radius(db, run)
            assert len(impact["results"]) == 3

            result = run_investigations(db, run)
            assert result["result_count"] == 3
            by_impl = {row["implementation_id"]: row for row in result["results"]}

            atlas = by_impl[ids["implementations"]["Atlas Bank"]]
            meridian = by_impl[ids["implementations"]["Meridian Bank"]]
            nova = by_impl[ids["implementations"]["Nova Finance"]]

            assert atlas["finding_type"] == "POTENTIALLY_AFFECTED"
            assert meridian["finding_type"] == "POTENTIALLY_AFFECTED"
            assert nova["finding_type"] == "NO_SUPPORTING_EVIDENCE_OF_IMPACT"
            assert {row["finding_type"] for row in result["results"]}.isdisjoint({"INSUFFICIENT_EVIDENCE"})

            assert "duplicate_suppression=false" in atlas["statement"]
            assert "requested value is true" in atlas["statement"]
            assert "duplicate_suppression=false" in meridian["statement"]
            assert "duplicate_suppression=true" in nova["statement"]
            assert "already matches" in nova["statement"]

            assert ids["documents"]["Atlas Bank"] in atlas["evidence_refs"]
            assert ids["documents"]["Meridian Bank"] in meridian["evidence_refs"]
            assert ids["documents"]["Nova Finance"] in nova["evidence_refs"]
            assert atlas["confidence"] == 0.99
            assert meridian["confidence"] == 0.99
            assert nova["confidence"] == 0.99

            findings = db.scalars(select(Finding)).all()
            assert len(findings) == 3
            assert all(f.finding_type != "INSUFFICIENT_EVIDENCE" for f in findings)
    finally:
        engine.dispose()


def test_configuration_change_parser_supports_generic_scalar_key():
    issue = SupportIssue(
        external_ticket_id="SUP-CFG-002",
        client_id="client-1",
        title="Increase retry window",
        description="Change `retry_window_seconds` from `30` to `60` for the affected implementation.",
        issue_type="CHANGE_REQUEST",
        severity="MEDIUM",
        status="OPEN",
    )
    parsed = _extract_configuration_change_request(issue)
    assert parsed is not None
    assert parsed.variable == "retry_window_seconds"
    assert parsed.previous_value == "30"
    assert parsed.requested_value == "60"


def test_conflicting_authoritative_values_remain_fail_closed(tmp_path: Path, monkeypatch):
    """R94.0.5 does not hide genuine evidence conflicts just to avoid an insufficient label."""
    engine, factory, ids = _seed_ui_style_abom(tmp_path)
    try:
        settings = advanced.get_settings()
        monkeypatch.setattr(settings, "investigation_use_heuristic_fast_path", False)
        monkeypatch.setattr(settings, "investigation_top_k", 3)
        with factory() as db:
            run = db.get(AgentRun, ids["run"])
            assert run is not None
            _set_variable_change_issue(db, run)
            atlas_doc = db.get(EvidenceDocument, ids["documents"]["Atlas Bank"])
            assert atlas_doc is not None
            atlas_doc.extracted_text += "\nduplicate_suppression = true\n"
            db.commit()

            score_blast_radius(db, run)
            result = run_investigations(db, run)
            by_impl = {row["implementation_id"]: row for row in result["results"]}
            atlas = by_impl[ids["implementations"]["Atlas Bank"]]
            assert atlas["finding_type"] == "INSUFFICIENT_EVIDENCE"
            assert "conflicting values" in atlas["statement"]
    finally:
        engine.dispose()
