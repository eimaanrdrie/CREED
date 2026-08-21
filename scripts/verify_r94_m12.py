from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
FINAL_BUILD = ROOT / "FINAL_BUILD_NOTES.md"
RUNBOOK = ROOT / "R94_FINAL_RUNBOOK.md"
NOTES = ROOT / "R94_M12_NOTES.md"
FINAL_NOTES = ROOT / "R94_FINAL_RELEASE_NOTES.md"
CONFIG = ROOT / "backend" / "app" / "core" / "config.py"
ENV_EXAMPLE = ROOT / "backend" / ".env.example"
COMPOSE = ROOT / "docker-compose.yml"
PACKAGE = ROOT / "frontend" / "package.json"
DEMO = ROOT / "backend" / "app" / "services" / "demo.py"
SIDEBAR = ROOT / "frontend" / "components" / "sidebar.tsx"
M11_TEST = ROOT / "backend" / "tests" / "test_r94_m11_end_to_end_demo_hardening.py"
M12_TEST = ROOT / "backend" / "tests" / "test_r94_m12_release_integration.py"
MANIFEST = ROOT / "R94_FINAL_MANIFEST.json"
DOCKERFILE = ROOT / "backend" / "Dockerfile"
PACKAGE_LOCK = ROOT / "frontend" / "package-lock.json"


def require(text: str, needle: str, *, source: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: {source} missing R94-M12 contract: {needle}")


def forbid(text: str, needle: str, *, source: str) -> None:
    if needle in text:
        raise SystemExit(f"FAIL: {source} contains stale R94-M12 content: {needle}")


def run_prior_verifiers() -> None:
    for index in range(1, 12):
        verifier = ROOT / "scripts" / f"verify_r94_m{index:02d}.py"
        if not verifier.exists():
            raise SystemExit(f"FAIL: missing prior verifier {verifier.name}")
        completed = subprocess.run(
            [sys.executable, str(verifier)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if completed.returncode != 0:
            print(completed.stdout, end="")
            raise SystemExit(f"FAIL: {verifier.name}")


def main() -> None:
    run_prior_verifiers()

    readme = README.read_text(encoding="utf-8")
    final_build = FINAL_BUILD.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    notes = NOTES.read_text(encoding="utf-8")
    final_notes = FINAL_NOTES.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    env_example = ENV_EXAMPLE.read_text(encoding="utf-8")
    compose = COMPOSE.read_text(encoding="utf-8")
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    demo = DEMO.read_text(encoding="utf-8")
    sidebar = SIDEBAR.read_text(encoding="utf-8")
    m11_test = M11_TEST.read_text(encoding="utf-8")
    m12_test = M12_TEST.read_text(encoding="utf-8")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    package_lock = json.loads(PACKAGE_LOCK.read_text(encoding="utf-8"))

    # Post-final R94.0.x hotfixes preserve M12's integration contract as long as
    # all runtime/package version surfaces agree.
    runtime_version = next((v for v in ("0.94.6", "0.94.5", "0.94.4", "0.94.3", "0.94.2", "0.94.1", "0.94.0") if f'app_version: str = "{v}"' in config), "0.94.0")
    require(config, f'app_version: str = "{runtime_version}"', source="backend config")
    require(env_example, f"APP_VERSION={runtime_version}", source="backend env example")
    require(compose, f"APP_VERSION: {runtime_version}", source="docker compose")
    if package.get("version") != runtime_version:
        raise SystemExit("FAIL: frontend package version is not aligned to backend runtime version")
    if package_lock.get("version") != runtime_version or package_lock.get("packages", {}).get("", {}).get("version") != runtime_version:
        raise SystemExit("FAIL: frontend package-lock version is not aligned to runtime version")
    require(dockerfile, "COPY demo_data ./demo_data", source="backend Dockerfile")

    for text, source in ((readme, "README"), (final_build, "FINAL_BUILD_NOTES"), (runbook, "R94_FINAL_RUNBOOK")):
        require(text, "10 indexed", source=source)
        require(text, "/demo", source=source)

    forbid(readme, "9 project artefacts", source="README")
    forbid(final_build, "no frontend Demo route", source="FINAL_BUILD_NOTES")

    require(readme, "operator-only", source="README")
    require(runbook, "Approval is not deployment", source="R94_FINAL_RUNBOOK")
    require(runbook, "RECALL-PTP-V2-001.md", source="R94_FINAL_RUNBOOK")
    require(notes, "R94-M12 REV1", source="R94_M12_NOTES")
    require(notes, "feature freeze", source="R94_M12_NOTES")
    require(final_notes, "APPROVED FINAL", source="R94_FINAL_RELEASE_NOTES")
    require(final_notes, "M01", source="R94_FINAL_RELEASE_NOTES")
    require(final_notes, "M12", source="R94_FINAL_RELEASE_NOTES")

    require(demo, 'DEMO_VERSION = "CREED-DEMO-1.1"', source="demo service")
    if 'href: "/demo"' in sidebar or 'href="/demo"' in sidebar:
        raise SystemExit("FAIL: /demo must remain operator-only and absent from the sidebar")

    for needle in (
        "test_demo_reset_is_complete_repeatable_and_judge_ready",
        "test_full_judge_path_issue_to_receipt_to_scope_aware_recall",
        '"CURRENT_REGISTERED_IMPLEMENTATIONS"',
        '"/api/v1/domain/dependencies"',
    ):
        require(m11_test, needle, source="M11 end-to-end regression")


    if manifest.get("release") != "R94" or manifest.get("module") != "M12-REV1-FINAL":
        raise SystemExit("FAIL: final manifest identity mismatch")
    if manifest.get("status") != "APPROVED_FINAL" or manifest.get("baseline") != "CREED-R94-M12-REV1_APPROVED":
        raise SystemExit("FAIL: final manifest approval state mismatch")
    if manifest.get("application_version") != "0.94.0":
        raise SystemExit("FAIL: final manifest version mismatch")
    verification = manifest.get("verification", {})
    if verification.get("backend_tests", {}).get("passed") != 126:
        raise SystemExit("FAIL: manifest backend verification count mismatch")
    if verification.get("r94_targeted_tests", {}).get("passed") != 40:
        raise SystemExit("FAIL: manifest R94 targeted verification count mismatch")
    if verification.get("source_verifiers", {}).get("passed") != 12:
        raise SystemExit("FAIL: manifest source verifier count mismatch")

    for needle in (
        "test_final_release_packages_every_demo_reset_and_recall_asset",
        "test_backend_docker_image_copies_demo_assets_required_by_operator_route",
    ):
        require(m12_test, needle, source="M12 release regression")

    forbidden_paths = [
        ROOT / "backend" / ".env",
        ROOT / "frontend" / ".env.local",
        ROOT / "backend" / ".data",
        ROOT / "frontend" / "tsconfig.tsbuildinfo",
    ]
    for path in forbidden_paths:
        if path.exists():
            raise SystemExit(f"FAIL: local/runtime artifact must not ship in final release: {path.relative_to(ROOT)}")

    print("R94 FINAL integration contract: PASS")


if __name__ == "__main__":
    main()
