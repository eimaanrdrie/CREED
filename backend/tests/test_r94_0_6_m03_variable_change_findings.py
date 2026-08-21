from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.domain.models import (
    AgentRun,
    DependencyEdge,
    EvidenceDocument,
    Finding,
    Implementation,
    SupportIssue,
)
from app.services import advanced
from app.services.advanced import (
    ConfigurationChangeRequest,
    _structured_configuration_change_output,
    run_investigations,
    score_blast_radius,
)
from test_r94_m01_abom_evidence_routing import _seed_ui_style_abom


def _set_variable_change_issue(db, run: AgentRun) -> SupportIssue:
    issue = db.get(SupportIssue, run.issue_id)
    assert issue is not None
    issue.external_ticket_id = "SUP-PTP-CONFIG-M03"
    issue.title = "Enable duplicate suppression for Atlas Promise-to-Pay events"
    issue.description = (
        "Atlas Bank requests that the `duplicate_suppression` configuration for Promise-to-Pay event processing "
        "be changed from `false` to `true`. Please assess whether the same configuration is used by any other "
        "registered Promise-to-Pay implementations using the same delivery method, identify their current control "
        "state, and determine which implementations also require the change."
    )
    issue.issue_type = "CHANGE_REQUEST"
    issue.severity = "HIGH"
    db.flush()
    return issue


def _add_test_evidence(db, impl_id: str, title: str, text: str) -> EvidenceDocument:
    doc = EvidenceDocument(
        source="LOCAL_REPOSITORY",
        title=title,
        original_filename=f"{title}.pdf",
        document_type="TEST",
        version="1.0",
        content_hash=f"hash-{title}",
        parse_status="PARSED",
        extracted_text=text,
        char_count=len(text),
        index_status="INDEXED",
    )
    db.add(doc)
    db.flush()
    db.add(
        DependencyEdge(
            source_type="Implementation",
            source_id=impl_id,
            target_type="EvidenceDocument",
            target_id=doc.id,
            relationship="SUPPORTED_BY",
            confidence=1.0,
            evidence_document_id=doc.id,
        )
    )
    db.flush()
    return doc


def test_real_repository_wording_maps_to_cross_bank_change_findings(tmp_path: Path, monkeypatch):
    """Exact M03 acceptance story using the mixed wording in the supplied repository.

    Atlas expresses the control across CFG + TEST, Meridian uses a table-style False,
    and Nova documents protection + a passing replay test. Known candidate state must
    be mapped deterministically without asking Qwen to adjudicate the scalar/control
    comparison.
    """

    engine, factory, ids = _seed_ui_style_abom(tmp_path)
    try:
        settings = advanced.get_settings()
        monkeypatch.setattr(settings, "investigation_use_heuristic_fast_path", False)
        monkeypatch.setattr(settings, "investigation_top_k", 3)
        monkeypatch.setattr(
            advanced,
            "get_ollama_runtime",
            lambda: (_ for _ in ()).throw(AssertionError("Qwen must not adjudicate a resolved variable-change state")),
        )

        with factory() as db:
            run = db.get(AgentRun, ids["run"])
            assert run is not None
            _set_variable_change_issue(db, run)

            atlas_cfg = db.get(EvidenceDocument, ids["documents"]["Atlas Bank"])
            meridian_cfg = db.get(EvidenceDocument, ids["documents"]["Meridian Bank"])
            nova_cfg = db.get(EvidenceDocument, ids["documents"]["Nova Finance"])
            assert atlas_cfg and meridian_cfg and nova_cfg

            atlas_cfg.extracted_text = (
                "The baseline does not document an explicit duplicate-event or idempotency-key guard ahead of "
                "the PTP state mutation path. No explicit idempotency-key guard is documented in this baseline."
            )
            meridian_cfg.extracted_text = (
                "Duplicate Suppression\nFalse\nIdempotency Key Required\nFalse\n"
                "This configuration does not enable duplicate suppression."
            )
            nova_cfg.extracted_text = (
                "Replay Protection\nDocumented idempotency / duplicate-suppression protection\n"
                "Duplicate suppression\nDocumented"
            )
            for doc in (atlas_cfg, meridian_cfg, nova_cfg):
                doc.char_count = len(doc.extracted_text or "")

            atlas_test = _add_test_evidence(
                db,
                ids["implementations"]["Atlas Bank"],
                "TEST-ATLAS-PTP-R1",
                "Recorded result: FAIL. Replaying the same accepted Promise-to-Pay event caused an additional "
                "state transition. CFG-ATLAS-PTP-01 records duplicate_suppression = false for Atlas.",
            )
            _add_test_evidence(
                db,
                ids["implementations"]["Meridian Bank"],
                "TEST-MERIDIAN-PTP-R1",
                "No dedicated duplicate replay/idempotency test is present in the current regression pack.",
            )
            nova_test = _add_test_evidence(
                db,
                ids["implementations"]["Nova Finance"],
                "TEST-NOVA-PTP-R1",
                "Recorded result: PASS. The duplicate replay test passed with documented idempotency / "
                "duplicate-suppression protection.",
            )
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

            assert "current state as DISABLED" in atlas["statement"]
            assert "requested target is ENABLED" in atlas["statement"]
            assert "current state as DISABLED" in meridian["statement"]
            assert "current state as PROTECTED" in nova["statement"]
            assert "does not fabricate a literal persisted true value" in nova["statement"]

            assert atlas_test.id in atlas["evidence_refs"]
            assert nova_cfg.id in nova["evidence_refs"]
            assert nova_test.id in nova["evidence_refs"]
            assert atlas["confidence"] >= 0.9
            assert meridian["confidence"] >= 0.9
            assert nova["confidence"] >= 0.9

            findings = db.scalars(select(Finding)).all()
            assert len(findings) == 3
            assert all(item.finding_type != "INSUFFICIENT_EVIDENCE" for item in findings)
    finally:
        engine.dispose()


