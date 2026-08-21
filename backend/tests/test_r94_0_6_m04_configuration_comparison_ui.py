from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.api.advanced import investigations as investigations_api
from app.domain.models import AgentRun, EvidenceDocument, InvestigationDetail
from app.services import advanced
from app.services.advanced import run_investigations, score_blast_radius
from test_r94_0_6_m03_variable_change_findings import _add_test_evidence, _set_variable_change_issue
from test_r94_m01_abom_evidence_routing import _seed_ui_style_abom


def test_configuration_comparison_persists_and_reaches_human_review_payload(tmp_path: Path, monkeypatch):
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
            direct = run_investigations(db, run)
            by_impl = {row["implementation_id"]: row for row in direct["results"]}

            atlas = by_impl[ids["implementations"]["Atlas Bank"]]
            nova = by_impl[ids["implementations"]["Nova Finance"]]
            assert atlas["configuration_comparison"]["current_state"] == "DISABLED"
            assert atlas["configuration_comparison"]["requested_state"] == "ENABLED"
            assert atlas["configuration_comparison"]["technical_result"] == "CHANGE_REVIEW_REQUIRED"
            assert nova["configuration_comparison"]["current_state"] == "PROTECTED"
            assert nova["configuration_comparison"]["technical_result"] == "ALREADY_PROTECTED"

            details = db.scalars(select(InvestigationDetail).where(InvestigationDetail.agent_run_id == run.id)).all()
            assert len(details) == 3
            assert all((detail.model_output_json or {}).get("configuration_comparison") for detail in details)

            api_payload = investigations_api(run.graph_run_id, db)
            api_by_impl = {row["implementation_id"]: row for row in api_payload["results"]}
            assert api_by_impl[ids["implementations"]["Atlas Bank"]]["configuration_comparison"]["technical_result"] == "CHANGE_REVIEW_REQUIRED"
            assert api_by_impl[ids["implementations"]["Nova Finance"]]["configuration_comparison"]["technical_result"] == "ALREADY_PROTECTED"
    finally:
        engine.dispose()
