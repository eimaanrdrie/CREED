from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "app" / "services" / "analysis_runs.py"
FRONTEND = ROOT / "frontend" / "components" / "analysis-shell.tsx"
TEST = ROOT / "backend" / "tests" / "test_r94_m02_zero_candidate_human_review_guard.py"


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: missing R94-M02 contract: {needle}")


def main() -> None:
    backend = BACKEND.read_text(encoding="utf-8")
    frontend = FRONTEND.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    for needle in (
        'if not investigations:',
        '"review_boundary": "SKIPPED_NO_CASES"',
        '"skip_reason": "NO_INVESTIGATION_CASES"',
        '"_step_skipped": True',
        'action="HUMAN_REVIEW_SKIPPED_NO_CASES"',
        'issue.status = IssueStatus.OPEN.value',
        '"ANALYSIS_RUN_NO_REVIEW_CASES"',
    ):
        require(backend, needle)

    for needle in (
        'No human-review cases available',
        'No governed decision was opened for this run.',
        'NO CASES',
        'No human-review cases produced · check routing or evidence if unexpected',
    ):
        require(frontend, needle)

    for needle in (
        'test_zero_investigations_skip_human_review_without_waiting',
        'test_zero_case_run_completes_without_waiting_and_keeps_issue_open',
        'assert step is not None and step.status == "SKIPPED"',
        'assert issue is not None and issue.status == "OPEN"',
    ):
        require(test, needle)

    print("R94-M02 source contract: PASS")


if __name__ == "__main__":
    main()
