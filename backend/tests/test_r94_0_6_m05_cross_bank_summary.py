from __future__ import annotations

from pathlib import Path

from app.api.advanced import human_review, investigations as investigations_api
from app.domain.models import AgentRun, EvidenceDocument
from app.services import advanced
from app.services.advanced import build_configuration_change_summary, run_investigations, score_blast_radius
from test_r94_0_6_m03_variable_change_findings import _add_test_evidence, _set_variable_change_issue
from test_r94_m01_abom_evidence_routing import _seed_ui_style_abom


def test_cross_bank_summary_identifies_remediation_targets_and_survives_human_review(tmp_path: Path, monkeypatch):
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

            _add_test_evidence(
                db,
                ids["implementations"]["Atlas Bank"],
                "TEST-ATLAS-PTP-R1",
                "duplicate_suppression = false. Recorded result: FAIL for duplicate replay.",
            )
            _add_test_evidence(
                db,
                ids["implementations"]["Nova Finance"],
                "TEST-NOVA-PTP-R1",
                "Recorded result: PASS. Duplicate replay is suppressed by documented protection.",
            )
            db.commit()

            score_blast_radius(db, run)
            run_investigations(db, run)

            payload = investigations_api(run.graph_run_id, db)
            summary = payload["configuration_change_summary"]
            assert summary is not None
            assert summary["variable"] == "duplicate_suppression"
            assert summary["requested_state"] == "ENABLED"
            assert summary["candidate_count"] == 3
            assert summary["change_required_count"] == 2
            assert summary["already_protected_count"] == 1
            assert summary["already_matching_count"] == 0
            assert summary["reconciliation_required_count"] == 0

            remediation_clients = {item["client_name"] for item in summary["remediation_targets"]}
            assert remediation_clients == {"Atlas Bank", "Meridian Bank"}
            assert {item["client_name"] for item in summary["already_protected"]} == {"Nova Finance"}
            assert all(row["client_name"] for row in payload["results"])

            review_payload = human_review(run.graph_run_id, db)
            assert review_payload["configuration_change_summary"] == summary
    finally:
        engine.dispose()


def test_cross_bank_summary_fails_closed_for_mixed_configuration_requests():
    rows = [
        {
            "implementation_id": "impl-a",
            "implementation_name": "Implementation A",
            "client_name": "Bank A",
            "configuration_comparison": {
                "variable": "duplicate_suppression",
                "requested_state": "ENABLED",
                "requested_value": "true",
                "current_state": "DISABLED",
                "technical_result": "CHANGE_REVIEW_REQUIRED",
            },
        },
        {
            "implementation_id": "impl-b",
            "implementation_name": "Implementation B",
            "client_name": "Bank B",
            "configuration_comparison": {
                "variable": "retry_window_seconds",
                "requested_state": "ENABLED",
                "requested_value": "60",
                "current_state": "UNKNOWN",
                "technical_result": "EVIDENCE_RECONCILIATION_REQUIRED",
            },
        },
    ]
    assert build_configuration_change_summary(rows) is None
