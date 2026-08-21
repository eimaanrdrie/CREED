from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
page = (ROOT / "frontend/app/methods/page.tsx").read_text(encoding="utf-8")
workspace = (ROOT / "frontend/components/method-registry-workspace.tsx").read_text(encoding="utf-8")
api = (ROOT / "frontend/lib/api.ts").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
domain_api = (ROOT / "backend/app/api/domain.py").read_text(encoding="utf-8")
service = (ROOT / "backend/app/services/domain.py").read_text(encoding="utf-8")
repo = (ROOT / "backend/app/repositories/domain.py").read_text(encoding="utf-8")
design = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
tests = (ROOT / "backend/tests/test_domain_api.py").read_text(encoding="utf-8")

checks = {
    "methods loads authorities": "getHumanAuthorities" in page and "authorityResult" in page and "authorityError" in page,
    "baseline api client": "approveBaselineMethodVersion" in api and "/baseline-approval" in api and "X-CREED-Principal" in api,
    "baseline endpoint": '@router.post("/method-versions/{version_id}/baseline-approval"' in domain_api,
    "authority enforcement": 'capability="can_approve_learning"' in domain_api and "AuthorityEnforcementError" in domain_api,
    "draft-only guard": "METHOD_VERSION_NOT_DRAFT" in service,
    "one-time baseline guard": "METHOD_BASELINE_ALREADY_ESTABLISHED" in service and "list_method_versions_for_method" in repo,
    "baseline audit": 'action="BASELINE_METHOD_VERSION_APPROVED"' in service,
    "audit carries authority and reason": all(token in service for token in ["authority_id", "authority_display_name", "authority_role_title", '"reason": reason']),
    "inline approval trigger": "method-baseline-trigger-r91" in workspace and "Approve baseline" in workspace,
    "inline approval form": "method-baseline-approval-r91" in workspace and "Approval rationale" in workspace and "Approving authority" in workspace,
    "eligible authority filter": "item.active && item.can_approve_learning" in workspace,
    "no modal-first approval": 'role="dialog"' not in workspace,
    "no adoption side effect copy": "No implementation adoption or A-BOM dependency was created" in workspace,
    "learning boundary copy": "Later versions must use the governed learning workflow" in workspace,
    "responsive approval css": ".method-baseline-approval-r91" in css and ".method-baseline-trigger-r91" in css and "@media (max-width:560px)" in css,
    "backend tests": all(name in tests for name in [
        "test_baseline_method_version_approval_is_human_governed",
        "test_baseline_method_version_approval_fails_closed_without_permission",
        "test_baseline_method_version_approval_cannot_be_reused",
    ]),
    "design contract": "UI-R91 REV1 — Governed Baseline Method Approval" in design and "baseline shortcut cannot be reused" in design,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit("UI-R91 REV1 verifier failed: " + ", ".join(failed))
print("UI-R91 REV1 verifier PASS")