def _doc(title: str, text: str) -> EvidenceDocument:
    return EvidenceDocument(
        id=title[:36],
        title=title,
        original_filename=f"{title}.pdf",
        document_type="CONFIGURATION",
        version="1.0",
        source="LOCAL_REPOSITORY",
        content_hash=f"hash-{title}",
        extracted_text=text,
        char_count=len(text),
        parse_status="PARSED",
    )


def _impl() -> Implementation:
    return Implementation(
        id="impl-m03",
        client_id="client-m03",
        product_id="product-m03",
        module_id="module-m03",
        name="Example PTP Implementation",
        release_version="R1",
        status="ACTIVE",
    )


def test_true_request_accepts_protected_without_fabricating_literal_true():
    change = ConfigurationChangeRequest(variable="duplicate_suppression", requested_value="true")
    out = _structured_configuration_change_output(
        change,
        _impl(),
        [_doc("CFG-NOVA", "Duplicate suppression protection is documented for the current implementation.")],
    )
    assert out is not None
    assert out.finding_type == "NO_SUPPORTING_EVIDENCE_OF_IMPACT"
    assert "PROTECTED" in out.statement
    assert "does not fabricate" in out.statement


def test_false_request_requires_review_when_current_state_is_protected():
    change = ConfigurationChangeRequest(variable="duplicate_suppression", requested_value="false")
    out = _structured_configuration_change_output(
        change,
        _impl(),
        [_doc("CFG-NOVA", "Duplicate suppression protection is documented for the current implementation.")],
    )
    assert out is not None
    assert out.finding_type == "POTENTIALLY_AFFECTED"
    assert "current state as PROTECTED" in out.statement
    assert "requested target is DISABLED" in out.statement


def test_real_fact_conflict_is_the_only_boolean_path_that_remains_insufficient():
    change = ConfigurationChangeRequest(variable="duplicate_suppression", requested_value="true")
    out = _structured_configuration_change_output(
        change,
        _impl(),
        [
            _doc("CFG-A", "duplicate_suppression = false"),
            _doc("CFG-B", "duplicate_suppression = true"),
        ],
    )
    assert out is not None
    assert out.finding_type == "INSUFFICIENT_EVIDENCE"
    assert "CONFLICTING_EXPLICIT_SCALARS" in out.statement
    assert out.confidence == 0.0
