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
TEST = ROOT / "backend" / "tests" / "test_r94_0_2_candidate_specific_evidence.py"
NOTES = ROOT / "R94_0_2_HOTFIX_NOTES.md"
RUNBOOK = ROOT / "R94_FINAL_RUNBOOK.md"


def require(text: str, needle: str, source: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: {source} missing {needle}")


def main() -> None:
    # Preserve all approved R94 contracts and R94.0.1 compatibility.
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_r94_0_1_hotfix.py")],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode:
        print(completed.stdout, end="")
        raise SystemExit("FAIL: R94.0.1 compatibility verifier")

    advanced = ADVANCED.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    env = ENV.read_text(encoding="utf-8")
    compose = COMPOSE.read_text(encoding="utf-8")
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    test = TEST.read_text(encoding="utf-8")
    notes = NOTES.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")

    require(advanced, "_candidate_catalog_fallback_document_ids", "advanced service")
    require(advanced, "explicit_doc_ids | fallback_doc_ids", "advanced service")
    require(advanced, "Candidate-specific evidence supplied to the Investigation Agent", "advanced service")
    require(advanced, "affected_inv_ids = {item.investigation_id for item in affected}", "learning readiness")
    require(advanced, "learning generation consumes evidence only from AFFECTED", "learning generation")

    runtime_version = next((v for v in ("0.94.6", "0.94.5", "0.94.4", "0.94.3", "0.94.2") if f'app_version: str = "{v}"' in config), "0.94.2")
    require(config, f'app_version: str = "{runtime_version}"', "config")
    require(config, "investigation_top_k: int = 3", "config")
    require(env, f"APP_VERSION={runtime_version}", "env example")
    require(env, "INVESTIGATION_TOP_K=3", "env example")
    require(compose, f"APP_VERSION: {runtime_version}", "compose")
    require(compose, "INVESTIGATION_TOP_K: 3", "compose")
    if package.get("version") != runtime_version or lock.get("version") != runtime_version or lock.get("packages", {}).get("", {}).get("version") != runtime_version:
        raise SystemExit(f"FAIL: frontend package versions not aligned to {runtime_version}")

    require(test, "test_legacy_missing_edge_evidence_is_bound_per_candidate", "R94.0.2 regression")
    require(test, "test_not_affected_evidence_cannot_unlock_learning", "R94.0.2 regression")
    require(notes, "Candidate-specific evidence propagation", "R94.0.2 notes")
    require(runbook, "1/0/0 evidence pattern", "operator runbook")

    print("R94.0.2 hotfix source contract: PASS")


if __name__ == "__main__":
    main()
