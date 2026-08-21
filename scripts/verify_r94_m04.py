from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "backend" / "app" / "api" / "analysis_runs.py"
RUNS = ROOT / "backend" / "app" / "services" / "analysis_runs.py"
FRONTEND_API = ROOT / "frontend" / "lib" / "api.ts"
SHELL = ROOT / "frontend" / "components" / "analysis-shell.tsx"
TEST = ROOT / "backend" / "tests" / "test_r94_m04_stuck_run_recovery.py"


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: missing R94-M04 contract: {needle}")


def main() -> None:
    api = API.read_text(encoding="utf-8")
    runs = RUNS.read_text(encoding="utf-8")
    frontend_api = FRONTEND_API.read_text(encoding="utf-8")
    shell = SHELL.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    for needle in (
        "def analysis_run_recovery_status",
        '"STALE_ZERO_CASE_HUMAN_REVIEW"',
        '"HUMAN_REVIEW_CASES_EXIST"',
        "def supersede_stuck_analysis_run",
        'action="ANALYSIS_RUN_RECOVERY_SUPERSEDED"',
        'run.status = AgentStatus.CANCELLED.value',
        '"preserved_checkpoint": True',
    ):
        require(runs, needle)

    for needle in (
        '"/issues/{issue_id}/analysis-runs/recover"',
        "AnalysisRecoveryRequest",
        'action="ANALYSIS_RUN_RECOVERY_STARTED"',
        "analysis_run_recovery_status",
    ):
        require(api, needle)

    for needle in (
        "recovery_eligible?: boolean",
        "recoverStuckAnalysisRun",
        "/analysis-runs/recover",
    ):
        require(frontend_api, needle)

    for needle in (
        "Recover & rerun",
        "run?.recovery_eligible",
        "recoverStuckAnalysisRun",
        "stale zero-case Human Review checkpoint",
    ):
        require(shell, needle)

    for needle in (
        "test_recovery_supersedes_zero_case_waiting_run_and_starts_fresh_run",
        "test_recovery_refuses_to_bypass_real_human_review_cases",
        "test_normal_start_still_reuses_waiting_run_until_explicit_recovery",
        'assert old is not None and old.status == "CANCELLED"',
    ):
        require(test, needle)

    print("R94-M04 source contract: PASS")


if __name__ == "__main__":
    main()
