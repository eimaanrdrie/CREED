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
TEST = ROOT / "backend" / "tests" / "test_r94_0_3_learning_ollama_boundary.py"
NOTES = ROOT / "R94_0_3_HOTFIX_NOTES.md"
RUNBOOK = ROOT / "R94_FINAL_RUNBOOK.md"


def require(text: str, needle: str, source: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: {source} missing {needle}")


def main() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_r94_0_2_hotfix.py")],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode:
        print(completed.stdout, end="")
        raise SystemExit("FAIL: R94.0.2 compatibility verifier")

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

    runtime_version = next((v for v in ("0.94.6", "0.94.5", "0.94.4", "0.94.3") if f'app_version: str = "{v}"' in config), None)
    if runtime_version is None:
        raise SystemExit("FAIL: config missing R94.0.3+ version")
    require(config, 'ollama_learning_model: str | None = "qwen3.5:4b"', "config")
    require(env, f"APP_VERSION={runtime_version}", "env example")
    require(env, "OLLAMA_LEARNING_MODEL=qwen3.5:4b", "env example")
    require(compose, f"APP_VERSION: {runtime_version}", "compose")
    require(compose, "OLLAMA_LEARNING_MODEL: ${OLLAMA_LEARNING_MODEL:-qwen3.5:4b}", "compose")
    if package.get("version") != runtime_version or lock.get("version") != runtime_version or lock.get("packages", {}).get("", {}).get("version") != runtime_version:
        raise SystemExit(f"FAIL: frontend package versions not aligned to {runtime_version}")

    require(runtime, "OLLAMA_HTTP_{response.status_code}", "Ollama runtime")
    require(runtime, "def require_model_available", "Ollama runtime")
    require(advanced, "def _learning_format_schema", "Learning service")
    require(advanced, "learning_model=settings.ollama_learning_model or settings.live_runtime_model", "Learning service")
    require(advanced, "runtime.require_model_available(learning_model)", "Learning service")
    require(advanced, "format_schema=format_schema", "Learning service")

    require(test, "test_learning_defaults_to_dedicated_4b_model_and_simple_schema", "R94.0.3 regression")
    require(test, "test_learning_model_preflight_fails_with_clear_model_name", "R94.0.3 regression")
    require(test, "test_ollama_400_preserves_real_response_body_and_execution_log", "R94.0.3 regression")
    require(notes, "Dedicated Learning model", "R94.0.3 notes")
    require(runbook, "OLLAMA_LEARNING_MODEL=qwen3.5:4b", "operator runbook")
    require(runbook, "OLLAMA_HTTP_400", "operator runbook")

    print("R94.0.3 hotfix source contract: PASS")


if __name__ == "__main__":
    main()
