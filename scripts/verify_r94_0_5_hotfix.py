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
TEST = ROOT / "backend" / "tests" / "test_r94_0_5_variable_aware_configuration_impact.py"
NOTES = ROOT / "R94_0_5_HOTFIX_NOTES.md"
RUNBOOK = ROOT / "R94_FINAL_RUNBOOK.md"
README = ROOT / "README.md"


def require(text: str, needle: str, source: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: {source} missing {needle}")


def main() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_r94_0_4_hotfix.py")],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode:
        print(completed.stdout, end="")
        raise SystemExit("FAIL: R94.0.4 compatibility verifier")

    advanced = ADVANCED.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    env = ENV.read_text(encoding="utf-8")
    compose = COMPOSE.read_text(encoding="utf-8")
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    test = TEST.read_text(encoding="utf-8")
    notes = NOTES.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")

    runtime_version = next((v for v in ("0.94.6", "0.94.5") if f'app_version: str = "{v}"' in config), None)
    if runtime_version is None:
        raise SystemExit("FAIL: config runtime version is not compatible with R94.0.5+")
    require(config, f'app_version: str = "{runtime_version}"', "config")
    require(config, "investigation_authoritative_config_chars: int = 2400", "config")
    require(env, f"APP_VERSION={runtime_version}", "env example")
    require(env, "INVESTIGATION_AUTHORITATIVE_CONFIG_CHARS=2400", "env example")
    require(compose, f"APP_VERSION: {runtime_version}", "compose")
    require(compose, "INVESTIGATION_AUTHORITATIVE_CONFIG_CHARS: 2400", "compose")
    if package.get("version") != runtime_version or lock.get("version") != runtime_version or lock.get("packages", {}).get("", {}).get("version") != runtime_version:
        raise SystemExit("FAIL: frontend package versions not aligned to compatible R94.0.5+ runtime")

    require(advanced, "class ConfigurationChangeRequest", "advanced service")
    require(advanced, "def _extract_configuration_change_request", "advanced service")
    require(advanced, "def _configuration_values_from_document", "advanced service")
    require(advanced, "def _configuration_change_investigation_output", "advanced service")
    require(advanced, "full persisted document text", "advanced service")
    require(advanced, "config_out = _configuration_change_investigation_output", "advanced service")
    require(advanced, 'finding_type="POTENTIALLY_AFFECTED"', "advanced service")
    require(advanced, 'finding_type="NO_SUPPORTING_EVIDENCE_OF_IMPACT"', "advanced service")

    require(test, "test_variable_change_uses_full_authoritative_config_and_never_false_insufficient", "R94.0.5 regression")
    require(test, "test_configuration_change_parser_supports_generic_scalar_key", "R94.0.5 regression")
    require(test, "test_conflicting_authoritative_values_remain_fail_closed", "R94.0.5 regression")
    require(notes, "Glass-box configuration comparator", "R94.0.5 notes")
    require(notes, "is not globally disabled", "R94.0.5 notes")
    require(runbook, "R94.0.5 Variable-aware configuration impact addendum", "operator runbook")
    require(readme, "R94.0.5 HOTFIX REV1", "README")

    print("R94.0.5 hotfix source contract: PASS")


if __name__ == "__main__":
    main()
