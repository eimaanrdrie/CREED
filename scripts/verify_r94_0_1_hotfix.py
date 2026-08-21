from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADVANCED = ROOT / "backend" / "app" / "services" / "advanced.py"
CONFIG = ROOT / "backend" / "app" / "core" / "config.py"
ENV = ROOT / "backend" / ".env.example"
COMPOSE = ROOT / "docker-compose.yml"
PACKAGE = ROOT / "frontend" / "package.json"
LOCK = ROOT / "frontend" / "package-lock.json"
TEST = ROOT / "backend" / "tests" / "test_r94_0_1_hotfix_investigation_evidence.py"
NOTES = ROOT / "R94_0_1_HOTFIX_NOTES.md"


def require(text: str, needle: str, source: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: {source} missing {needle}")


def main() -> None:
    # M01-M11 semantic contracts remain unchanged. M12's verifier is also run
    # after being made version-compatible with the 0.94.1 post-final hotfix.
    for index in range(1, 13):
        verifier = ROOT / "scripts" / f"verify_r94_m{index:02d}.py"
        completed = subprocess.run([sys.executable, str(verifier)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if completed.returncode:
            print(completed.stdout, end="")
            raise SystemExit(f"FAIL: {verifier.name}")

    advanced = ADVANCED.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    env = ENV.read_text(encoding="utf-8")
    compose = COMPOSE.read_text(encoding="utf-8")
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    test = TEST.read_text(encoding="utf-8")
    notes = NOTES.read_text(encoding="utf-8")

    require(advanced, "explicit_doc_ids = _implementation_supporting_document_ids(", "advanced service")
    require(advanced, "method_version_id=assessment.method_version_id", "advanced service")
    runtime_version = next((v for v in ("0.94.6", "0.94.5", "0.94.4", "0.94.3", "0.94.2", "0.94.1") if f'app_version: str = "{v}"' in config), None)
    if not runtime_version:
        raise SystemExit("FAIL: unsupported R94.0.1-compatible runtime version")
    require(config, f'app_version: str = "{runtime_version}"', "config")
    require(config, "investigation_top_k: int = 3", "config")
    require(env, f"APP_VERSION={runtime_version}", "env example")
    require(env, "INVESTIGATION_TOP_K=3", "env example")
    require(compose, f"APP_VERSION: {runtime_version}", "compose")
    require(compose, "INVESTIGATION_TOP_K: 3", "compose")
    if package.get("version") != runtime_version or lock.get("version") != runtime_version or lock.get("packages", {}).get("", {}).get("version") != runtime_version:
        raise SystemExit(f"FAIL: frontend package versions not aligned to {runtime_version}")
    require(test, "test_ui_dependency_supporting_evidence_reaches_investigation_and_learning", "hotfix regression")
    require(test, 'assert readiness["reason"] == "READY"', "hotfix regression")
    require(notes, "Existing completed runs", "hotfix notes")
    print("R94.0.1 hotfix source contract: PASS")


if __name__ == "__main__":
    main()
