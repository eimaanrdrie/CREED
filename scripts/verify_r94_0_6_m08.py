from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(text: str, needle: str, source: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: {source} missing {needle}")


def run_verifier(name: str) -> None:
    verifier = ROOT / "scripts" / name
    if not verifier.exists():
        raise SystemExit(f"FAIL: missing verifier {name}")
    completed = subprocess.run(
        [sys.executable, str(verifier)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode:
        print(completed.stdout, end="")
        raise SystemExit(f"FAIL: {name}")


def main() -> None:
    # Preserve the approved R94 final integration contract and the latest
    # R94.0.6 extraction/robustness contracts without recursively replaying
    # every post-final verifier chain inside this one verifier.
    for verifier in (
        "verify_r94_m12.py",
        "verify_r94_0_6_m07.py",
    ):
        run_verifier(verifier)

    for name in (
        "verify_r94_0_1_hotfix.py",
        "verify_r94_0_2_hotfix.py",
        "verify_r94_0_3_hotfix.py",
        "verify_r94_0_4_hotfix.py",
        "verify_r94_0_5_hotfix.py",
    ):
        if not (ROOT / "scripts" / name).exists():
            raise SystemExit(f"FAIL: missing prior hotfix verifier {name}")

    config = (ROOT / "backend/app/core/config.py").read_text(encoding="utf-8")
    env = (ROOT / "backend/.env.example").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8"))
    advanced = (ROOT / "backend/app/services/advanced.py").read_text(encoding="utf-8")
    facts = (ROOT / "backend/app/services/configuration_facts.py").read_text(encoding="utf-8")
    ui = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
    runbook = (ROOT / "R94_FINAL_RUNBOOK.md").read_text(encoding="utf-8")
    release_notes = (ROOT / "R94_0_6_RELEASE_NOTES.md").read_text(encoding="utf-8")
    m08_notes = (ROOT / "R94_0_6_M08_NOTES.md").read_text(encoding="utf-8")
    m08_test = (ROOT / "backend/tests/test_r94_0_6_m08_release_integration.py").read_text(encoding="utf-8")
    m08_manifest = json.loads((ROOT / "R94_0_6_M08_MANIFEST.json").read_text(encoding="utf-8"))

    require(config, 'app_version: str = "0.94.6"', "backend config")
    require(env, "APP_VERSION=0.94.6", "env example")
    require(compose, "APP_VERSION: 0.94.6", "docker compose")
    if package.get("version") != "0.94.6" or lock.get("version") != "0.94.6" or lock.get("packages", {}).get("", {}).get("version") != "0.94.6":
        raise SystemExit("FAIL: frontend version surfaces are not aligned to 0.94.6")

    # Integrated behavior contract from M01-M07.
    for token, source in (
        ("class ConfigurationFactAssessment", facts),
        ("def assess_configuration_documents", facts),
        ("def _structured_configuration_change_output", advanced),
        ("CHANGE_REVIEW_REQUIRED", advanced),
        ("ALREADY_PROTECTED", advanced),
        ("build_configuration_change_summary", advanced),
        ("assess_human_decision_consistency", advanced),
        ("configuration_comparison", ui),
        ("TECHNICAL ADVISORY CONTRADICTION", ui),
    ):
        if token not in source:
            raise SystemExit(f"FAIL: integrated M01-M07 behavior missing {token}")

    for index in range(1, 8):
        manifest_path = ROOT / f"R94_0_6_M{index:02d}_MANIFEST.json"
        module_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if module_manifest.get("status") != "APPROVED_BASELINE" or module_manifest.get("approval", {}).get("state") != "USER_APPROVED":
            raise SystemExit(f"FAIL: {manifest_path.name} not sealed approved")

    require(runbook, "R94.0.6 Structured configuration facts + cross-bank remediation addendum", "operator runbook")
    require(runbook, "2 implementations require change", "operator runbook")
    require(release_notes, "ALREADY PROTECTED", "R94.0.6 release notes")
    require(m08_notes, "M01 through M07 are user-approved", "M08 notes")
    require(m08_test, "test_r9406_release_version_surfaces_are_aligned", "M08 regression")
    if m08_manifest.get("release") != "R94.0.6-M08-REV1" or m08_manifest.get("application_version") != "0.94.6":
        raise SystemExit("FAIL: M08 manifest identity/version mismatch")
    if m08_manifest.get("status") != "CANDIDATE_AWAITING_APPROVAL" or m08_manifest.get("approval", {}).get("m08") != "AWAITING_USER_APPROVAL":
        raise SystemExit("FAIL: M08 manifest approval state mismatch")
    if m08_manifest.get("verification", {}).get("backend_total", {}).get("passed") != 173:
        raise SystemExit("FAIL: M08 manifest backend verification count mismatch")

    pdf = ROOT / "CREED_R94_0_6_Exact_Data_Entry_and_Live_Demo_Runbook.pdf"
    if not pdf.exists() or pdf.stat().st_size < 50_000:
        raise SystemExit("FAIL: R94.0.6 exact runbook PDF missing or unexpectedly small")

    for forbidden in (
        ROOT / "backend/.env",
        ROOT / "frontend/.env.local",
        ROOT / "backend/.data",
        ROOT / "frontend/tsconfig.tsbuildinfo",
    ):
        if forbidden.exists():
            raise SystemExit(f"FAIL: local/runtime artifact must not ship: {forbidden.relative_to(ROOT)}")

    print("R94.0.6-M08 release integration source verifier: PASS")


if __name__ == "__main__":
    main()
