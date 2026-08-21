from __future__ import annotations

import json
from pathlib import Path

from app.core.config import Settings


ROOT = Path(__file__).resolve().parents[2]


def test_r9406_release_version_surfaces_are_aligned():
    assert Settings().app_version == "0.94.6"
    env = (ROOT / "backend/.env.example").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8"))

    assert "APP_VERSION=0.94.6" in env
    assert "APP_VERSION: 0.94.6" in compose
    assert package["version"] == "0.94.6"
    assert lock["version"] == "0.94.6"
    assert lock["packages"][""]["version"] == "0.94.6"


def test_m01_to_m07_are_sealed_as_approved_baselines_in_integrated_candidate():
    for index in range(1, 8):
        manifest_path = ROOT / f"R94_0_6_M{index:02d}_MANIFEST.json"
        assert manifest_path.exists(), manifest_path.name
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["status"] == "APPROVED_BASELINE", manifest_path.name
        assert manifest["approval"]["state"] == "USER_APPROVED", manifest_path.name

        test_matches = list((ROOT / "backend/tests").glob(f"test_r94_0_6_m{index:02d}_*.py"))
        assert test_matches, f"M{index:02d} regression missing"


def test_release_candidate_includes_operator_docs_and_truth_boundaries():
    runbook = ROOT / "CREED_R94_0_6_Exact_Data_Entry_and_Live_Demo_Runbook.pdf"
    markdown = (ROOT / "R94_FINAL_RUNBOOK.md").read_text(encoding="utf-8")
    notes = (ROOT / "R94_0_6_RELEASE_NOTES.md").read_text(encoding="utf-8")
    m08 = (ROOT / "R94_0_6_M08_NOTES.md").read_text(encoding="utf-8")

    assert runbook.exists() and runbook.stat().st_size > 50_000
    assert "R94.0.6 Structured configuration facts + cross-bank remediation addendum" in markdown
    assert "2 implementations require change" in markdown
    assert "Nova PTP Implementation" in markdown
    assert "Human Authority remains final" in m08
    assert "ALREADY PROTECTED" in notes
    assert "missing or contradictory evidence remains fail-closed" in notes


def test_m08_release_candidate_manifest_identity_and_truth_boundary():
    manifest = json.loads((ROOT / "R94_0_6_M08_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["release"] == "R94.0.6-M08-REV1"
    assert manifest["application_version"] == "0.94.6"
    assert manifest["status"] == "CANDIDATE_AWAITING_APPROVAL"
    assert manifest["approval"]["m01_to_m07"] == "USER_APPROVED"
    assert manifest["approval"]["m08"] == "AWAITING_USER_APPROVAL"
    assert manifest["verification"]["backend_total"]["passed"] == 173
    assert any("INSUFFICIENT_EVIDENCE" in item for item in manifest["truth_boundaries"])
