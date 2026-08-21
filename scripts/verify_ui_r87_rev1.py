from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
page = (ROOT / "frontend/app/ownership/page.tsx").read_text(encoding="utf-8")
workspace = (ROOT / "frontend/components/ownership-registry-workspace.tsx").read_text(encoding="utf-8")
api = (ROOT / "frontend/lib/api.ts").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
models = (ROOT / "backend/app/domain/models.py").read_text(encoding="utf-8")
domain_api = (ROOT / "backend/app/api/domain.py").read_text(encoding="utf-8")
service = (ROOT / "backend/app/services/domain.py").read_text(encoding="utf-8")
repo = (ROOT / "backend/app/repositories/domain.py").read_text(encoding="utf-8")
migration = (ROOT / "backend/migrations/versions/f2a3b4c5d6e7_r87_ownership_responsibility_registry.py").read_text(encoding="utf-8")
design = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")

checks = {
    "ownership route exists": 'active="Ownership"' in page and "OwnershipRegistryWorkspace" in page,
    "sidebar navigation": '{ label: "Ownership", icon: UsersRound, href: "/ownership" }' in sidebar,
    "lucide-only ownership icons": 'from "lucide-react"' in workspace and 'UsersRound' in sidebar,
    "real ownership api client": 'getOwnershipAssignments' in api and '/api/v1/domain/ownership' in api,
    "create update remove api client": all(name in api for name in ['createOwnershipAssignment','updateOwnershipAssignment','removeOwnershipAssignment']),
    "backend responsibility model": 'class ResponsibilityAssignment' in models and '__tablename__ = "responsibility_assignments"' in models,
    "one current role per scope": 'uq_responsibility_scope_role' in models and 'uq_responsibility_scope_role' in migration,
    "authority linkage": 'ForeignKey("human_authorities.id", ondelete="RESTRICT")' in models,
    "scope controls": all(value in domain_api for value in ['PRODUCT_OWNER','MODULE_OWNER','TECHNICAL_OWNER','QA_OWNER','IMPLEMENTATION_LEAD']),
    "ownership endpoints": all(route in domain_api for route in ['@router.get("/ownership"','@router.post("/ownership"','@router.patch("/ownership/{assignment_id}"','@router.delete("/ownership/{assignment_id}"']),
    "inactive authority blocked": 'AUTHORITY_INACTIVE' in domain_api,
    "silent replacement blocked": 'RESPONSIBILITY_ALREADY_ASSIGNED' in service and 'RESPONSIBILITY_ALREADY_ASSIGNED' in domain_api,
    "audited lifecycle": all(action in service for action in ['RESPONSIBILITY_ASSIGNED','RESPONSIBILITY_REASSIGNED','RESPONSIBILITY_REMOVED']),
    "repository support": 'def list_responsibility_assignments' in repo and 'def get_responsibility_assignment' in repo,
    "migration chain": 'down_revision: Union[str, None] = "e1f2a3b4c5d6"' in migration,
    "r87 responsive css": '.ownership-registry-r87' in css and '@media (max-width:560px)' in css,
    "governance boundary copy": 'Responsibility is not permission.' in workspace,
    "design contract": 'UI-R87 — Ownership & Responsibility Registry' in design,
}
failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit("UI-R87 REV1 verifier failed: " + ", ".join(failed))
print("UI-R87 REV1 verifier PASS")
