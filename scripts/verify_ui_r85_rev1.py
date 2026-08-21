from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
advanced = (ROOT / "backend/app/api/advanced.py").read_text(encoding="utf-8")
enforcement = (ROOT / "backend/app/services/authority_enforcement.py").read_text(encoding="utf-8")
analysis = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
recalls = (ROOT / "frontend/components/recalls-workspace.tsx").read_text(encoding="utf-8")
authority = (ROOT / "frontend/components/human-authority-workspace.tsx").read_text(encoding="utf-8")
api = (ROOT / "frontend/lib/api.ts").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
design = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
test = (ROOT / "backend/tests/test_authority_enforcement.py").read_text(encoding="utf-8")

checks = {
    "central enforcement service": "def require_human_authority" in enforcement and "AuthorityEnforcementError" in enforcement,
    "fail closed principal": all(code in enforcement for code in ["AUTHORITY_PRINCIPAL_REQUIRED", "AUTHORITY_PRINCIPAL_NOT_REGISTERED", "AUTHORITY_PRINCIPAL_INACTIVE", "AUTHORITY_PRINCIPAL_MISMATCH"]),
    "capability enforcement": all(code in enforcement for code in ["HUMAN_DECISION_AUTHORITY_REQUIRED", "LEARNING_APPROVAL_AUTHORITY_REQUIRED", "RECALL_AUTHORITY_REQUIRED"]),
    "governed endpoints require header": advanced.count('alias="X-CREED-Principal"') >= 3,
    "human decision enforced": '"can_submit_human_decision"' in advanced and "authority.principal" in advanced and "authority_id" in advanced,
    "learning decision enforced": '"can_approve_learning"' in advanced and "approve_learning(" in advanced,
    "recall enforced": '"can_authorize_recall"' in advanced and "revoke_method(" in advanced,
    "frontend sends principal header": api.count('"X-CREED-Principal"') >= 3,
    "human review uses eligible principals": "can_submit_human_decision" in analysis and "Select Human Decision authority" in analysis,
    "learning approval uses eligible principals": "can_approve_learning" in analysis and "Approve learning" in analysis and "decideLearningProposal" in analysis,
    "recall free text removed": "can_authorize_recall" in recalls and "Select recall authority" in recalls and '<input value={reviewer}' not in recalls,
    "no authentication fabrication": "not an authenticated login" in authority and "authorization enforcement, not authentication" in design,
    "blocked state links to registry": 'href="/authority"' in analysis and 'href="/authority"' in recalls,
    "operate scoped styling": ".authority-enforcement-r85" in css and ".learning-authority-r85" in css and ".recall-authority-empty-r85" in css,
    "responsive hardening": "@media (max-width: 760px)" in css and "@media (max-width: 560px)" in css,
    "backend regression coverage": "test_governed_endpoints_reject_missing_or_wrong_authority_before_business_action" in test and "test_authorized_principal_reaches_governed_business_validation" in test,
}

failures = [name for name, passed in checks.items() if not passed]
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}  {name}")
if failures:
    raise SystemExit("UI-R85 REV1 verification failed: " + ", ".join(failures))
print("UI-R85 REV1 verifier PASS")
