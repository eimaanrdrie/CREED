from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADVANCED = ROOT / "backend" / "app" / "services" / "advanced.py"
API = ROOT / "backend" / "app" / "api" / "advanced.py"
FRONT_API = ROOT / "frontend" / "lib" / "api.ts"
SHELL = ROOT / "frontend" / "components" / "analysis-shell.tsx"
CSS = ROOT / "frontend" / "app" / "globals.css"
TEST = ROOT / "backend" / "tests" / "test_r94_m06_learning_correction_ui.py"


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: missing R94-M06 contract: {needle}")


def main() -> None:
    advanced = ADVANCED.read_text(encoding="utf-8")
    api = API.read_text(encoding="utf-8")
    front_api = FRONT_API.read_text(encoding="utf-8")
    shell = SHELL.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    for needle in (
        "def learning_readiness",
        '"FINAL_AFFECTED_DECISION_REQUIRED"',
        '"APPROVED_SOURCE_METHOD_REQUIRED"',
        '"LEARNING_SUPPORTING_EVIDENCE_REQUIRED"',
        '"LEARNING_VERSION_ALREADY_EXISTS"',
        "def _suggest_learning_version",
        'if run.status != "COMPLETED": raise ValueError("HUMAN_REVIEW_MUST_COMPLETE")',
    ):
        require(advanced, needle)

    for needle in (
        "learning-readiness",
        'x_creed_principal: str | None = Header(default=None, alias="X-CREED-Principal")',
        '_authority_or_403(db, x_creed_principal, "can_submit_human_decision", payload.author)',
    ):
        require(api, needle)

    for needle in (
        "export type LearningReadiness",
        "getLearningReadiness",
        "createLearningProposal",
        '"X-CREED-Principal":principal',
    ):
        require(front_api, needle)

    for needle in (
        "HUMAN CORRECTION",
        "Generate learning proposal",
        "Qwen structuring",
        "correctionAuthorities",
        "readiness.affected_decision_count",
        "readiness.supporting_evidence_count",
        "The correction is human-authored. Qwen structures the proposal",
    ):
        require(shell, needle)

    require(css, "R94-M06 — Human Correction -> Learning Proposal UI")
    require(test, "test_learning_readiness_requires_affected_decision_and_suggests_next_version")
    require(test, "test_learning_proposal_create_requires_registered_human_decision_authority")
    print("R94-M06 source contract: PASS")


if __name__ == "__main__":
    main()
