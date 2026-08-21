from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "backend" / "app" / "services" / "demo.py"
ADVANCED_API = ROOT / "backend" / "app" / "api" / "advanced.py"
FRONT_API = ROOT / "frontend" / "lib" / "api.ts"
DEMO_PAGE = ROOT / "frontend" / "app" / "demo" / "page.tsx"
DEMO_WORKSPACE = ROOT / "frontend" / "components" / "demo-readiness-workspace.tsx"
ISSUE_FORM = ROOT / "frontend" / "components" / "issue-capsule-form.tsx"
ISSUE_PAGE = ROOT / "frontend" / "app" / "issues" / "new" / "page.tsx"
SIDEBAR = ROOT / "frontend" / "components" / "sidebar.tsx"
RECALL_FIXTURE = ROOT / "backend" / "demo_data" / "RECALL-PTP-V2-001.md"
TEST = ROOT / "backend" / "tests" / "test_r94_m11_end_to_end_demo_hardening.py"
NOTES = ROOT / "R94_M11_NOTES.md"


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: missing R94-M11 contract: {needle}")


def main() -> None:
    demo = DEMO.read_text(encoding="utf-8")
    advanced_api = ADVANCED_API.read_text(encoding="utf-8")
    front_api = FRONT_API.read_text(encoding="utf-8")
    demo_page = DEMO_PAGE.read_text(encoding="utf-8")
    workspace = DEMO_WORKSPACE.read_text(encoding="utf-8")
    issue_form = ISSUE_FORM.read_text(encoding="utf-8")
    issue_page = ISSUE_PAGE.read_text(encoding="utf-8")
    sidebar = SIDEBAR.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")
    notes = NOTES.read_text(encoding="utf-8")

    for needle in (
        'DEMO_VERSION = "CREED-DEMO-1.1"',
        '"BRD-COL-088.md"',
        'HumanAuthority(',
        'ImplementationDeployment(',
        'ResponsibilityAssignment(',
        'def demo_readiness(',
        '"clean_case"',
        '"qwen"',
        '"langgraph"',
        'RECALL-PTP-V2-001.md',
    ):
        require(demo, needle)

    require(advanced_api, "@router.get('/demo/readiness')")
    require(front_api, "export type DemoReadiness = {")
    require(front_api, "export const getDemoReadiness")
    require(front_api, "export const resetDemoBaseline")
    require(demo_page, "DemoReadinessWorkspace")

    for needle in (
        "READY TO START",
        "Reset synthetic baseline",
        "Start live issue",
        "Register any intended v2 adoption in Dependencies before demonstrating Recall",
    ):
        require(workspace, needle)

    require(issue_form, "Judging rehearsal values loaded")
    require(issue_page, 'ticket: "SUP-PTP-001"')
    require(issue_page, 'demoLoaded: true')
    if 'href: "/demo"' in sidebar or 'href="/demo"' in sidebar:
        raise SystemExit("FAIL: /demo must remain operator-only and absent from the sidebar")
    if not RECALL_FIXTURE.exists():
        raise SystemExit("FAIL: optional Recall evidence fixture missing")

    for needle in (
        "test_demo_reset_is_complete_repeatable_and_judge_ready",
        "test_readiness_fails_closed_if_live_issue_or_governance_baseline_is_dirty",
        "test_full_judge_path_issue_to_receipt_to_scope_aware_recall",
        '"CURRENT_REGISTERED_IMPLEMENTATIONS"',
        '"/api/v1/domain/dependencies"',
        '"/api/v1/method-versions/{v2_id}/revoke"',
    ):
        require(test, needle)

    require(notes, "R94-M11 REV1")
    print("R94-M11 source contract: PASS")


if __name__ == "__main__":
    main()
