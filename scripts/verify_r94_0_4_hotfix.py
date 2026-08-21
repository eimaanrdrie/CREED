from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "backend" / "app" / "core" / "ai_runtime.py"
CONFIG = ROOT / "backend" / "app" / "core" / "config.py"
ADVANCED = ROOT / "backend" / "app" / "services" / "advanced.py"
ENV = ROOT / "backend" / ".env.example"
COMPOSE = ROOT / "docker-compose.yml"
PACKAGE = ROOT / "frontend" / "package.json"
LOCK = ROOT / "frontend" / "package-lock.json"
TEST = ROOT / "backend" / "tests" / "test_r94_0_4_learning_json_recovery.py"
NOTES = ROOT / "R94_0_4_HOTFIX_NOTES.md"
RUNBOOK = ROOT / "R94_FINAL_RUNBOOK.md"


def require(text: str, needle: str, source: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: {source} missing {needle}")


def main() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_r94_0_3_hotfix.py")],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode:
        print(completed.stdout, end="")
        raise SystemExit("FAIL: R94.0.3 compatibility verifier")

    runtime = RUNTIME.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    advanced = ADVANCED.read_text(encoding="utf-8")
    env = ENV.read_text(encoding="utf-8")
    compose = COMPOSE.read_text(encoding="utf-8")
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    test = TEST.read_text(encoding="utf-8")
    notes = NOTES.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")

    runtime_version = next((v for v in ("0.94.6", "0.94.5", "0.94.4") if f'app_version: str = "{v}"' in config), None)
    if runtime_version is None:
        raise SystemExit("FAIL: config missing R94.0.4+ version")
    require(config, f'app_version: str = "{runtime_version}"', "config")
    require(config, "learning_context_window: int = 8192", "config")
    require(config, "learning_num_predict: int = 900", "config")
    require(config, "learning_excerpt_chars: int = 1400", "config")
    require(config, "learning_generation_attempts: int = 3", "config")
    require(env, f"APP_VERSION={runtime_version}", "env example")
    require(env, "LEARNING_CONTEXT_WINDOW=8192", "env example")
    require(env, "LEARNING_NUM_PREDICT=900", "env example")
    require(env, "LEARNING_EXCERPT_CHARS=1400", "env example")
    require(env, "LEARNING_GENERATION_ATTEMPTS=3", "env example")
    require(compose, f"APP_VERSION: {runtime_version}", "compose")
    require(compose, "LEARNING_CONTEXT_WINDOW: ${LEARNING_CONTEXT_WINDOW:-8192}", "compose")
    require(compose, "LEARNING_NUM_PREDICT: ${LEARNING_NUM_PREDICT:-900}", "compose")
    if package.get("version") != runtime_version or lock.get("version") != runtime_version or lock.get("packages", {}).get("", {}).get("version") != runtime_version:
        raise SystemExit(f"FAIL: frontend package versions not aligned to {runtime_version}")

    require(runtime, "OLLAMA_OUTPUT_TRUNCATED", "Ollama runtime")
    require(runtime, 'raw.get("done") is False', "Ollama runtime")
    require(advanced, "settings.learning_excerpt_chars", "Learning service")
    require(advanced, "settings.learning_context_window", "Learning service")
    require(advanced, "settings.learning_num_predict", "Learning service")
    require(advanced, "settings.learning_generation_attempts", "Learning service")
    require(advanced, "RETRY INSTRUCTION", "Learning service")
    require(advanced, "LEARNING_OUTPUT_TRUNCATED_AFTER_RETRY", "Learning service")
    require(advanced, "AI_LEARNING_VALIDATION_FAILED_AFTER_RETRY", "Learning service")

    require(test, "test_runtime_reports_explicit_ollama_length_stop", "R94.0.4 regression")
    require(test, "test_learning_retries_malformed_json_with_compact_budget_and_succeeds", "R94.0.4 regression")
    require(test, "test_learning_truncation_exhaustion_has_clear_error", "R94.0.4 regression")
    require(notes, "Malformed/truncated JSON retry", "R94.0.4 notes")
    require(runbook, "LEARNING_CONTEXT_WINDOW=8192", "operator runbook")
    require(runbook, "LEARNING_OUTPUT_TRUNCATED_AFTER_RETRY", "operator runbook")

    print("R94.0.4 hotfix source contract: PASS")


if __name__ == "__main__":
    main()
